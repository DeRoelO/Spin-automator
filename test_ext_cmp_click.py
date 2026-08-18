import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=== TESTING EXT GXT COMPONENT FIRE EVENT FOR VLUCHTSTROOK/BERM ===")
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
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # Hover Nieuwe maatregel
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Inspect all open menu anchors and dispatch full event sequence including pointer events
        log("3. Dispatchen van pointer events op Vluchtstrook/berm...")
        res = page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('.x-menu-item, a, span, div'));
            const target = anchors.find(el => el.innerText && el.innerText.trim() === 'Vluchtstrook/berm');
            if (target) {
                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(t => {
                    const evt = new MouseEvent(t, { bubbles: true, cancelable: true, view: window });
                    target.dispatchEvent(evt);
                });
                return { found: true, id: target.id, tag: target.tagName };
            }
            return { found: false };
        }""")

        log(f"   Event dispatch resultaat: {res}")
        page.wait_for_timeout(6000)

        wins = page.query_selector_all(".x-window")
        log(f"4. Aantal geopende vensters: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = w.query_selector(".x-window-header-text").inner_text().strip()
                log(f"   [✓✓✓] SUCCESS! VENSTER GEOPEND: '{title}'")

        browser.close()

if __name__ == "__main__":
    run()
