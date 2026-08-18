import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "gxt_el_id_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   DIRECT GXT ELEMENT ID DISPATCH: BESTAND -> REGULIER             ===")
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
        log("3. Klikken op 'Bestand'...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # Hover Nieuwe maatregel
        log("4. Hoveren over 'Nieuwe maatregel'...")
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Find element containing 'Regulier' text inside open popup and trigger click
        log("5. Zoeken in DOM naar 'Regulier' element en direct dispatchen...")
        res = page.evaluate("""() => {
            const allEls = document.querySelectorAll('*');
            for (let el of allEls) {
                if (el.children.length === 0 && el.innerText && el.innerText.trim() === 'Regulier') {
                    const target = el.closest('a') || el.closest('.x-menu-list-item') || el;
                    target.click();
                    return { found: true, tag: target.tagName, id: target.id, class: target.className };
                }
            }
            return { found: false };
        }""")

        log(f"   JS Dispatch resultaat: {res}")
        page.wait_for_timeout(6000)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_after_dispatch.png"))

        wins = page.query_selector_all(".x-window")
        log(f"6. Aantal geopende vensters: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = w.query_selector(".x-window-header-text").inner_text().strip()
                log(f"   [✓] VENSTER GEOPEND! Titel: '{title}'")

                # Fill form and click Bewaren
                log("7. Test formulier gegevens invullen...")
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
                    setVal('start', '28.10.2026, 09:00');
                    setVal('end', '28.10.2026, 15:00');
                    setVal('location.fromRoadNumber', 'A12');
                    setVal('location.fromRoadSide', 'Re');
                    setVal('location.fromMeter', '130,000');
                    setVal('location.toRoadNumber', 'A12');
                    setVal('location.toRoadSide', 'Re');
                    setVal('location.toMeter', '140,000');
                }""")
                page.wait_for_timeout(1000)

                # Click Bewaren
                w_btns = w.query_selector_all("button, .x-btn-text")
                for b in w_btns:
                    if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                        log("8. Klikken op 'Bewaren' inside window...")
                        b.click(force=True)
                        page.wait_for_timeout(8000)
                        page.screenshot(path=os.path.join(OUTPUT_DIR, "02_after_bewaren.png"))
                        break

        # Check Dashboard grid rows
        log("9. Controleren van het maatregelen overzicht op het dashboard...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(5000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "03_dashboard_grid.png"))

        rows = page.query_selector_all(".x-grid3-row")
        log(f"   Totaal rijen op het dashboard: {len(rows)}")
        for r_idx, r in enumerate(rows[:8]):
            log(f"   Rij {r_idx}: {r.inner_text().strip().replace('\n', ' | ')[:140]}")

        browser.close()

if __name__ == "__main__":
    run()
