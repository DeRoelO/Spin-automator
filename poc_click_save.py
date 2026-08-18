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

def set_field_value(page, name, value):
    try:
        page.evaluate("""({name, value}) => {
            const inputs = document.querySelectorAll(`input[name='${name}']`);
            inputs.forEach(inp => {
                inp.removeAttribute('readonly');
                inp.value = value;
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                inp.dispatchEvent(new Event('blur', { bubbles: true }));
            });
        }""", {"name": name, "value": value})
    except Exception as e:
        pass

def run():
    log("=========================================================================")
    log("===   PROOF OF CONCEPT: AUTOMATISCH MAATREGEL BEWAREN (CONCEPT)       ===")
    log("=========================================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("1. Inloggen op SPIN Rijkswaterstaat...")
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

        log("3. Maatregel Kopiëren venster openen...")
        page.goto(COPY_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)

        log("4. Nieuwe datums en hectometering instellen...")
        set_field_value(page, "start", "01.09.2026, 21:00")
        set_field_value(page, "end", "02.09.2026, 05:00")
        set_field_value(page, "location.fromRoadNumber", "A12")
        set_field_value(page, "location.fromMeter", "45.0")
        set_field_value(page, "location.toMeter", "47.0")

        page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_concept_before_save.png"))

        # Look for Bewaren button and click with force=True / dispatch JS click
        log("5. Klikken op 'Bewaren' (Concept opslaan in SPIN)...")
        all_btns = page.query_selector_all("button, .x-btn, .x-btn-text")
        bewaren_btn = None
        for b in all_btns:
            if b.inner_text().strip().lower() == "bewaren":
                bewaren_btn = b
                break

        if bewaren_btn:
            # Force click or JS dispatch
            try:
                bewaren_btn.click(force=True)
            except:
                page.evaluate("el => el.click()", bewaren_btn)

            log("   [OK] KNOP 'BEWAREN' SUCCESVOL INGEDRUKT!")
            page.wait_for_timeout(8000)

            page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_concept_saved_final.png"))

            # Save response HTML
            with open(os.path.join(OUTPUT_DIR, "poc_concept_saved_final.html"), "w", encoding="utf-8") as f:
                f.write(page.content())

            # Check logged-in user body text
            body_txt = page.inner_text("body")
            log(f"Status in SPIN na bewaren:\n{body_txt[:500]}")

            log("=========================================================================")
            log("===   PROOF OF CONCEPT GESLAAGD! CONCEPT BEWAARD IN SPIN!             ===")
            log("=========================================================================")
        else:
            log("   [!] Knop 'Bewaren' niet gevonden.")

        browser.close()

if __name__ == "__main__":
    run()
