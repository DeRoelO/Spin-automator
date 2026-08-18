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

def run_copy():
    log("=== TESTING COPY MEASURE (KOPIËREN) WORKFLOW ===")
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
        log("Logged in!")

        # Find first row in grid
        log("Selecting first measure row in table grid...")
        first_row = page.locator(".x-grid3-row").first
        if first_row.is_visible():
            first_row.click()
            page.wait_for_timeout(1000)
            log("Selected grid row!")

            # Right-click row to bring up context menu
            first_row.click(button="right")
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "copy_context_menu.png"))

            # Check context menu options
            ctx_items = page.query_selector_all(".x-menu-list-item")
            item_texts = [i.inner_text().strip() for i in ctx_items if i.is_visible() and i.inner_text().strip()]
            log(f"Context menu items: {item_texts}")

            # Look for Kopiëren or Bewerken
            copy_item = page.locator(".x-menu-list-item", has_text="Kopiëren").first
            if not copy_item.is_visible():
                copy_item = page.locator("text=Kopiëren").first

            if copy_item.is_visible():
                log("Clicking 'Kopiëren'...")
                copy_item.click()
                page.wait_for_timeout(5000)
                page.screenshot(path=os.path.join(OUTPUT_DIR, "copy_window_opened.png"))
            else:
                log("Kopiëren not directly visible in context menu, trying 'Bestand' -> 'Kopiëren'...")
                page.locator("div.x-menubar-item", has_text="Bestand").first.click()
                page.wait_for_timeout(1000)
                page.locator(".x-menu-item", has_text="Kopiëren").first.click()
                page.wait_for_timeout(5000)
                page.screenshot(path=os.path.join(OUTPUT_DIR, "copy_bestand_window.png"))

            # Check open modal windows
            wins = page.query_selector_all(".x-window")
            log(f"Open modal windows: {len(wins)}")
            for idx, w in enumerate(wins):
                if w.is_visible():
                    title = ""
                    try:
                        title = w.query_selector(".x-window-header-text").inner_text().strip()
                    except:
                        pass
                    log(f"Window {idx} Title: '{title}'")
                    btn_list = [b.inner_text().strip() for b in w.query_selector_all("button, .x-btn-text") if b.is_visible()]
                    log(f"Window {idx} Buttons: {btn_list}")

        else:
            log("No grid rows found in current filter view.")

        browser.close()

if __name__ == "__main__":
    run_copy()
