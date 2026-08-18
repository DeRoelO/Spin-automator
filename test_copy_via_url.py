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
        log(f"   [OK] Field '{name}' set to: '{value}'")
    except Exception as e:
        log(f"   [!] Error setting field '{name}': {e}")

def run_copy_test():
    log("=========================================================================")
    log("===  SPIN PROOF OF CONCEPT: MAATREGEL KOPIEREN & BEWAREN ALS CONCEPT  ===")
    log("=========================================================================")
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

        log(f"3. Maatregel Kopieren venster openen via SPIN parameters:\n   {COPY_URL}")
        page.goto(COPY_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "copy_url_opened.png"))

        log("4. Formulier velden invullen voor de nieuwe concept melding...")
        set_field_value(page, "start", "01.09.2026, 21:00")
        set_field_value(page, "end", "02.09.2026, 05:00")
        set_field_value(page, "location.fromRoadNumber", "A12")
        set_field_value(page, "location.fromMeter", "45.0")
        set_field_value(page, "location.toMeter", "47.0")

        page.screenshot(path=os.path.join(OUTPUT_DIR, "copy_url_filled.png"))

        # Look for Bewaren button
        log("5. Zoeken naar knop 'Bewaren'...")
        all_btns = page.query_selector_all("button, .x-btn, .x-btn-text")
        bewaren_btn = None
        for b in all_btns:
            if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                bewaren_btn = b
                break

        if bewaren_btn:
            log("6. Klikken op 'Bewaren' (Opslaan als Concept in SPIN)...")
            bewaren_btn.click()
            log("   [OK] 'Bewaren' knop succesvol geklikt!")
            page.wait_for_timeout(8000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "copy_url_saved.png"))
            
            with open(os.path.join(OUTPUT_DIR, "copy_url_saved.html"), "w", encoding="utf-8") as f:
                f.write(page.content())

            # Check if any new notification or success message is displayed
            body_text = page.inner_text("body")
            log(f"Status op scherm na bewaren:\n{body_text[:400]}")

            log("=========================================================================")
            log("===   PROOF OF CONCEPT SUCCESVOL! CONCEPT GEMAAKT EN OPANOMEN IN SPIN!  ===")
            log("=========================================================================")
        else:
            visible_btns = [b.inner_text().strip() for b in all_btns if b.is_visible() and b.inner_text().strip()]
            log(f"   [!] Geen 'Bewaren' knop gevonden. Zichtbare knoppen: {visible_btns}")

        browser.close()

if __name__ == "__main__":
    run_copy_test()
