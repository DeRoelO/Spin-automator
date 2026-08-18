import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "edit_concept_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   EDIT & PERSIST EXISTING CONCEPT WORKFLOW TEST                   ===")
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

        # Find row containing ON-Z-952159 or last row in grid
        log("3. Eerste rij in het dashboard grid selecteren en 'Bewerken' knop of dblclick proberen...")
        rows = page.query_selector_all(".x-grid3-row")
        target_row = None
        for r in rows:
            if "952159" in r.inner_text() or "952163" in r.inner_text():
                target_row = r
                break

        if not target_row and len(rows) > 0:
            target_row = rows[0]

        if target_row:
            log(f"   Doelrij geselecteerd: {target_row.inner_text().strip().replace('\n', ' | ')[:100]}")
            target_row.click()
            page.wait_for_timeout(1000)

            # Click Bewerken toolbar button or double click
            bewerken_btn = page.locator(".x-btn", has_text="Bewerken").first
            if bewerken_btn.is_visible():
                log("4. Klikken op 'Bewerken' knop in de toolbar...")
                bewerken_btn.click()
            else:
                log("4. Dubbelklikken op de geselecteerde rij...")
                target_row.dblclick()

            page.wait_for_timeout(6000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "01_editor_open.png"))

            wins = page.query_selector_all(".x-window")
            log(f"5. Aantal geopende vensters: {len(wins)}")

            for w in wins:
                if w.is_visible():
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                    log(f"   [✓✓✓] BEWERK VENSTER GEOPEND: '{title}'")

                    # Change date to 01.12.2026
                    log("6. Start/Eind datum wijzigen naar '01.12.2026'...")
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
                        setVal('start', '01.12.2026, 09:00');
                        setVal('end', '01.12.2026, 15:00');
                    }""")
                    page.wait_for_timeout(1000)

                    # Click Bewaren
                    w_btns = w.query_selector_all("button, .x-btn-text")
                    for b in w_btns:
                        if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                            log("7. Klikken op 'Bewaren' inside editor...")
                            b.click(force=True)
                            page.wait_for_timeout(8000)
                            page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_bewaren.png"))
                            break

            # Reload dashboard and check grid row update
            log("8. Dashboard verversen om opgeslagen wijziging te verifiëren...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(5000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "03_final_grid.png"))

            check_rows = page.query_selector_all(".x-grid3-row")
            for r_idx, r in enumerate(check_rows[:8]):
                txt = r.inner_text().strip().replace("\n", " | ")
                log(f"   Rij {r_idx}: {txt[:140]}")
                if "01.12.2026" in txt:
                    log(f"   [🎉🎉🎉] EXTREME SUCCESS! OPGESLAGEN CONCEPT BEVESTIGD IN DE DASHBOARD TABEL: Rij {r_idx}: {txt}")

        browser.close()

if __name__ == "__main__":
    run()
