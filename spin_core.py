import time
import math
import re
import traceback
from playwright.sync_api import sync_playwright

BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"

def write_debug_log(msg):
    with open("spin_debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def calculate_measure_segments(from_km_float, to_km_float):
    segments = []
    curr_start = from_km_float
    
    while True:
        remaining = round(to_km_float - curr_start, 3)
        # Als het overgebleven stuk kleiner of gelijk aan 20km is -> laatste stuk
        if remaining <= 20.0:
            segments.append((curr_start, to_km_float))
            break
        # Als het overgebleven stuk tússen de 20 en 25km zit (oftewel: rest is < 5km) -> plak eraan vast
        elif remaining < 25.0:
            segments.append((curr_start, to_km_float))
            break
        # Anders maken we een strak blok van 20.0 km
        else:
            curr_end = round(curr_start + 20.0, 3)
            segments.append((curr_start, curr_end))
            curr_start = curr_end
            
    return segments

def format_km(val_float):
    return f"{val_float:.3f}".replace(".", ",")

def safe_wait(popup, ms):
    if popup and not popup.is_closed():
        try:
            popup.wait_for_timeout(ms)
            return
        except:
            pass
    time.sleep(ms / 1000.0)

def confirm_and_validate_gxt_field(popup, field_name, value):
    try:
        if popup.is_closed(): return
        el = popup.locator(f"input[name='{field_name}'], textarea[name='{field_name}']").first
        if el.is_visible():
            el.click()
            el.fill(value)
            popup.evaluate("""(name) => {
                const inp = document.querySelector(`input[name='${name}']`);
                if (inp) {
                    ['input', 'change', 'blur', 'keyup'].forEach(evt => inp.dispatchEvent(new Event(evt, { bubbles: true })));
                }
            }""", field_name)
            el.press("Enter")
            el.press("Tab")
            popup.evaluate("""() => {
                const legend = document.querySelector('fieldset legend, .x-fieldset-header, div.x-form-item-label');
                if (legend) legend.click();
            }""")
            safe_wait(popup, 800)
    except Exception:
        pass

def select_gxt_dropdown_option(popup, field_name, target_text=""):
    try:
        if popup.is_closed(): return False
        input_el = popup.locator(f"input[name='{field_name}']").first
        if not input_el.is_visible(): return False

        parent_wrap = popup.locator(f"input[name='{field_name}']").locator("xpath=ancestor::div[contains(@class, 'x-form-field-wrap')]").first
        trigger = parent_wrap.locator("img.x-form-trigger").first
        if trigger.is_visible():
            trigger.click()
        else:
            input_el.click()

        safe_wait(popup, 400)
        items = popup.query_selector_all(".x-combo-list-item")
        visible_items = [it for it in items if it.is_visible()]

        matched = False
        if target_text and visible_items:
            for it in visible_items:
                txt = it.inner_text().strip()
                if target_text.lower() in txt.lower():
                    it.click()
                    matched = True
                    break
        if not matched and visible_items:
            target_item = visible_items[1] if len(visible_items) > 1 else visible_items[0]
            target_item.click()
            matched = True

        safe_wait(popup, 500)
        return matched
    except Exception:
        return False

def check_and_correct_location_after_full_fill(popup, log_queue):
    if popup.is_closed(): return

    safe_wait(popup, 800)

    # Van km check
    from_meter_el = popup.locator("input[name='location.fromMeter']").first
    if from_meter_el.is_visible():
        from_meter_el.hover()
        safe_wait(popup, 1000)
        tooltip_text_from = popup.evaluate("""(name) => {
            const inp = document.querySelector(`input[name='${name}']`);
            let txt = inp ? (inp.getAttribute('ext:qtip') || inp.getAttribute('qtip') || inp.title || '') : '';
            txt = txt.replace(/<[^>]*>?/gm, '');
            if (!txt) {
                const tips = Array.from(document.querySelectorAll('.x-tip, .x-tip-bd, .x-form-invalid-msg, [role="alert"]'));
                for (const t of tips) {
                    const tTxt = t.innerText ? t.innerText.trim() : '';
                    if (tTxt.includes('tenminste') || tTxt.includes('maximaal') || tTxt.includes('hoogstens')) {
                        txt = tTxt; break;
                    }
                }
            }
            return txt;
        }""", "location.fromMeter")

        if tooltip_text_from:
            min_match = re.search(r"tenminste\s+([\d,]+)", tooltip_text_from)
            max_match = re.search(r"(?:maximaal|hoogstens)\s+([\d,]+)", tooltip_text_from)
            corrected_val_from = min_match.group(1) if min_match else (max_match.group(1) if max_match else None)
            if corrected_val_from:
                confirm_and_validate_gxt_field(popup, "location.fromMeter", corrected_val_from)
                log_queue.append(f"⚠️ 'Van km' gecorrigeerd naar toegestane grens: {corrected_val_from}")

    # Tot km check
    to_meter_el = popup.locator("input[name='location.toMeter']").first
    if to_meter_el.is_visible():
        to_meter_el.hover()
        safe_wait(popup, 1000)
        tooltip_text_to = popup.evaluate("""(name) => {
            const inp = document.querySelector(`input[name='${name}']`);
            let txt = inp ? (inp.getAttribute('ext:qtip') || inp.getAttribute('qtip') || inp.title || '') : '';
            txt = txt.replace(/<[^>]*>?/gm, '');
            if (!txt) {
                const tips = Array.from(document.querySelectorAll('.x-tip, .x-tip-bd, .x-form-invalid-msg, [role="alert"]'));
                for (const t of tips) {
                    const tTxt = t.innerText ? t.innerText.trim() : '';
                    if (tTxt.includes('tenminste') || tTxt.includes('maximaal') || tTxt.includes('hoogstens')) {
                        txt = tTxt; break;
                    }
                }
            }
            return txt;
        }""", "location.toMeter")

        if tooltip_text_to:
            min_match = re.search(r"tenminste\s+([\d,]+)", tooltip_text_to)
            max_match = re.search(r"(?:maximaal|hoogstens)\s+([\d,]+)", tooltip_text_to)
            corrected_val_to = max_match.group(1) if max_match else (min_match.group(1) if min_match else None)
            if corrected_val_to:
                confirm_and_validate_gxt_field(popup, "location.toMeter", corrected_val_to)
                log_queue.append(f"⚠️ 'Tot km' gecorrigeerd naar toegestane grens: {corrected_val_to}")

def add_contactpersoon_uitvoering(popup, search_term):
    try:
        if popup.is_closed(): return
        pencil_btn = popup.locator("#x-auto-523 button, div#x-auto-522 button").first
        if not pencil_btn.is_visible():
            pencil_btn = popup.locator("button:has(img[src*='cache.png'])").last

        pencil_btn.click()
        safe_wait(popup, 1000)

        nieuw_btn = popup.locator(".x-window button:has-text('Nieuw')").first
        if nieuw_btn.is_visible():
            nieuw_btn.click()
            safe_wait(popup, 800)

        achternaam_input = popup.locator(".x-window input[name='name'], .x-window input[name='lastName'], .x-window input[type='text']").first
        if achternaam_input.is_visible():
            achternaam_input.click()
            achternaam_input.fill("")
            achternaam_input.type(search_term, delay=50)
            safe_wait(popup, 800)

            first_word = search_term.split(' ')[0].lower()
            matched_item = popup.evaluate("""(word) => {
                const items = Array.from(document.querySelectorAll('.x-combo-list-item, .x-grid3-row, .x-combo-list-item'));
                const match = items.find(it => it.innerText && it.innerText.toLowerCase().includes(word));
                if (match) {
                    ['mousedown', 'mouseup', 'click'].forEach(evt => {
                        match.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    });
                    return match.innerText.trim();
                }
                return null;
            }""", first_word)

            if not matched_item:
                achternaam_input.press("Enter")

            safe_wait(popup, 1500)

        toepassen_btn = popup.locator(".x-window button:has-text('Toepassen')").first
        if toepassen_btn.is_visible():
            toepassen_btn.click()
            safe_wait(popup, 800)

        popup.evaluate("""() => {
            const modal = document.querySelector('.x-window');
            if (modal) {
                const btns = Array.from(modal.querySelectorAll('button'));
                const sluitenBtn = btns.find(b => b.innerText && b.innerText.trim().toLowerCase() === 'sluiten');
                if (sluitenBtn) {
                    ['mousedown', 'mouseup', 'click'].forEach(evt => {
                        sluitenBtn.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    });
                }
            }
        }""")
        safe_wait(popup, 800)
    except Exception:
        pass

def add_opmerking(popup, text):
    try:
        if popup.is_closed(): return
        toevoegen_btns = popup.query_selector_all("button")
        target_toevoegen = None
        for b in toevoegen_btns:
            if b.is_visible() and b.inner_text().strip().lower() == "toevoegen":
                target_toevoegen = b
                break

        if target_toevoegen:
            target_toevoegen.click()
            safe_wait(popup, 1000)

            comment_area = popup.locator(".x-window textarea, textarea[name='content'], textarea[name='comment']").first
            if comment_area.is_visible():
                comment_area.click()
                comment_area.fill(text)
                safe_wait(popup, 500)

            ok_btn = popup.locator(".x-window button:has-text('Ok'), button:has-text('OK')").first
            if ok_btn.is_visible():
                ok_btn.click()
                safe_wait(popup, 800)
    except Exception:
        pass

def click_bewaren_or_report_error(popup, task_info, log_queue):
    safe_wait(popup, 1500)
    if popup.is_closed(): return False

    status = popup.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button, .x-btn-text'));
        const match = btns.find(b => b.innerText && b.innerText.trim().toLowerCase() === 'bewaren');
        if (!match) return { found: false, enabled: false, errors: 'Knop Bewaren niet gevonden' };
        
        const btnEl = match.closest('table.x-btn') || match;
        const isDisabled = btnEl.classList.contains('x-item-disabled') || btnEl.classList.contains('x-btn-disabled') || match.disabled;
        
        let errors = [];
        if (isDisabled) {
            const invalidEls = Array.from(document.querySelectorAll('.x-form-invalid'));
            invalidEls.forEach(el => {
                let name = el.getAttribute('name') || el.id;
                if (name) errors.push(name);
            });
        }
        return { found: true, enabled: !isDisabled, errors: errors.join(', ') || 'Onbekend veld' };
    }""")

    if status.get("enabled"):
        popup.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button, .x-btn-text'));
            const match = btns.find(b => b.innerText && b.innerText.trim().toLowerCase() === 'bewaren');
            if (match) {
                ['mousedown', 'mouseup', 'click'].forEach(evt => {
                    match.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                });
            }
        }""")
        log_queue.append(f"✅ Formulier bewaard voor {task_info['Wegnummer']} {task_info['Van km']} - {task_info['Tot km']}")
        return True
    else:
        errors = status.get("errors", "Onbekend")
        log_queue.append(f"❌ MISLUKT: Spinmelding vak {task_info['Wegnummer']} {task_info['Van km']} - {task_info['Tot km']} {task_info['Wegzijde']} mislukt, fout op veld: {errors}")
        return False

