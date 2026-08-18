import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "poc_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def run_poc():
    log("=== STARTING SPIN PROOF OF CONCEPT (CONCEPT MAKEN) ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("1. Navigating to SPIN...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Login
        log("2. Logging in...")
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
        log("3. Logged in successfully!")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_dashboard.png"))

        # Open 'Bestand' menu
        log("4. Opening 'Bestand' menu...")
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "02_bestand_menu.png"))

        # Click 'Nieuwe maatregel'
        log("5. Clicking 'Nieuwe maatregel'...")
        nieuwe_maatregel = page.locator(".x-menu-item-text", has_text="Nieuwe maatregel").first
        if not nieuwe_maatregel.is_visible():
            nieuwe_maatregel = page.locator("text=Nieuwe maatregel").first

        nieuwe_maatregel.click()
        page.wait_for_timeout(5000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "03_new_measure_window.png"))

        # Save HTML of the newly opened window
        with open(os.path.join(OUTPUT_DIR, "03_new_measure_window.html"), "w", encoding="utf-8") as f:
            f.write(page.content())

        # Inspect open window tabs & fields
        log("6. Inspecting tabs and dropdowns in the window...")
        tabs = page.query_selector_all(".x-tab-strip-inner, .x-tab-strip-text")
        tab_titles = [t.inner_text().strip() for t in tabs if t.inner_text().strip()]
        log(f"Discovered tabs: {tab_titles}")

        # Scan dropdown comboboxes
        triggers = page.query_selector_all(".x-form-trigger-arrow")
        log(f"Found {len(triggers)} dropdown comboboxes in form.")

        dropdown_data = {}
        for idx, trigger in enumerate(triggers):
            try:
                # Find parent label
                parent = trigger.evaluate_handle("el => el.closest('.x-form-item')")
                lbl = ""
                if parent:
                    lbl = parent.inner_text().replace("\n", " ").strip()
                
                if trigger.is_visible():
                    trigger.click()
                    page.wait_for_timeout(500)
                    
                    # Extract list items from open combo list
                    items = page.query_selector_all(".x-combo-list-item")
                    visible_items = [it.inner_text().strip() for it in items if it.is_visible() and it.inner_text().strip()]
                    if visible_items:
                        dropdown_data[lbl or f"dropdown_{idx}"] = visible_items[:20]
                        log(f"Dropdown '{lbl}': {len(visible_items)} options found (e.g. {visible_items[:3]})")
                    
                    # Close combo by clicking trigger again or Escape
                    trigger.click()
                    page.wait_for_timeout(300)
            except Exception as e:
                pass

        with open(os.path.join(OUTPUT_DIR, "dropdown_options.json"), "w", encoding="utf-8") as f:
            json.dump(dropdown_data, f, indent=2, ensure_ascii=False)

        # Attempting to fill test data into visible fields
        log("7. Filling test data into measure form...")
        
        # Start date
        start_field = page.locator("input[name='start']").first
        if start_field.is_visible():
            start_field.fill("01.09.2026, 21:00")
            log("Filled Start: 01.09.2026, 21:00")

        # End date
        end_field = page.locator("input[name='end']").first
        if end_field.is_visible():
            end_field.fill("02.09.2026, 05:00")
            log("Filled End: 02.09.2026, 05:00")

        # Road number
        road_field = page.locator("input[name='location.fromRoadNumber']").first
        if road_field.is_visible():
            road_field.fill("A12")
            log("Filled Road: A12")

        # From meter
        from_meter = page.locator("input[name='location.fromMeter']").first
        if from_meter.is_visible():
            from_meter.fill("45.0")
            log("Filled From meter: 45.0")

        # To meter
        to_meter = page.locator("input[name='location.toMeter']").first
        if to_meter.is_visible():
            to_meter.fill("47.0")
            log("Filled To meter: 47.0")

        page.screenshot(path=os.path.join(OUTPUT_DIR, "04_form_filled.png"))

        # Look for 'Concept' or 'Opslaan' or 'Concept opslaan' button
        log("8. Searching for 'Concept' or 'Opslaan' button...")
        save_buttons = page.query_selector_all("button, .x-btn-text")
        concept_btn = None
        for b in save_buttons:
            txt = b.inner_text().strip().lower()
            if "concept" in txt or "opslaan" in txt:
                log(f"Found save button candidate: '{b.inner_text().strip()}'")
                if "concept" in txt:
                    concept_btn = b
                    break
                elif not concept_btn:
                    concept_btn = b

        if concept_btn:
            log(f"Clicking save button: '{concept_btn.inner_text().strip()}'...")
            concept_btn.click()
            page.wait_for_timeout(6000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "05_after_concept_save.png"))

            with open(os.path.join(OUTPUT_DIR, "05_after_concept_save.html"), "w", encoding="utf-8") as f:
                f.write(page.content())
            
            log("9. Concept save operation completed!")
        else:
            log("No explicit 'Concept' / 'Opslaan' button found among current buttons.")
            button_texts = [b.inner_text().strip() for b in save_buttons if b.inner_text().strip()]
            log(f"All available buttons on screen: {button_texts}")

        browser.close()

if __name__ == "__main__":
    run_poc()
