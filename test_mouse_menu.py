import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_mouse_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   PLAYWRIGHT ANCHOR CLICK: BESTAND -> NIEUWE MAATREGEL -> REGULIER ===")
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
        log("3. Klikken op 'Bestand' menu bar item...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # Hover Nieuwe maatregel
        log("4. Hoveren over 'Nieuwe maatregel'...")
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Click the exact anchor element with text 'Regulier'
        log("5. Klikken op de 'a.x-menu-item' met tekst 'Regulier'...")
        anchor = page.locator("a.x-menu-item", has_text="Regulier").first
        if anchor.is_visible():
            anchor.click()
            log("   'Regulier' anchor succesvol ingedrukt met Playwright click!")
            page.wait_for_timeout(6000)

            wins = page.query_selector_all(".x-window")
            log(f"6. Geopende vensters: {len(wins)}")
            for idx, w in enumerate(wins):
                if w.is_visible():
                    log(f"   Venster {idx} Titel: '{w.query_selector('.x-window-header-text').inner_text().strip()}'")
                    
                    # Fill dates and test saving!
                    page.evaluate("""() => {
                        const setVal = (name, val) => {
                            const el = document.querySelector(`.x-window input[name='${name}']`);
                            if (el) {
                                el.removeAttribute('readonly');
                                el.value = val;
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                                el.dispatchEvent(new Event('blur', { bubbles: true }));
                            }
                        };
                        setVal('start', '25.10.2026, 09:00');
                        setVal('end', '25.10.2026, 15:00');
                        setVal('location.fromRoadNumber', 'A15');
                        setVal('location.fromMeter', '150,000');
                        setVal('location.toMeter', '165,000');
                    }""")
                    page.wait_for_timeout(1000)

                    # Click Bewaren
                    w_btns = w.query_selector_all("button, .x-btn-text")
                    for b in w_btns:
                        if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                            log("   Klikken op 'Bewaren' inside the new measure window...")
                            b.click(force=True)
                            page.wait_for_timeout(8000)
                            break

            # Check Dashboard grid rows
            log("7. Dashboard grid overzicht controleren...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(5000)

            rows = page.query_selector_all(".x-grid3-row")
            log(f"   Totaal aantal rijen in het grid overzicht: {len(rows)}")
            for r_idx, r in enumerate(rows[:6]):
                row_txt = r.inner_text().strip().replace("\n", " | ")
                log(f"   Rij {r_idx}: {row_txt}")

        else:
            log("   Anchor 'a.x-menu-item' met tekst 'Regulier' niet zichtbaar.")

        browser.close()

if __name__ == "__main__":
    run()
