import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "copy_edit_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   GXT NATIVE COPY -> PASTE -> EDIT WORKFLOW TEST                 ===")
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

        initial_rows = len(page.query_selector_all(".x-grid3-row"))
        log(f"   Aantal rijen op dashboard vooraf: {initial_rows}")

        # Select row 0 and copy
        log("3. Rij 0 selecteren en Kopiëren...")
        row0 = page.locator(".x-grid3-row").first
        row0.click(button="right")
        page.wait_for_timeout(1000)
        page.locator(".x-menu-list-item", has_text="Kopiëren").first.click()
        page.wait_for_timeout(2000)

        # Paste row
        log("4. Rechtsklikken en Plakken...")
        row0.click(button="right")
        page.wait_for_timeout(1000)
        page.locator(".x-menu-list-item", has_text="Plakken").first.click()
        page.wait_for_timeout(4000)

        post_rows = page.query_selector_all(".x-grid3-row")
        log(f"   Aantal rijen op dashboard na Plakken: {len(post_rows)}")

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_paste.png"))

        # Double click newly pasted row or click Bewerken
        log("5. Nieuw geplakte rij dubbelklikken om editor venster te openen...")
        if len(post_rows) > 0:
            post_rows[0].dblclick()
            page.wait_for_timeout(5000)

            page.screenshot(path=os.path.join(OUTPUT_DIR, "02_editor_open.png"))

            wins = page.query_selector_all(".x-window")
            log(f"6. Aantal geopende editor vensters: {len(wins)}")

            for w in wins:
                if w.is_visible():
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                    log(f"   [✓] EDIT VENSTER GEOPEND! Titel: '{title}'")

                    # Change dates to 18.11.2026
                    log("7. Datum wijzigen naar '18.11.2026'...")
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
                        setVal('start', '18.11.2026, 09:00');
                        setVal('end', '18.11.2026, 15:00');
                    }""")
                    page.wait_for_timeout(1000)

                    # Click Bewaren
                    all_btns = w.query_selector_all("button, .x-btn-text")
                    for b in all_btns:
                        if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                            log("8. Klikken op 'Bewaren'...")
                            b.click(force=True)
                            page.wait_for_timeout(8000)
                            page.screenshot(path=os.path.join(OUTPUT_DIR, "03_after_bewaren.png"))
                            break

            # Reload dashboard & clear filters
            log("9. Controleren of concept '18.11.2026' bewaard is in het overzicht...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(5000)

            page.locator(".x-btn", has_text="Wissen").first.click()
            page.wait_for_timeout(1000)
            page.locator(".x-btn", has_text="Toepassen").first.click()
            page.wait_for_timeout(5000)

            page.screenshot(path=os.path.join(OUTPUT_DIR, "04_final_grid.png"))

            final_rows = page.query_selector_all(".x-grid3-row")
            log(f"   Totaal rijen in het overzicht: {len(final_rows)}")
            for r_idx, r in enumerate(final_rows[:10]):
                txt = r.inner_text().strip().replace("\n", " | ")
                if "18.11.2026" in txt:
                    log(f"   [🎉🎉🎉] SUCCESS! CONCEPT DEFINITIEF GEPAST EN GEBEWAARD: Rij {r_idx}: {txt}")

        browser.close()

if __name__ == "__main__":
    run()
