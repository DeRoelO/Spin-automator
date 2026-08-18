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

def inspect_menu():
    log("=== INSPECTING MENU HIERARCHY ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

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

        # Click Bestand
        log("Clicking 'Bestand' menu item...")
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1500)

        # Dump all elements in open menus (.x-menu-list, .x-menu-item)
        menu_elements = page.query_selector_all(".x-menu, .x-menu-item, .x-menu-list-item, a, div")
        visible_menu_texts = []
        for el in menu_elements:
            try:
                if el.is_visible():
                    txt = el.inner_text().strip()
                    cls = el.get_attribute("class") or ""
                    id_attr = el.get_attribute("id") or ""
                    if txt and len(txt) < 50 and ("Nieuw" in txt or "Maatregel" in txt or "Bestand" in txt or "Kopie" in txt):
                        visible_menu_texts.append({"text": txt, "class": cls, "id": id_attr})
            except:
                pass

        log(f"Visible menu elements ({len(visible_menu_texts)}):")
        for item in visible_menu_texts:
            log(f"  -> {item}")

        browser.close()

if __name__ == "__main__":
    inspect_menu()
