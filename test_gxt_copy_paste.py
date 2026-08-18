import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_copy_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run_gxt_copy():
    log("=========================================================================")
    log("===   EXACT GXT KOPIËREN EN PLAKKEN WORKFLOW TEST (SPIN NATIVE GXT)   ===")
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
            first_row.click()
            page.wait_for_timeout(1000)
            log("3. Eerste maatregel geselecteerd in tabel.")

            # Right click -> Kopiëren
            first_row.click(button="right")
            page.wait_for_timeout(1500)
            page.locator(".x-menu-list-item", has_text="Kopiëren").first.click()
            page.wait_for_timeout(2000)
            log("4. 'Kopiëren' geklikt in snelmenu!")

            # Right click -> Plakken
            first_row.click(button="right")
            page.wait_for_timeout(1500)
            page.locator(".x-menu-list-item", has_text="Plakken").first.click()
            page.wait_for_timeout(6000)
            log("5. 'Plakken' geklikt in snelmenu!")

            page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_paste_window.png"))

            # Check open window header and inputs
            wins = page.query_selector_all(".x-window")
            editor_win = None
            for w in wins:
                if w.is_visible():
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                    log(f"   Geopend venster titel: '{title}'")
                    if "maatregel" in title.lower():
                        editor_win = w
                        break

            if editor_win:
                # Update start date and end date
                log("6. Nieuwe start- en einddatum instellen...")
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
                    setVal('start', '15.10.2026, 08:00');
                    setVal('end', '15.10.2026, 16:00');
                }""")
                page.wait_for_timeout(1000)

                # Click Bewaren inside editor window
                log("7. Klikken op 'Bewaren' (Concept Opslaan)...")
                win_btns = editor_win.query_selector_all("button, .x-btn-text")
                bewaren_btn = None
                for b in win_btns:
                    if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                        bewaren_btn = b
                        break

                if bewaren_btn:
                    bewaren_btn.click(force=True)
                    log("   Knop 'Bewaren' geklikt! Wachten op respons...")
                    page.wait_for_timeout(8000)

                    page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_save.png"))

                    # Check for popups/dialogs
                    for idx, w in enumerate(page.query_selector_all(".x-window")):
                        if w.is_visible():
                            txt = w.inner_text().strip().replace("\n", " ")
                            log(f"   Venster na bewaren: '{txt[:200]}'")

                # Check grid table for new measure!
                log("8. Tabel overzicht controleren op nieuwe concept melding...")
                page.goto(BASE_URL, wait_until="networkidle")
                page.wait_for_timeout(5000)
                page.screenshot(path=os.path.join(OUTPUT_DIR, "03_grid_after_save.png"))

                rows = page.query_selector_all(".x-grid3-row")
                log(f"   Aantal rijen in het overzicht: {len(rows)}")
                for r_idx, r in enumerate(rows[:5]):
                    row_txt = r.inner_text().strip().replace("\n", " | ")
                    log(f"   Rij {r_idx}: {row_txt}")

        browser.close()

if __name__ == "__main__":
    run_gxt_copy()
