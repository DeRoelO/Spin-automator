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
    log("=========================================================")
    log("  SPIN PROOF OF CONCEPT: MAATREGEL CREËREN (CONCEPT)     ")
    log("=========================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        log("1. Inloggen op SPIN Rijkswaterstaat...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Login Step 1: Click initial notice dialog OK button
        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                page.wait_for_timeout(1500)
                break

        # Login Step 2: Fill credentials & submit
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

        # Step 3: Click Bestand menu
        log("3. Menu 'Bestand' openen...")
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1000)

        # Step 4: Hover over 'Nieuwe maatregel' to trigger sub-menu
        log("4. Hoveren over sub-menu 'Nieuwe maatregel'...")
        nieuwe_m = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        nieuwe_m.hover()
        page.wait_for_timeout(1500)

        # Step 5: Click 'Regulier' sub-menu item
        log("5. Klikken op 'Regulier' in het sub-menu...")
        regulier = page.locator(".x-menu-list-item", has_text="Regulier").first
        regulier.click()
        page.wait_for_timeout(6000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_window_open.png"))

        log("6. Formulier invullen met testgegevens...")

        # Fill start date
        start_el = page.locator(".x-window input[name='start']").first
        if start_el.is_visible():
            start_el.fill("01.09.2026, 21:00")
            log("   [✓] Startdatum ingesteld: 01.09.2026, 21:00")

        # Fill end date
        end_el = page.locator(".x-window input[name='end']").first
        if end_el.is_visible():
            end_el.fill("02.09.2026, 05:00")
            log("   [✓] Einddatum ingesteld: 02.09.2026, 05:00")

        # Fill road number
        road_el = page.locator(".x-window input[name='location.fromRoadNumber']").first
        if road_el.is_visible():
            road_el.fill("A12")
            log("   [✓] Wegnummer ingesteld: A12")

        # Fill from meter
        fm_el = page.locator(".x-window input[name='location.fromMeter']").first
        if fm_el.is_visible():
            fm_el.fill("45.0")
            log("   [✓] Van km ingesteld: 45.0")

        # Fill to meter
        tm_el = page.locator(".x-window input[name='location.toMeter']").first
        if tm_el.is_visible():
            tm_el.fill("47.0")
            log("   [✓] Tot km ingesteld: 47.0")

        page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_form_filled.png"))

        # Step 7: Click 'Bewaren' button inside window
        log("7. Klikken op 'Bewaren' (Concept Opslaan in SPIN)...")
        win_buttons = page.query_selector_all(".x-window button, .x-window .x-btn-text")
        bewaren_btn = None
        for b in win_buttons:
            if b.inner_text().strip().lower() == "bewaren":
                bewaren_btn = b
                break

        if bewaren_btn and bewaren_btn.is_visible():
            bewaren_btn.click()
            log("   [✓] Knop 'Bewaren' geklikt! Concept wordt opgeslagen...")
            page.wait_for_timeout(8000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "poc_final_result.png"))

            with open(os.path.join(OUTPUT_DIR, "poc_final_result.html"), "w", encoding="utf-8") as f:
                f.write(page.content())

            log("=========================================================")
            log("  SUCCESS! CONCEPT PROOF OF CONCEPT SUCCESVOL VERWERKT!  ")
            log("=========================================================")
        else:
            log("  [!] Knop 'Bewaren' niet gevonden.")
            avail = [b.inner_text().strip() for b in win_buttons if b.is_visible()]
            log(f"  Zichtbare venster knoppen: {avail}")

        browser.close()

if __name__ == "__main__":
    run_poc()
