import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_coord_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   EXACT MOUSE COORDINATE CLICK TEST: BESTAND -> REGULIER          ===")
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

        # Click Bestand menu
        log("3. Klikken op 'Bestand'...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # Hover Nieuwe maatregel
        log("4. Hoveren over 'Nieuwe maatregel'...")
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Get exact bounding box of Regulier menu item
        log("5. BoundingBox ophalen van 'Regulier' element...")
        reg_el = page.locator("a", has_text="Regulier").first
        if reg_el.is_visible():
            box = reg_el.bounding_box()
            log(f"   Bounding box: {box}")

            # Click center of bounding box
            click_x = box["x"] + box["width"] / 2
            click_y = box["y"] + box["height"] / 2
            log(f"   Muisklik op exacte coördinaten: ({click_x}, {click_y})...")
            page.mouse.click(click_x, click_y)
            page.wait_for_timeout(6000)

            page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_coord_click.png"))

            wins = page.query_selector_all(".x-window")
            log(f"6. Aantal geopende vensters na coördinaten klik: {len(wins)}")
            for idx, w in enumerate(wins):
                if w.is_visible():
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                    log(f"   [✓] VENSTER GEOPEND! Titel: '{title}'")

                    # Fill inputs
                    log("7. Formulier in het nieuwe venster invullen...")
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
                        setVal('start', '28.10.2026, 09:00');
                        setVal('end', '28.10.2026, 15:00');
                        setVal('location.fromRoadNumber', 'A12');
                        setVal('location.fromRoadSide', 'Re');
                        setVal('location.fromMeter', '130,000');
                        setVal('location.toRoadNumber', 'A12');
                        setVal('location.toRoadSide', 'Re');
                        setVal('location.toMeter', '140,000');
                    }""")
                    page.wait_for_timeout(1000)

                    # Click Bewaren inside window
                    w_btns = w.query_selector_all("button, .x-btn-text")
                    for b in w_btns:
                        if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                            log("8. Klikken op 'Bewaren' inside new measure window...")
                            b.click(force=True)
                            page.wait_for_timeout(8000)
                            page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_bewaren.png"))
                            break

            # Check Dashboard grid rows
            log("9. Controleren van het maatregelen overzicht op het dashboard...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(5000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "03_dashboard_grid.png"))

            rows = page.query_selector_all(".x-grid3-row")
            log(f"   Totaal aantal rijen in de tabel op dashboard: {len(rows)}")
            for r_idx, r in enumerate(rows[:8]):
                log(f"   Rij {r_idx}: {r.inner_text().strip().replace('\n', ' | ')[:140]}")

        else:
            log("   Regulier element niet zichtbaar.")

        browser.close()

if __name__ == "__main__":
    run()
