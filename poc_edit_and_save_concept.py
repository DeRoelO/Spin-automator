import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "poc_results")

def log(msg):
    print(msg, flush=True)

def run_poc():
    log("================================================================")
    log("===   SPIN PROOF OF CONCEPT: MAATREGEL OPENEN & CONCEPT SPINS  ===")
    log("================================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("1. Inloggen op SPIN...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Login dialog
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

        # Select first measure row in table
        log("3. Eerste maatregel selecteren in de tabel...")
        first_row = page.locator(".x-grid3-row").first
        if first_row.is_visible():
            # Right click to open context menu
            first_row.click(button="right")
            page.wait_for_timeout(1500)

            # Click 'Bewerken'
            log("4. Klikken op 'Bewerken' in het snelmenu...")
            bewerken = page.locator(".x-menu-list-item", has_text="Bewerken").first
            bewerken.click()
            page.wait_for_timeout(6000)

            page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_editor_success.png"))

            log("5. Controleren of Maatregel Venster geopend is...")
            wins = page.query_selector_all(".x-window")
            active_win = None
            for w in wins:
                if w.is_visible():
                    active_win = w
                    break

            if active_win:
                title = active_win.query_selector(".x-window-header-text").inner_text().strip()
                log(f"   [✓] Venster geopend: '{title}'")
                
                # Check for buttons inside win
                win_btns = active_win.query_selector_all("button, .x-btn-text")
                btn_names = [b.inner_text().strip() for b in win_btns if b.is_visible() and b.inner_text().strip()]
                log(f"   [✓] Actie-knoppen in venster: {btn_names}")

                # Check form inputs inside win
                inputs = active_win.query_selector_all("input, textarea, select")
                log(f"   [✓] Aantal invoervelden in venster: {len(inputs)}")

                # Inspect all labels & prefilled values in the editor!
                editor_data = []
                for inp in inputs:
                    try:
                        iname = inp.get_attribute("name") or ""
                        ival = inp.get_attribute("value") or ""
                        lbl = ""
                        try:
                            parent = inp.evaluate_handle("el => el.closest('.x-form-item')")
                            if parent:
                                lbl = parent.inner_text().strip().replace("\n", " ")
                        except:
                            pass

                        if iname or lbl:
                            editor_data.append({"name": iname, "value": ival, "label": lbl})
                    except:
                        pass

                with open(os.path.join(OUTPUT_DIR, "prefilled_editor_data.json"), "w", encoding="utf-8") as f:
                    json.dump(editor_data, f, indent=2, ensure_ascii=False)

                log(f"   [✓] {len(editor_data)} vooringevulde velden opgeslagen in prefilled_editor_data.json!")
                log("================================================================")
                log("===  PROMPT PROOF OF CONCEPT SUCCESVOL! BEWERKEN GEOPEND!  ===")
                log("================================================================")

            else:
                log("Geen actief venster gevonden na 'Bewerken' klik.")
        else:
            log("Geen rijen in de tabel gevonden.")

        browser.close()

if __name__ == "__main__":
    run_poc()
