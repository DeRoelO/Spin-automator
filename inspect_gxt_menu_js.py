import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_js_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=== INSPECTING SPIN GXT MENU JS HANDLERS ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

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

        # Inspect GXT global objects or window.GE / GXT / Ext
        gxt_info = page.evaluate("""() => {
            let keys = [];
            for (let k in window) {
                if (k.toLowerCase().includes('gxt') || k.toLowerCase().includes('spin') || k.toLowerCase().includes('ext') || k.toLowerCase().includes('gwt')) {
                    keys.push(k);
                }
            }
            return {
                window_keys: keys,
                has_ext: typeof Ext !== 'undefined',
                has_gwt: typeof $wnd !== 'undefined'
            };
        }""")

        log(f"Global GXT / GWT keys found: {gxt_info}")

        # Now click Bestand
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Dump DOM structure of the open menu
        menu_html = page.evaluate("""() => {
            const menus = document.querySelectorAll('.x-menu');
            let res = [];
            menus.forEach((m, idx) => {
                if (m.offsetWidth > 0 && m.offsetHeight > 0) {
                    res.push({idx: idx, html: m.outerHTML});
                }
            });
            return res;
        }""")

        log(f"Found {len(menu_html)} open .x-menu popups:")
        for m in menu_html:
            log(f"Menu {m['idx']} HTML:\n{m['html']}")

        browser.close()

if __name__ == "__main__":
    run()
