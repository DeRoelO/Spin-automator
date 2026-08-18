import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
COPY_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW_COPY&viewType=GE_MEASURE_WINDOW&measureId=1107615&phaseId=0&eventId=0&isCopy=true&isInverse=false&mode=CREATE&version=-1&measureType=STATIONARY"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "debug_save_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run_debug():
    log("=========================================================================")
    log("===   DEBUGGING SPIN SAVE (BEWAREN) BEHAVIOR & PERSISTENCE VERIFICATION  ===")
    log("=========================================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        # Listen for console and network requests
        page.on("console", lambda msg: log(f"BROWSER CONSOLE: {msg.type}: {msg.text}"))
        
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

        log("3. Maatregel Kopiëren venster openen...")
        page.goto(COPY_URL, wait_until="networkidle")
        page.wait_for_timeout(6000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_editor_opened.png"))

        # Inspect current Maatregelnummer before saving
        mn_el = page.locator("input[name='measureId']").first
        mn_before = mn_el.input_value() if mn_el.is_visible() else "N/A"
        log(f"   Maatregelnummer voor opslaan: '{mn_before}'")

        # Fill start and end dates
        page.evaluate("""() => {
            const setVal = (name, val) => {
                const el = document.querySelector(`input[name='${name}']`);
                if (el) {
                    el.removeAttribute('readonly');
                    el.value = val;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('blur', { bubbles: true }));
                }
            };
            setVal('start', '10.10.2026, 08:00');
            setVal('end', '10.10.2026, 16:00');
        }""")
        page.wait_for_timeout(1000)

        # Check for Toon route button
        toon_route_btn = None
        for b in page.query_selector_all("button, .x-btn-text"):
            if b.is_visible() and "toon route" in b.inner_text().lower():
                toon_route_btn = b
                break

        if toon_route_btn:
            log("   Klikken op 'Toon route' om de route/locatie te berekenen...")
            toon_route_btn.click(force=True)
            page.wait_for_timeout(3000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_toon_route.png"))

        # Click Bewaren button
        log("4. Klikken op 'Bewaren' (Concept opslaan)...")
        all_btns = page.query_selector_all("button, .x-btn-text, .x-btn")
        bewaren_btn = None
        for b in all_btns:
            if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                bewaren_btn = b
                break

        if bewaren_btn:
            bewaren_btn.click(force=True)
            log("   'Bewaren' knop ingedrukt. Schermverloop analyseren over 10 seconden...")

            for t in range(1, 10):
                page.wait_for_timeout(1000)
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"03_save_step_{t}.png"))

                # Check for popups/dialogs
                wins = page.query_selector_all(".x-window")
                for idx, w in enumerate(wins):
                    if w.is_visible():
                        txt = w.inner_text().strip().replace("\n", " ")
                        log(f"   [t={t}s] Venster visible: '{txt[:150]}'")
                        
                        # Check for Ja / Ok buttons inside popup dialog
                        popup_btns = w.query_selector_all("button, .x-btn-text")
                        for pb in popup_btns:
                            pbtxt = pb.inner_text().strip().lower()
                            if pb.is_visible() and pbtxt in ["ja", "ok", "opslaan", "bevestigen"]:
                                log(f"   [t={t}s] POPUP BEVESTIGINGSKNOP GEVONDEN: '{pbtxt}'. Klikken...")
                                pb.click(force=True)
                                page.wait_for_timeout(2000)
                                break

        # Check Maatregelnummer after saving
        mn_after = mn_el.input_value() if mn_el.is_visible() else "N/A"
        log(f"5. Maatregelnummer na opslaan: '{mn_after}'")

        # Navigate back to main grid / dashboard to verify measure in grid list!
        log("6. Terugkeren naar Hoofdscherm / Maatregelen Overzicht om de lijst te controleren...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(5000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "04_dashboard_grid_after_save.png"))

        # Inspect table rows in the grid
        rows = page.query_selector_all(".x-grid3-row")
        log(f"   Aantal rijen in het overzicht: {len(rows)}")
        for r_idx, r in enumerate(rows[:10]):
            try:
                row_txt = r.inner_text().strip().replace("\n", " | ")
                log(f"   Rij {r_idx}: {row_txt[:120]}")
            except:
                pass

        browser.close()

if __name__ == "__main__":
    run_debug()
