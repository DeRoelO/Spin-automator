import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "persistence_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run_test():
    log("=========================================================================")
    log("===   PERSISTENCE TEST: COPY EXISTING MEASURE & VERIFY IN GRID        ===")
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

        # Select first row in grid
        first_row = page.locator(".x-grid3-row").first
        if first_row.is_visible():
            log("3. Eerste maatregel in de tabel selecteren...")
            first_row.click()
            page.wait_for_timeout(1000)

            # Right click -> Kopiëren
            log("4. Rechtsklikken -> Kopiëren...")
            first_row.click(button="right")
            page.wait_for_timeout(1500)
            page.locator(".x-menu-list-item", has_text="Kopiëren").first.click()
            page.wait_for_timeout(2000)

            # Right click -> Plakken
            log("5. Rechtsklikken -> Plakken...")
            first_row.click(button="right")
            page.wait_for_timeout(1500)
            page.locator(".x-menu-list-item", has_text="Plakken").first.click()
            page.wait_for_timeout(6000)

            # Check if editor window opened
            wins = page.query_selector_all(".x-window")
            log(f"   Vensters geopend na Plakken: {len(wins)}")

            # Update dates to 15.11.2026
            log("6. Unieke testdatum instellen (15.11.2026)...")
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
                setVal('start', '15.11.2026, 09:00');
                setVal('end', '15.11.2026, 15:00');
            }""")
            page.wait_for_timeout(1000)

            # Click Bewaren
            log("7. Klikken op 'Bewaren'...")
            all_btns = page.query_selector_all("button, .x-btn-text")
            bewaren_btn = None
            for b in all_btns:
                if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                    bewaren_btn = b
                    break

            if bewaren_btn:
                bewaren_btn.click(force=True)
                log("   Knop 'Bewaren' ingedrukt!")
                page.wait_for_timeout(8000)
                page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_bewaren.png"))

            # Now clear filters and check grid table!
            log("8. Dashboard verversen, filter wissen en zoeken naar '15.11.2026'...")
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

            page.screenshot(path=os.path.join(OUTPUT_DIR, "02_grid_unfiltered.png"))

            # Search table rows for '15.11.2026'
            rows = page.query_selector_all(".x-grid3-row")
            log(f"   Totaal rijen in het overzicht: {len(rows)}")

            found = False
            for r_idx, r in enumerate(rows):
                txt = r.inner_text().strip().replace("\n", " | ")
                if "15.11.2026" in txt or "15.11.2026" in txt:
                    log(f"   [🎉] GEPASTE CONCEPT VERIFIËERD OP DE GRID: Rij {r_idx}: {txt}")
                    found = True
                    break

            if not found:
                log("   [!] Concept 15.11.2026 nog niet direct zichtbaar in de eerste 500 rijen.")
                for r_idx, r in enumerate(rows[:5]):
                    log(f"   Eerste rijen grid: {r.inner_text().strip().replace('\n', ' | ')[:120]}")

        browser.close()

if __name__ == "__main__":
    run_test()
