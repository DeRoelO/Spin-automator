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

def dump_btns():
    log("=== DUMPING ALL BUTTONS IN MEASURE CREATION WINDOW ===")
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

        # Open Bestand -> Nieuwe maatregel -> Regulier
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1000)

        nieuwe_m = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        nieuwe_m.hover()
        page.wait_for_timeout(1500)

        regulier = page.locator(".x-menu-list-item", has_text="Regulier").first
        regulier.click()
        page.wait_for_timeout(7000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "dump_btns_screen.png"))

        # Find all clickable items on entire page
        all_clickables = page.query_selector_all("button, .x-btn, .x-btn-text, td.x-btn-mc, div.x-component")
        btn_details = []
        for idx, el in enumerate(all_clickables):
            try:
                if el.is_visible():
                    txt = el.inner_text().strip().replace("\n", " ")
                    cls = el.get_attribute("class") or ""
                    id_attr = el.get_attribute("id") or ""
                    if txt and len(txt) < 30 and any(k in txt.lower() for k in ["bewaar", "opslaan", "indien", "sluit", "ok", "annuleer", "concept"]):
                        btn_details.append({"idx": idx, "text": txt, "class": cls, "id": id_attr})
            except:
                pass

        log(f"Found {len(btn_details)} relevant action buttons on screen:")
        for b in btn_details:
            log(f"  Button: {b}")

        browser.close()

if __name__ == "__main__":
    dump_btns()
