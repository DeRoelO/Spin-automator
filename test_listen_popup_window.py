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
    log("=========================================================================")
    log("===   EUREKA TEST: LISTEN FOR POPUP BROWSER WINDOW (window.open)      ===")
    log("=========================================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        
        # Track all new popup windows spawned by browser
        popups = []
        context.on("page", lambda new_page: popups.append(new_page))

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

        # Reset popups list
        popups.clear()

        # STAP 1: Klik Bestand
        log("3. STAP 1: Klikken op 'Bestand'...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # STAP 2: Klik Nieuwe maatregel
        log("4. STAP 2: Klikken op 'Nieuwe maatregel'...")
        nieuw_el = page.locator("a.x-menu-item", has_text="Nieuwe maatregel").first
        nieuw_el.hover()
        page.wait_for_timeout(500)
        box = nieuw_el.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"] - 10, box["y"] + (box["height"] / 2))
        else:
            nieuw_el.click()
        page.wait_for_timeout(1000)

        # STAP 3: Klik Vluchtstrook/berm en luister naar POPUP
        log("5. STAP 3: Klikken op 'Vluchtstrook/berm'...")
        target_el = page.locator("a.x-menu-item", has_text="Vluchtstrook/berm").first
        
        try:
            with page.expect_popup(timeout=8000) as popup_info:
                target_el.click(force=True)
            popup_page = popup_info.value
            log(f"   [🎉🎉🎉] EXTREME EUREKA! NIEUW POPUP VENSTER GEOPEND! URL: {popup_page.url}")
        except Exception as e:
            log(f"   Popup event timeout of niet opgevangen via expect_popup: {e}")
            target_el.click(force=True)
            page.wait_for_timeout(5000)

        log(f"6. Totaal aantal geopende browser-vensters/pagina's in context: {len(context.pages)}")
        for p_idx, p_obj in enumerate(context.pages):
            log(f"   Venster {p_idx}: URL = '{p_obj.url}', Title = '{p_obj.title()}'")

        browser.close()

if __name__ == "__main__":
    run()
