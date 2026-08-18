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
    log("=== SPIN PROOF OF CONCEPT: REGULIERE MAATREGEL AANMAKEN (CONCEPT) ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("1. Inloggen op SPIN...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Login dialog step 1
        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                page.wait_for_timeout(1500)
                break

        # Fill credentials
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
        log("2. Ingelogd als Roel van Haandel.")

        # Open Bestand menu
        log("3. Menu 'Bestand' openen...")
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1000)

        # Hover 'Nieuwe maatregel'
        log("4. Hoveren over 'Nieuwe maatregel'...")
        nieuwe_m = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        nieuwe_m.hover()
        page.wait_for_timeout(1500)

        # Click 'Regulier'
        log("5. Klikken op 'Regulier' in het sub-menu...")
        regulier = page.locator(".x-menu-list-item", has_text="Regulier").first
        regulier.click()
        page.wait_for_timeout(6000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_regulier_window.png"))
        with open(os.path.join(OUTPUT_DIR, "poc_regulier_window.html"), "w", encoding="utf-8") as f:
            f.write(page.content())

        # Check open window title
        win_title = ""
        try:
            win_title = page.locator(".x-window-header-text").first.inner_text().strip()
        except:
            pass
        log(f"Venstertitel geopend: '{win_title}'")

        # Fill form fields
        log("6. Invullen van testgegevens in het formulier...")

        # Start Date
        start_el = page.locator(".x-window input[name='start']").first
        if start_el.is_visible():
            start_el.fill("01.09.2026, 21:00")
            log("  -> Startdatum: 01.09.2026, 21:00")

        # End Date
        end_el = page.locator(".x-window input[name='end']").first
        if end_el.is_visible():
            end_el.fill("02.09.2026, 05:00")
            log("  -> Einddatum: 02.09.2026, 05:00")

        # Road number
        road_el = page.locator(".x-window input[name='location.fromRoadNumber']").first
        if road_el.is_visible():
            road_el.fill("A12")
            log("  -> Wegnummer: A12")

        # From Meter
        fm_el = page.locator(".x-window input[name='location.fromMeter']").first
        if fm_el.is_visible():
            fm_el.fill("45.0")
            log("  -> Van km: 45.0")

        # To Meter
        tm_el = page.locator(".x-window input[name='location.toMeter']").first
        if tm_el.is_visible():
            tm_el.fill("47.0")
            log("  -> Tot km: 47.0")

        page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_regulier_filled.png"))

        # Click Bewaren button
        log("7. Zoeken naar knop 'Bewaren' inside window...")
        win_btns = page.query_selector_all(".x-window button, .x-window .x-btn-text")
        bewaren = None
        for b in win_btns:
            if b.inner_text().strip().lower() == "bewaren":
                bewaren = b
                break

        if bewaren and bewaren.is_visible():
            bewaren.click()
            log("-> KNOP 'BEWAREN' GEKLIKT! CONCEPT WORDT OPSLAGEN IN SPIN...")
            page.wait_for_timeout(8000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_regulier_saved.png"))
            
            with open(os.path.join(OUTPUT_DIR, "poc_regulier_saved.html"), "w", encoding="utf-8") as f:
                f.write(page.content())
                
            log("=== PROOF OF CONCEPT VOLTOOID! CONCEPT GEMAAKT EN BEWAARD IN SPIN ===")
        else:
            visible_btns = [b.inner_text().strip() for b in win_btns if b.is_visible()]
            log(f"Zichtbare knoppen in het venster: {visible_btns}")

        browser.close()

if __name__ == "__main__":
    run_poc()
