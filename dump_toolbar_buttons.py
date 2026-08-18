import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_toolbar_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=== DUMPING ALL TOOLBAR & MENU BUTTONS ON SPIN DASHBOARD ===")
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

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_dashboard_full.png"))

        # Find all buttons / toolbars in document
        toolbars = page.query_selector_all(".x-toolbar, .x-panel-tbar, .x-panel-bbar, .x-btn")
        log(f"Found {len(toolbars)} toolbar elements. Dumping text & classes:")

        for idx, tb in enumerate(toolbars):
            try:
                if tb.is_visible():
                    txt = tb.inner_text().strip().replace("\n", " ")
                    cls = tb.get_attribute("class") or ""
                    log(f"Toolbar {idx} [{cls[:40]}]: '{txt}'")
            except:
                pass

        browser.close()

if __name__ == "__main__":
    run()
