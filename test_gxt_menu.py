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
    log("=== EXACT GXT SUBMENU CLICK TEST ===")
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

        # Click Bestand
        log("Clicking 'Bestand'...")
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1000)

        # Click / Hover 'Nieuwe maatregel'
        log("Hovering 'Nieuwe maatregel'...")
        nm = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        nm.hover()
        page.wait_for_timeout(1500)

        # Find visible menu items with Regulier
        all_visible = page.query_selector_all(".x-menu-list-item")
        reg_item = None
        for item in all_visible:
            if item.is_visible() and "regulier" in item.inner_text().strip().lower():
                reg_item = item
                break

        if reg_item:
            log(f"Found 'Regulier' item with class: '{reg_item.get_attribute('class')}'. Clicking inner element...")
            # Click inner anchor / text span
            inner = reg_item.query_selector("a, span, div") or reg_item
            inner.click()
            page.wait_for_timeout(6000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "gxt_regulier_clicked.png"))

            # Check for open window
            wins = page.query_selector_all(".x-window")
            log(f"Open modal windows after click: {len(wins)}")
            for w in wins:
                if w.is_visible():
                    log(f"Window title: '{w.query_selector('.x-window-header-text').inner_text().strip()}'")
                    # List all inputs
                    inps = w.query_selector_all("input")
                    log(f"Window inputs: {len(inps)}")
                    btns = w.query_selector_all("button, .x-btn-text")
                    log(f"Window buttons: {[b.inner_text().strip() for b in btns if b.is_visible()]}")
        else:
            log("Regulier sub-item not found.")

        browser.close()

if __name__ == "__main__":
    run()
