import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_filter_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   FILTER TEST: DUMP ALL CONCEPTS IN SPIN DASHBOARD                ===")
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

        # Check status filter combobox or click 'Wissen' then 'Toepassen'
        log("3. Klikken op 'Wissen' knop om alle filters leeg te maken...")
        wissen_btn = page.locator(".x-btn", has_text="Wissen").first
        if wissen_btn.is_visible():
            wissen_btn.click()
            page.wait_for_timeout(1000)

        log("4. Klikken op 'Toepassen' om alle maatregelen/concepten te tonen...")
        toepassen_btn = page.locator(".x-btn", has_text="Toepassen").first
        if toepassen_btn.is_visible():
            toepassen_btn.click()
            page.wait_for_timeout(5000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_all_measures_unfiltered.png"))

        # Inspect table rows
        rows = page.query_selector_all(".x-grid3-row")
        log(f"5. Totaal aantal rijen in de tabel na filter wissen: {len(rows)}")

        for r_idx, r in enumerate(rows):
            try:
                row_txt = r.inner_text().strip().replace("\n", " | ")
                log(f"   Rij {r_idx}: {row_txt[:150]}")
            except:
                pass

        browser.close()

if __name__ == "__main__":
    run()
