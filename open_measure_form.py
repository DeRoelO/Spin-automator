import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "inspection_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def inspect_form():
    log("Starting SPIN measure form detailed inspection...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("Navigating to SPIN landing page...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Login process
        log("Checking initial modal OK button...")
        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                page.wait_for_timeout(1500)
                break

        log("Filling username and password...")
        name_input = page.locator("input[name='name']").first
        pass_input = page.locator("input[name='password']").first

        name_input.fill(USERNAME, force=True)
        pass_input.fill(PASSWORD, force=True)

        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                log("Logged in!")
                break

        page.wait_for_timeout(8000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "10_logged_in.png"))

        # Click menu "Bestand"
        log("Clicking 'Bestand' menu in main menubar...")
        bestand_menu = page.locator("div.x-menubar-item", has_text="Bestand").first
        if bestand_menu.is_visible():
            bestand_menu.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "11_bestand_menu.png"))

        # Look for visible submenus like 'Nieuwe Maatregel' or 'Nieuwe Melding'
        menu_items = page.query_selector_all(".x-menu-item, .x-component")
        log(f"Found menu items:")
        for item in menu_items:
            txt = item.inner_text().strip()
            if txt and len(txt) < 40 and ("Nieuw" in txt or "Maatregel" in txt or "Melding" in txt):
                log(f"Menu item candidate: {txt}")

        # Also try double-clicking the first row in grid
        log("Attempting double-click on first grid row...")
        first_row = page.locator(".x-grid3-row").first
        if first_row.is_visible():
            first_row.dblclick()
            page.wait_for_timeout(5000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "12_grid_row_dblclicked.png"))

        # Inspect any open GXT Window / Dialog
        windows = page.query_selector_all(".x-window")
        log(f"Open GXT Windows found: {len(windows)}")

        for idx, win in enumerate(windows):
            if win.is_visible():
                title = ""
                try:
                    title = win.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"Window {idx} title: '{title}'")
                
                # Extract all form inputs inside this window
                win_inputs = win.query_selector_all("input, textarea, select")
                log(f"Window {idx} inputs count: {len(win_inputs)}")

                fields_detail = []
                for inp in win_inputs:
                    try:
                        iname = inp.get_attribute("name") or ""
                        iid = inp.get_attribute("id") or ""
                        itype = inp.get_attribute("type") or inp.tag_name
                        ival = inp.get_attribute("value") or ""
                        
                        # Find closest label
                        lbl = ""
                        try:
                            parent = inp.evaluate_handle("el => el.closest('.x-form-item')")
                            if parent:
                                lbl = parent.inner_text().strip().replace("\n", " ")
                        except:
                            pass

                        fields_detail.append({
                            "name": iname,
                            "id": iid,
                            "type": itype,
                            "value": ival,
                            "label": lbl
                        })
                    except Exception as e:
                        pass

                with open(os.path.join(OUTPUT_DIR, f"window_{idx}_fields.json"), "w", encoding="utf-8") as f:
                    json.dump(fields_detail, f, indent=2, ensure_ascii=False)

        log("Form inspection complete!")
        browser.close()

if __name__ == "__main__":
    inspect_form()
