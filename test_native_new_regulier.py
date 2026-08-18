import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_native_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   NATIVE GXT BESTAND -> NIEUWE MAATREGEL -> REGULIER TEST          ===")
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

        # Open Bestand menu
        log("3. Menu 'Bestand' openen...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # Hover Nieuwe maatregel
        log("4. Hoveren over 'Nieuwe maatregel'...")
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Click Regulier menu item via JavaScript click on .x-menu-item-text
        log("5. Klikken op 'Regulier' in het sub-menu...")
        page.evaluate("""() => {
            const items = document.querySelectorAll('.x-menu-list-item, .x-menu-item-text, span, a');
            for (let el of items) {
                if (el.innerText && el.innerText.trim() === 'Regulier') {
                    el.click();
                    break;
                }
            }
        }""")
        page.wait_for_timeout(6000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_regulier_click.png"))

        # Inspect visible x-window modals
        wins = page.query_selector_all(".x-window")
        log(f"Aantal geopende vensters: {len(wins)}")

        active_win = None
        for w in wins:
            if w.is_visible():
                title = w.query_selector(".x-window-header-text").inner_text().strip()
                log(f"   Venster geopend! Titel: '{title}'")
                active_win = w
                break

        if active_win:
            log("6. Invoervelden invullen in het geopende venster...")
            page.evaluate("""() => {
                const setInput = (name, val) => {
                    const el = document.querySelector(`.x-window input[name='${name}']`);
                    if (el) {
                        el.removeAttribute('readonly');
                        el.value = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new Event('blur', { bubbles: true }));
                    }
                };

                setInput('start', '20.10.2026, 09:00');
                setInput('end', '20.10.2026, 15:00');
                setInput('location.fromMeter', '150,000');
                setInput('location.toMeter', '165,000');
                setInput('widthConstraint', '7,00');
            }""")
            page.wait_for_timeout(1000)

            # Click Bewaren
            log("7. Klikken op 'Bewaren' (Concept Opslaan)...")
            win_btns = active_win.query_selector_all("button, .x-btn-text")
            bewaren_btn = None
            for b in win_btns:
                if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                    bewaren_btn = b
                    break

            if bewaren_btn:
                bewaren_btn.click(force=True)
                log("   Knop 'Bewaren' geklikt!")
                page.wait_for_timeout(8000)
                page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_bewaren.png"))

                # Check popups
                for idx, w in enumerate(page.query_selector_all(".x-window")):
                    if w.is_visible():
                        txt = w.inner_text().strip().replace("\n", " ")
                        log(f"   Popup {idx}: '{txt[:200]}'")

            # Verify grid rows
            log("8. Controle van het maatregelenoverzicht op het dashboard...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(5000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "03_grid_final.png"))

            rows = page.query_selector_all(".x-grid3-row")
            log(f"   Totaal aantal rijen in de tabel: {len(rows)}")
            for r_idx, r in enumerate(rows[:5]):
                row_txt = r.inner_text().strip().replace("\n", " | ")
                log(f"   Rij {r_idx}: {row_txt}")

        browser.close()

if __name__ == "__main__":
    run()
