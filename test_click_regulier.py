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

def run_test():
    log("=== TESTING EXACT REGULIER MENU CLICK & CONCEPT SAVE ===")
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

        # Click Bestand
        log("Clicking 'Bestand'...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # Hover Nieuwe maatregel
        log("Hovering 'Nieuwe maatregel'...")
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Click Regulier directly via exact text selector
        log("Clicking 'Regulier'...")
        page.locator("text='Regulier'").first.click()
        page.wait_for_timeout(5000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "regulier_clicked_screen.png"))

        # Check for open x-window dialogs
        windows = page.query_selector_all(".x-window")
        log(f"Number of open .x-window modals: {len(windows)}")

        for idx, win in enumerate(windows):
            if win.is_visible():
                title = ""
                try:
                    title = win.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"Window {idx} visible! Title: '{title}'")
                
                # Check for buttons inside win
                btns = win.query_selector_all("button, .x-btn-text")
                btn_txts = [b.inner_text().strip() for b in btns if b.is_visible() and b.inner_text().strip()]
                log(f"Window {idx} buttons: {btn_txts}")

        browser.close()

if __name__ == "__main__":
    run_test()