def handle_post_save_dialogs(popup, log_queue):
    for step in range(4):
        if popup.is_closed(): break
        safe_wait(popup, 1000)
        result = popup.evaluate("""() => {
            const dialogs = Array.from(document.querySelectorAll('.x-window, .x-message-box, .x-window-dlg'));
            let handled = false;
            let msgText = '';
            for (const dlg of dialogs) {
                if (!dlg || dlg.style.display === 'none' || dlg.style.visibility === 'hidden') continue;
                const btns = Array.from(dlg.querySelectorAll('button, .x-btn-text, .x-btn'));
                const okBtn = btns.find(b => {
                    const t = b.innerText ? b.innerText.trim().toLowerCase() : '';
                    return t === 'ok' || t === 'ja' || t === 'akkoord';
                });
                if (okBtn) {
                    const textEl = dlg.querySelector('.ext-mb-text, .x-window-body');
                    if (textEl) msgText = textEl.innerText.trim();
                    const parentTable = okBtn.closest('table.x-btn') || okBtn;
                    [okBtn, parentTable].forEach(el => {
                        if (el) {
                            el.focus();
                            ['mouseover', 'mousedown', 'mouseup', 'click'].forEach(evt => {
                                el.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                            });
                        }
                    });
                    handled = true;
                    break;
                }
            }
            return { handled: handled, text: msgText };
        }""")
        if result and result.get("handled"):
            warn_text = result.get("text", "Onbekende waarschuwing")
            
            # Opschonen van enters, gaten en de tekst van de 'Ok' knop
            warn_text = re.sub(r'\s+', ' ', warn_text).strip()
            if warn_text.lower().endswith(" ok"):
                warn_text = warn_text[:-3].strip()
                
            log_queue.append(f"ℹ️ Waarschuwing gesloten: '{warn_text}'")
            safe_wait(popup, 1200)

