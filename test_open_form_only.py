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
    log("===   STAP 1 ENKEL EN ALLEEN: FORMULIER OPENEN VIA HET MENU           ===")
    log("=========================================================================")
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
        log("3. Klikken op 'Bestand' in de menubalk...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1500)

        # Hover Nieuwe maatregel
        log("4. Hoveren over 'Nieuwe maatregel'...")
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(2000)

        # Try triggering the menu item via Keyboard navigation: Down to Nieuwe maatregel, Right to submenu, Down to Vluchtstrook/berm, Enter
        log("5. Via toetsenbord navigeren: Pijl omlaag -> Pijl rechts -> Pijl omlaag -> Enter...")
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        page.keyboard.press("ArrowDown")  # Move to Rijdend
        page.wait_for_timeout(500)
        page.keyboard.press("ArrowDown")  # Move to Vluchtstrook/berm
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(6000)

        wins = page.query_selector_all(".x-window")
        log(f"6. Aantal geopende vensters: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = ""
                try:
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"   [🎉] VENSTER SUCCESVOL GEOPEND! Titel: '{title}'")

        browser.close()

if __name__ == "__main__":
    run()
