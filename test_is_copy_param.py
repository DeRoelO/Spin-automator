import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
COPY_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW_NEW&viewType=GE_MEASURE_WINDOW&measureId=1107615&phaseId=0&eventId=0&isCopy=true&isInverse=false&mode=EDIT&version=-1&measureType=STATIONARY"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "is_copy_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   TESTING NATIVE SPIN ISCOPY=TRUE CREATION WORKFLOW               ===")
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
        log("2. Ingelogd op SPIN Dashboard.")

        # Navigate to COPY_URL
        log("3. Navigeren naar COPY_URL met isCopy=true...")
        page.goto(COPY_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_copy_url_loaded.png"))

        wins = page.query_selector_all(".x-window")
        log(f"4. Aantal geopende vensters: {len(wins)}")

        for idx, w in enumerate(wins):
            if w.is_visible():
                title = w.query_selector(".x-window-header-text").inner_text().strip()
                log(f"   [✓] VENSTER GEOPEND! Titel: '{title}'")

                # Change dates to 20.12.2026
                log("5. Datum aanpassen naar '20.12.2026'...")
                page.evaluate("""() => {
                    const setVal = (name, val) => {
                        const el = document.querySelector(`.x-window input[name='${name}']`);
                        if (el) {
                            el.removeAttribute('readonly');
                            el.value = val;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            el.dispatchEvent(new Event('blur', { bubbles: true }));
                        }
                    };
                    setVal('start', '20.12.2026, 09:00');
                    setVal('end', '20.12.2026, 15:00');
                }""")
                page.wait_for_timeout(1000)

                # Click Bewaren
                all_btns = w.query_selector_all("button, .x-btn-text")
                for b in all_btns:
                    if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                        log("6. Klikken op 'Bewaren'...")
                        b.click(force=True)
                        page.wait_for_timeout(8000)
                        page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_bewaren.png"))

                        # Check if any error modal popped up
                        err_modals = page.query_selector_all(".x-window-plain, .x-window-dlg")
                        for em in err_modals:
                            if em.is_visible():
                                log(f"   [!] Popup modal gedetecteerd: '{em.inner_text().strip()[:100]}'")
                        break

        # Refresh dashboard and check if saved
        log("7. Dashboard verversen, filter wissen en grid controleren...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(5000)

        wissen_btn = page.locator(".x-btn", has_text="Wissen").first
        if wissen_btn.is_visible():
            wissen_btn.click()
            page.wait_for_timeout(1000)

        toepassen_btn = page.locator(".x-btn", has_text="Toepassen").first
        if toepassen_btn.is_visible():
            toepassen_btn.click()
            page.wait_for_timeout(5000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "03_final_grid.png"))

        rows = page.query_selector_all(".x-grid3-row")
        log(f"   Totaal rijen in het overzicht: {len(rows)}")
        for r_idx, r in enumerate(rows[:10]):
            txt = r.inner_text().strip().replace("\n", " | ")
            if "20.12.2026" in txt:
                log(f"   [🎉🎉🎉] CONCEPT SUCCESVOL GEAUTOMATISEERD & AANGEWEZEN OP SPIN GRID! Rij {r_idx}: {txt}")

        browser.close()

if __name__ == "__main__":
    run()