def try_click_sluiten_until_closed(popup, max_attempts=15):
    for attempt in range(1, max_attempts + 1):
        if popup.is_closed(): return True
        try:
            closed = popup.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, .x-btn-text'));
                const sluitenBtn = btns.find(b => b.innerText && b.innerText.trim().toLowerCase() === 'sluiten');
                if (sluitenBtn && !sluitenBtn.disabled && !sluitenBtn.classList.contains('x-btn-disabled')) {
                    ['mousedown', 'mouseup', 'click'].forEach(evt => {
                        sluitenBtn.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    });
                    return true;
                }
                return false;
            }""")
            if closed:
                time.sleep(1.5)
                if popup.is_closed(): return True
            else:
                time.sleep(1.5)
        except Exception:
            if popup.is_closed(): return True
    return False

def run_spin_automation(tasks, config):
    """
    Generator function that yields log messages.
    """
    yield "🚀 SPIN Automator gestart..."
    write_debug_log("\n=== NIEUWE AUTOMATISERING RUN ===")
    
    with sync_playwright() as p:
        yield "🌐 Chrome Browser opstarten (Headless = {})...".format(config['headless'])
        browser = p.chromium.launch(
            headless=config['headless'],
            args=["--disable-popup-blocking", "--start-maximized"]
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        yield "🔑 Inloggen op SPIN..."
        try:
            page.goto(BASE_URL, wait_until="networkidle")
            time.sleep(2.0)

            buttons = page.query_selector_all("button")
            for btn in buttons:
                if btn.is_visible() and btn.inner_text().strip() == "Ok":
                    btn.click()
                    time.sleep(1.0)
                    break

            name_input = page.locator("input[name='name']").first
            pass_input = page.locator("input[name='password']").first
            name_input.fill(config['username'], force=True)
            pass_input.fill(config['password'], force=True)

            buttons = page.query_selector_all("button")
            for btn in buttons:
                if btn.is_visible() and btn.inner_text().strip() == "Ok":
                    btn.click()
                    break
            
            time.sleep(5.0)
            yield "✅ Succesvol ingelogd op SPIN Dashboard."
        except Exception as e:
            err_str = traceback.format_exc()
            write_debug_log(f"FOUT BIJ INLOGGEN:\n{err_str}")
            yield f"❌ Fout tijdens inloggen: {e}"
            browser.close()
            return

        for idx, task in enumerate(tasks, 1):
            log_queue = []
            yield f"\n🔄 Start aanvraag {idx}/{len(tasks)}: {task['Datum']} | {task['Wegnummer']} {task['Van km']} - {task['Tot km']} ({task['Wegzijde']})"
            
            try:
                # Open form
                page.locator("div.x-menubar-item", has_text="Bestand").first.click()
                time.sleep(0.4)
                page.keyboard.press("ArrowDown")
                time.sleep(0.3)
                page.keyboard.press("ArrowRight")
                time.sleep(0.3)
                page.keyboard.press("ArrowDown")
                time.sleep(0.3)
                page.keyboard.press("ArrowDown")
                time.sleep(0.3)

                popup_page = None
                try:
                    with context.expect_page(timeout=8000) as popup_info:
                        page.keyboard.press("Enter")
                    popup_page = popup_info.value
                except Exception:
                    page.keyboard.press("Enter")
                    time.sleep(3.0)
                    if len(context.pages) > 1:
                        popup_page = context.pages[-1]

                if not popup_page or popup_page.is_closed():
                    yield f"❌ Kon formuliervenster niet openen voor taak {idx}!"
                    continue

                popup_page.bring_to_front()
                time.sleep(2.0)

                # Fill Data
                safe_wait(popup_page, 1500)
                select_gxt_dropdown_option(popup_page, "bestekId", config['besteknummer'])
                confirm_and_validate_gxt_field(popup_page, "start", task['Start'])
                confirm_and_validate_gxt_field(popup_page, "end", task['End'])
                select_gxt_dropdown_option(popup_page, "roadworkType", "inspectie algemeen")
                
                select_gxt_dropdown_option(popup_page, "managingDistrict", config['district'])

                select_gxt_dropdown_option(popup_page, "location.fromRoadNumber", task['Wegnummer'])
                select_gxt_dropdown_option(popup_page, "location.fromRoadSide", task['Wegzijde'])
                confirm_and_validate_gxt_field(popup_page, "location.fromMeter", task['Van km'])

                select_gxt_dropdown_option(popup_page, "location.toRoadNumber", task['Wegnummer'])
                select_gxt_dropdown_option(popup_page, "location.toRoadSide", task['Wegzijde'])
                confirm_and_validate_gxt_field(popup_page, "location.toMeter", task['Tot km'])

                check_and_correct_location_after_full_fill(popup_page, log_queue)

                select_gxt_dropdown_option(popup_page, "trafficHindranceClass", "1 (geen file)")
                select_gxt_dropdown_option(popup_page, "outsideWorkableHours", "Nee")

                try:
                    popup_page.locator("input[name='gxt.RadioGroup.3'][value='true']").first.click(force=True)
                    popup_page.locator("input[name='gxt.RadioGroup.4'][value='false']").first.click(force=True)
                    popup_page.locator("input[name='gxt.RadioGroup.5'][value='false']").first.click(force=True)
                except: pass

                confirm_and_validate_gxt_field(popup_page, "widthConstraint", "7,00")
                select_gxt_dropdown_option(popup_page, "roadblockType", "96a-430")

                try:
                    popup_page.locator("input[name='gxt.RadioGroup.8'][value='false']").first.click(force=True)
                    popup_page.locator("input[name='gxt.RadioGroup.9'][value='true']").first.click(force=True)
                except: pass

                select_gxt_dropdown_option(popup_page, "trafficDesk", config['district'])
                select_gxt_dropdown_option(popup_page, "contractor", "DHV Royal Haskoning")
                
                select_gxt_dropdown_option(popup_page, "submitters.id", config['naam_dropdown'])
                add_contactpersoon_uitvoering(popup_page, config['naam_potlood'])
                add_opmerking(popup_page, config['opmerking'])

                for l_msg in log_queue:
                    yield l_msg
                log_queue.clear()

                is_saved = click_bewaren_or_report_error(popup_page, task, log_queue)
                for l_msg in log_queue:
                    yield l_msg
                log_queue.clear()

                if is_saved:
                    handle_post_save_dialogs(popup_page, log_queue)
                    for l_msg in log_queue:
                        yield l_msg

                try_click_sluiten_until_closed(popup_page, max_attempts=15)
                yield f"☑️ Venster voor {task['Wegnummer']} gesloten."
                time.sleep(1.0)
            
            except Exception as e:
                err_str = traceback.format_exc()
                write_debug_log(f"FOUT BIJ TAAK {idx}:\n{err_str}")
                yield f"❌ Onverwachte fout bij taak {idx}: {e} (Zie spin_debug.log)"

        browser.close()
        yield f"\n🎉 Klaar! {len(tasks)} spinmeldingen in concept aangemaakt. Controleer spin op aantal meldingen en dien in."
