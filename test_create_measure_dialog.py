import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
CREATE_URL = "https://spin.rijkswaterstaat.nl/spin/?viewType=GE_MEASURE_WINDOW&mode=CREATE&measureType=STATIONARY"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "poc_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def test_dialog():
    log("Starting SPIN Measure Creation Window Test...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("1. Navigating & Logging in to SPIN...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Login
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
        log("2. Logged in successfully.")

        log(f"3. Navigating to measure creation URL: {CREATE_URL}")
        page.goto(CREATE_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "20_create_measure_dialog.png"))

        # Inspecting open windows/dialogs
        windows = page.query_selector_all(".x-window")
        log(f"Open modal windows on screen: {len(windows)}")

        window_titles = []
        for win in windows:
            if win.is_visible():
                try:
                    title = win.query_selector(".x-window-header-text").inner_text().strip()
                    window_titles.append(title)
                except:
                    pass

        log(f"Visible window titles: {window_titles}")

        # Dump buttons
        all_buttons = page.query_selector_all("button, .x-btn")
        btn_info = []
        for b in all_buttons:
            if b.is_visible():
                txt = b.inner_text().strip().replace("\n", " ")
                if txt:
                    btn_info.append(txt)

        log(f"Visible buttons on measure dialog screen: {btn_info[:25]}")

        # Scan tabs inside measure window
        tabs = page.query_selector_all(".x-tab-strip-inner, .x-tab-strip-text, .x-tab-panel-header")
        tab_names = [t.inner_text().strip() for t in tabs if t.is_visible() and t.inner_text().strip()]
        log(f"Active form tab titles: {tab_names}")

        # Inspect all form inputs inside measure creation window
        inputs = page.query_selector_all(".x-window input, .x-window textarea, .x-window select")
        log(f"Form controls inside window: {len(inputs)}")

        form_fields = []
        for idx, inp in enumerate(inputs):
            try:
                iname = inp.get_attribute("name") or ""
                iid = inp.get_attribute("id") or ""
                itype = inp.get_attribute("type") or inp.tag_name
                ival = inp.get_attribute("value") or ""
                
                lbl = ""
                try:
                    parent = inp.evaluate_handle("el => el.closest('.x-form-item')")
                    if parent:
                        lbl = parent.inner_text().strip().replace("\n", " ")
                except:
                    pass

                form_fields.append({
                    "idx": idx,
                    "name": iname,
                    "id": iid,
                    "type": itype,
                    "value": ival,
                    "label": lbl
                })
            except Exception as e:
                pass

        with open(os.path.join(OUTPUT_DIR, "create_form_fields.json"), "w", encoding="utf-8") as f:
            json.dump(form_fields, f, indent=2, ensure_ascii=False)

        log(f"Saved {len(form_fields)} form controls to create_form_fields.json")
        log("Creation window test finished.")
        browser.close()

if __name__ == "__main__":
    test_dialog()
