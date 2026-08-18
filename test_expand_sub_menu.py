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
    log("===   CLICKING NIEUWE MAATREGEL ARROW / EXPANDER (GXT SUB-MENU)       ===")
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

        # STAP 1: Klik op 'Bestand'
        log("3. STAP 1: Klikken op 'Bestand' div.x-menubar-item...")
        bestand_el = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand_el.click()
        page.wait_for_timeout(1000)

        # STAP 2: Klik op de rechterkant (het pijltje) van 'Nieuwe maatregel'
        log("4. STAP 2: Klikken op het pijltje van 'Nieuwe maatregel'...")
        nieuw_el = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        box = nieuw_el.bounding_box()
        # Click near the right edge where aria-haspopup arrow is located
        page.mouse.click(box["x"] + box["width"] - 10, box["y"] + (box["height"] / 2))
        page.wait_for_timeout(1500)

        # STAP 3: Klik op 'Vluchtstrook/berm'
        log("5. STAP 3: Klikken op 'Vluchtstrook/berm'...")
        vlucht_el = page.locator("a, div", has_text="Vluchtstrook/berm").first
        vlucht_el.click()
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
                log(f"   [🎉🎉🎉] EXTREME OVERWINNING! FORMULIER GEOPEND: '{title}'")

        browser.close()

if __name__ == "__main__":
    run()
