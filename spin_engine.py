import os
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
COPY_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW_COPY&viewType=GE_MEASURE_WINDOW&measureId=1107615&phaseId=0&eventId=0&isCopy=true&isInverse=false&mode=CREATE&version=-1&measureType=STATIONARY"

def get_profile():
    cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def update_profile(new_data):
    cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
    profile = get_profile()
    profile.update(new_data)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    return profile

def set_input(page, name, val):
    if not val:
        return
    try:
        page.evaluate("""({name, val}) => {
            const inputs = document.querySelectorAll(`input[name='${name}']`);
            inputs.forEach(inp => {
                inp.removeAttribute('readonly');
                inp.value = val;
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                inp.dispatchEvent(new Event('blur', { bubbles: true }));
            });
        }""", {"name": name, "val": str(val)})
    except Exception as e:
        print(f"Error setting '{name}': {e}", flush=True)

def set_combo(page, name, val):
    if not val:
        return
    try:
        page.evaluate("""({name, val}) => {
            const inp = document.querySelector(`input[name='${name}']`);
            if (inp) {
                inp.value = val;
                inp.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""", {"name": name, "val": str(val)})
    except Exception as e:
        print(f"Error setting combo '{name}': {e}", flush=True)

def login_spin(page):
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(3000)

    # Initial dialog
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

def submit_measure(measure_data, is_draft=True):
    profile = get_profile()
    # Merge measure_data with profile defaults
    merged = {**profile, **measure_data}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        login_spin(page)

        page.goto(COPY_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)

        # Fill Algemeen & Locatie
        set_combo(page, "bestekId", merged.get("bestekId"))
        set_input(page, "start", merged.get("start"))
        set_input(page, "end", merged.get("end"))
        set_combo(page, "roadworkType", merged.get("roadworkType"))
        set_combo(page, "managingDistrict", merged.get("managingDistrict"))

        set_combo(page, "location.fromRoadNumber", merged.get("location.fromRoadNumber"))
        set_combo(page, "location.fromRoadSide", merged.get("location.fromRoadSide", "Re"))
        set_input(page, "location.fromMeter", merged.get("location.fromMeter"))
        set_combo(page, "location.betweenName", merged.get("location.betweenName"))
        set_combo(page, "location.secondaryName", merged.get("location.secondaryName"))

        set_combo(page, "location.toRoadNumber", merged.get("location.toRoadNumber"))
        set_combo(page, "location.toRoadSide", merged.get("location.toRoadSide", "Re"))
        set_input(page, "location.toMeter", merged.get("location.toMeter"))
        set_combo(page, "location.andName", merged.get("location.andName"))
        set_combo(page, "location.primaryName", merged.get("location.primaryName"))

        # Verkeer
        set_combo(page, "trafficHindranceClass", merged.get("trafficHindranceClass"))
        set_combo(page, "roadblockType", merged.get("roadblockType"))
        set_input(page, "widthConstraint", merged.get("widthConstraint"))

        # Aannemer
        set_combo(page, "trafficDesk", merged.get("trafficDesk"))

        target_button = "bewaren" if is_draft else "indienen"
        
        all_btns = page.query_selector_all("button, .x-btn, .x-btn-text")
        action_btn = None
        for b in all_btns:
            if b.inner_text().strip().lower() == target_button:
                action_btn = b
                break

        success = False
        message = ""

        if action_btn:
            try:
                action_btn.click(force=True)
            except:
                page.evaluate("el => el.click()", action_btn)

            page.wait_for_timeout(8000)
            success = True
            message = f"Maatregel succesvol opgeslagen als {'Concept' if is_draft else 'Definitief'}!"

            # Update profile with last-used values
            update_profile(measure_data)
        else:
            success = False
            message = f"Knop '{target_button}' niet gevonden in SPIN venster."

        browser.close()
        return {"success": success, "message": message, "data": merged}
