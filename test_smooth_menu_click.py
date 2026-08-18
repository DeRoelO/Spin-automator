import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=== TESTING SMOOTH MOUSE TRAVERSAL FOR GXT SUB-MENU (VLUCHTSTROOK/BERM) ===")
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

        # Click Bestand menu
        log("3. Klikken op 'Bestand'...")
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1000)

        # Smooth mouse move to 'Nieuwe maatregel'
        log("4. Muis geleidelijk bewegen naar 'Nieuwe maatregel'...")
        nieuw_el = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        box_nieuw = nieuw_el.bounding_box()
        page.mouse.move(box_nieuw["x"] + 20, box_nieuw["y"] + 10, steps=10)
        page.wait_for_timeout(1500)

        # Smooth mouse move into the expanded sub-menu onto 'Vluchtstrook/berm'
        log("5. Muis geleidelijk naar rechts bewegen op 'Vluchtstrook/berm'...")
        target_el = page.locator("a", has_text="Vluchtstrook/berm").first
        box_target = target_el.bounding_box()
        log(f"   Vluchtstrook/berm positie: {box_target}")

        page.mouse.move(box_target["x"] + 30, box_target["y"] + 10, steps=15)
        page.wait_for_timeout(500)

        log("6. Muisklik op Vluchtstrook/berm...")
        page.mouse.click(box_target["x"] + 30, box_target["y"] + 10)
        page.wait_for_timeout(6000)

        wins = page.query_selector_all(".x-window")
        log(f"7. Aantal geopende vensters: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = ""
                try:
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"   [🎉🎉🎉] EXTREME VICTORY! FORMULIER VLUCHTSTROOK/BERM GEOPEND: '{title}'")

        browser.close()

if __name__ == "__main__":
    run()
