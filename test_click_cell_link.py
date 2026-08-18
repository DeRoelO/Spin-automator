import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "cell_link_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   CLICKING GRID CELL ANCHOR LINK WORKFLOW TEST                   ===")
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

        # Find cell link or anchor in grid
        log("3. Zoeken naar klikbaar element in de tabel-rijen...")
        cell = page.locator(".x-grid3-cell-inner").first
        if cell.is_visible():
            log(f"   Cell content: '{cell.inner_text().strip()}'")
            cell.click()
            page.wait_for_timeout(1000)

            # Try pressing Enter or clicking toolbar button
            log("4. Pijl omlaag & Enter indrukken...")
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)

            wins = page.query_selector_all(".x-window")
            log(f"5. Aantal geopende vensters: {len(wins)}")

            for w in wins:
                if w.is_visible():
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                    log(f"   [✓✓✓] SUCCESS! VENSTER GEOPEND: '{title}'")

                    # Change date to 05.12.2026
                    log("6. Datum wijzigen naar '05.12.2026'...")
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
                        setVal('start', '05.12.2026, 09:00');
                        setVal('end', '05.12.2026, 15:00');
                    }""")
                    page.wait_for_timeout(1000)

                    # Click Bewaren
                    w_btns = w.query_selector_all("button, .x-btn-text")
                    for b in w_btns:
                        if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                            log("7. Klikken op 'Bewaren'...")
                            b.click(force=True)
                            page.wait_for_timeout(8000)
                            page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_bewaren.png"))
                            break

            # Reload dashboard
            log("8. Dashboard verversen...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(5000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "02_final_grid.png"))

            check_rows = page.query_selector_all(".x-grid3-row")
            for r_idx, r in enumerate(check_rows[:8]):
                txt = r.inner_text().strip().replace("\n", " | ")
                log(f"   Rij {r_idx}: {txt[:140]}")
                if "05.12.2026" in txt:
                    log(f"   [🎉🎉🎉] OPGESLAGEN CONCEPT BEVESTIGD IN HET OVERZICHT: Rij {r_idx}: {txt}")

        browser.close()

if __name__ == "__main__":
    run()
