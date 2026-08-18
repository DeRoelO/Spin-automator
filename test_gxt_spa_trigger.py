import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "spa_trigger_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   TESTING GXT SPA IN-PAGE WINDOW TRIGGER (No page reload)         ===")
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

        # Execute JS event to open measure window in SPA
        log("3. GXT Window open event via JS dispatchen...")
        page.evaluate("""() => {
            // Find Bestand menu item and dispatch mousedown
            const bestandItem = Array.from(document.querySelectorAll('.x-menubar-item')).find(el => el.innerText.trim() === 'Bestand');
            if (bestandItem) {
                const evt = new MouseEvent('mousedown', { bubbles: true, cancelable: true });
                bestandItem.dispatchEvent(evt);
            }
        }""")
        page.wait_for_timeout(1500)

        page.evaluate("""() => {
            // Find Nieuwe maatregel and dispatch mouseover
            const items = Array.from(document.querySelectorAll('.x-menu-item'));
            const nieuwItem = items.find(el => el.innerText && el.innerText.includes('Nieuwe maatregel'));
            if (nieuwItem) {
                nieuwItem.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, cancelable: true }));
                nieuwItem.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
            }
        }""")
        page.wait_for_timeout(1500)

        page.evaluate("""() => {
            // Find Regulier and dispatch mousedown + mouseup + click
            const items = Array.from(document.querySelectorAll('.x-menu-item, a, span'));
            const regItem = items.find(el => el.innerText && el.innerText.trim() === 'Regulier');
            if (regItem) {
                ['mouseover', 'mousedown', 'mouseup', 'click'].forEach(t => {
                    regItem.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true }));
                });
            }
        }""")
        page.wait_for_timeout(5000)

        wins = page.query_selector_all(".x-window")
        log(f"4. Geopende vensters: {len(wins)}")

        for idx, w in enumerate(wins):
            if w.is_visible():
                title = w.query_selector(".x-window-header-text").inner_text().strip()
                log(f"   [✓✓✓] SUCCESS! VENSTER GEOPEND: '{title}'")

                # Fill dates and save
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
                    setVal('start', '25.12.2026, 09:00');
                    setVal('end', '25.12.2026, 15:00');
                    setVal('location.fromRoadNumber', 'A15');
                    setVal('location.fromRoadSide', 'Re');
                    setVal('location.fromMeter', '150,000');
                    setVal('location.toRoadNumber', 'A15');
                    setVal('location.toRoadSide', 'Re');
                    setVal('location.toMeter', '165,000');
                }""")
                page.wait_for_timeout(1000)

                # Click Bewaren
                all_btns = w.query_selector_all("button, .x-btn-text")
                for b in all_btns:
                    if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                        log("5. Klikken op 'Bewaren'...")
                        b.click(force=True)
                        page.wait_for_timeout(8000)
                        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_bewaren.png"))
                        break

        browser.close()

if __name__ == "__main__":
    run()
