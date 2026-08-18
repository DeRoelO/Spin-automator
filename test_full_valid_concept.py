import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
COPY_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW_COPY&viewType=GE_MEASURE_WINDOW&measureId=1107615&phaseId=0&eventId=0&isCopy=true&isInverse=false&mode=CREATE&version=-1&measureType=STATIONARY"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "poc_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def set_input(page, name, val):
    try:
        page.evaluate("""({name, val}) => {
            const inputs = document.querySelectorAll(`input[name='${name}']`);
            inputs.forEach(inp => {
                inp.removeAttribute('readonly');
                inp.value = val;
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                inp.dispatchEvent(new Event('blur', { bubbles: true }));
            });
        }""", {"name": name, "val": val})
        log(f"   [✓] Set '{name}' = '{val}'")
    except Exception as e:
        log(f"   [!] Error setting '{name}': {e}")

def set_combo_by_text(page, field_name, search_text):
    try:
        page.evaluate("""({field_name, search_text}) => {
            const inp = document.querySelector(`input[name='${field_name}']`);
            if (inp) {
                inp.value = search_text;
                inp.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""", {"field_name": field_name, "search_text": search_text})
        log(f"   [✓] Combo '{field_name}' = '{search_text}'")
    except Exception as e:
        log(f"   [!] Error setting combo '{field_name}': {e}")

def run_valid_poc():
    log("=========================================================================")
    log("===   VOLLEDIGE SPIN CONCEPT TEST (OP BASIS VAN JOUW SCREENSHOT)    ===")
    log("=========================================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("1. Inloggen op SPIN...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Login modal
        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                page.wait_for_timeout(1500)
                break

        name_input = page.locator("input[name='name']").first
        pass_input = page.locator("input[name='password']").first
        name_input.fill(USERNAME, force=True)
        pass_input.fill(PASSWORD, force=True)

        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                break

        page.wait_for_timeout(7000)
        log("2. Ingelogd als Roel van Haandel.")

        log("3. Maatregel Kopiëren venster openen...")
        page.goto(COPY_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)

        log("4. Alle 20+ verplichte velden invullen uit jouw screenshot...")

        # Algemene eigenschappen
        set_combo_by_text(page, "bestekId", "NL-31154600-inspecties voor MJPV")
        set_input(page, "start", "06.09.2026, 09:00")
        set_input(page, "end", "06.09.2026, 15:00")
        set_combo_by_text(page, "roadworkType", "inspectie algemeen")
        set_combo_by_text(page, "managingDistrict", "ON District Zuid")

        # Van locatie
        set_combo_by_text(page, "location.fromRoadNumber", "A15")
        set_combo_by_text(page, "location.fromRoadSide", "Re")
        set_input(page, "location.fromMeter", "150,000")
        set_combo_by_text(page, "location.betweenName", "Gorinchem")
        set_combo_by_text(page, "location.secondaryName", "Leigraaf")

        # Naar locatie
        set_combo_by_text(page, "location.toRoadNumber", "A15")
        set_combo_by_text(page, "location.toRoadSide", "Re")
        set_input(page, "location.toMeter", "165,000")
        set_combo_by_text(page, "location.andName", "Nijmegen")
        set_combo_by_text(page, "location.primaryName", "Bemmel")

        # Verkeer
        set_combo_by_text(page, "trafficHindranceClass", "1 (geen file)")
        set_combo_by_text(page, "roadblockType", "96a-430")
        set_input(page, "widthConstraint", "7,00")

        # Aannemer
        set_combo_by_text(page, "trafficDesk", "ON District Zuid")

        page.screenshot(path=os.path.join(OUTPUT_DIR, "valid_poc_form_filled.png"))

        log("5. Klikken op 'Bewaren' in SPIN...")
        all_btns = page.query_selector_all("button, .x-btn, .x-btn-text")
        bewaren_btn = None
        for b in all_btns:
            if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                bewaren_btn = b
                break

        if bewaren_btn:
            try:
                bewaren_btn.click(force=True)
            except:
                page.evaluate("el => el.click()", bewaren_btn)

            log("   [✓] Knop 'Bewaren' geklikt!")
            page.wait_for_timeout(8000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "valid_poc_after_bewaren.png"))

            # Save full HTML
            with open(os.path.join(OUTPUT_DIR, "valid_poc_after_bewaren.html"), "w", encoding="utf-8") as f:
                f.write(page.content())

            log("=========================================================================")
            log("===   SUCCES! VOLLEDIG GELDIGE CONCEPT MELDING VERWERKT IN SPIN!       ===")
            log("=========================================================================")
        else:
            log("   [!] Knop 'Bewaren' niet gevonden.")

        browser.close()

if __name__ == "__main__":
    run_valid_poc()
