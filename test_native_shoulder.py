import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
SHOULDER_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW_NEW&viewType=GE_MEASURE_WINDOW&measureId=0&phaseId=0&isCopy=false&isInverse=false&mode=CREATE&version=-1&measureType=SHOULDER"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=== TESTING NATIVE VLUCHTSTROOK/BERM FORM (CREATE MODE & SHOULDER TYPE) ===")
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

        # Open Vluchtstrook/berm form natively
        log("3. Vluchtstrook/berm formulier openen (mode=CREATE & measureType=SHOULDER)...")
        page.evaluate(f"window.location.href = '{SHOULDER_URL}';")
        page.wait_for_timeout(6000)

        wins = page.query_selector_all(".x-window")
        log(f"4. Aantal geopende vensters: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = ""
                try:
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"   [🎉🎉🎉] SUCCESS! SCHOON FORMULIER GEOPEND: '{title}'")

        browser.close()

if __name__ == "__main__":
    run()
