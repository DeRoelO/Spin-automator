import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "poc_results")

def log(msg):
    print(msg, flush=True)

def run():
    log("=== TESTING DOUBLE CLICK ON GRID CELL ===")
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

        # Double click grid row cell
        cell = page.locator(".x-grid3-cell-inner").first
        if cell.is_visible():
            txt = cell.inner_text().strip()
            log(f"Double clicking cell with text: '{txt}'...")
            cell.dblclick()
            page.wait_for_timeout(6000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "dblclick_cell_result.png"))

            # Check open windows
            wins = page.query_selector_all(".x-window")
            log(f"Visible .x-window modals after dblclick: {len(wins)}")
            for w in wins:
                if w.is_visible():
                    try:
                        title = w.query_selector(".x-window-header-text").inner_text().strip()
                        log(f"Window title: '{title}'")
                    except:
                        pass

        browser.close()

if __name__ == "__main__":
    run()
