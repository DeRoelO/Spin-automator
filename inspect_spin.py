import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
MEASURE_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW1107615&viewType=GE_MEASURE_WINDOW&measureId=1107615&phaseId=0&eventId=0&isCopy=false&isInverse=false&mode=EDIT&version=-1&measureType=STATIONARY"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "inspection_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def inspect():
    log(f"Starting inspection of SPIN ({BASE_URL})...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("Navigating to SPIN landing page...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(4000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_landing_page.png"))

        # Look for OK buttons on initial notice / modal
        log("Checking for initial modal OK button...")
        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                log("Found visible OK button on initial dialog. Clicking it...")
                btn.click()
                page.wait_for_timeout(2000)
                break

        page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_first_ok.png"))

        log("Filling username and password...")
        # Now fill input[name='name'] and input[name='password']
        name_input = page.locator("input[name='name']").first
        pass_input = page.locator("input[name='password']").first

        name_input.fill(USERNAME, force=True)
        pass_input.fill(PASSWORD, force=True)
        
        page.screenshot(path=os.path.join(OUTPUT_DIR, "03_credentials_entered.png"))

        log("Clicking final login OK button...")
        # Find visible OK button again
        buttons = page.query_selector_all("button")
        ok_clicked = False
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                ok_clicked = True
                log("Clicked login OK button!")
                break
        
        if not ok_clicked:
            log("Pressing Enter on password field...")
            pass_input.press("Enter")

        log("Waiting 10 seconds for main SPIN app to load...")
        page.wait_for_timeout(10000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "04_main_app.png"))

        # Save HTML after login
        with open(os.path.join(OUTPUT_DIR, "04_main_app.html"), "w", encoding="utf-8") as f:
            f.write(page.content())

        log("Checking logged-in user state...")
        body_text = page.inner_text("body")
        log(f"Body excerpt:\n{body_text[:500]}")

        log(f"Navigating to measure edit URL: {MEASURE_URL}")
        page.goto(MEASURE_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "05_measure_window.png"))

        # Save HTML of measure edit window
        with open(os.path.join(OUTPUT_DIR, "05_measure_window.html"), "w", encoding="utf-8") as f:
            f.write(page.content())

        log("Inspecting measure window form controls...")
        inputs = page.query_selector_all("input, textarea, select")
        log(f"Total form inputs found: {len(inputs)}")

        controls = []
        for idx, inp in enumerate(inputs):
            try:
                name = inp.get_attribute("name") or ""
                id_attr = inp.get_attribute("id") or ""
                itype = inp.get_attribute("type") or inp.tag_name
                val = inp.get_attribute("value") or ""
                visible = inp.is_visible()
                
                label_text = ""
                try:
                    # Get closest label text
                    parent = inp.evaluate_handle("el => el.closest('.x-form-item') || el.parentElement")
                    if parent:
                        label_text = parent.inner_text().strip().replace("\n", " ")
                except:
                    pass

                controls.append({
                    "idx": idx,
                    "name": name,
                    "id": id_attr,
                    "type": itype,
                    "value": val,
                    "visible": visible,
                    "label": label_text
                })
            except Exception as e:
                pass

        with open(os.path.join(OUTPUT_DIR, "measure_controls.json"), "w", encoding="utf-8") as f:
            json.dump(controls, f, indent=2, ensure_ascii=False)

        log(f"Successfully saved {len(controls)} controls to measure_controls.json")
        log("Inspection completed successfully!")
        browser.close()

if __name__ == "__main__":
    inspect()
