import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
CLEAN_SHOULDER_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW_NEW&viewType=GE_MEASURE_WINDOW&phaseId=0&eventId=0&isCopy=false&isInverse=false&mode=CREATE&measureType=SHOULDER"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=== TESTING CLEAN VLUCHTSTROOK/BERM FORM (No measureId parameter) ===")
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

        # Open clean Vluchtstrook/berm form
        log("3. Schoon Vluchtstrook/berm formulier openen (mode=CREATE & measureType=SHOULDER)...")
        page.evaluate(f"window.location.href = '{CLEAN_SHOULDER_URL}';")
        page.wait_for_timeout(6000)

        wins = page.query_selector_all(".x-window")
        log(f"4. Aantal geopende vensters: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = ""
                try:
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"   [🎉🎉🎉] VENSTER TITEL: '{title}'")

                if title != "Fout":
                    log("5. Vluchtstrook/berm formulier gegevens uit screenshot invullen...")
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

                        setVal('start', '06.09.2026, 09:00');
                        setVal('end', '06.09.2026, 15:00');
                        setVal('location.fromRoadNumber', 'A15');
                        setVal('location.fromRoadSide', 'Re');
                        setVal('location.fromMeter', '150,000');
                        setVal('location.toRoadNumber', 'A15');
                        setVal('location.toRoadSide', 'Re');
                        setVal('location.toMeter', '165,000');
                        setVal('clearanceWidth', '7,00');
                        setVal('contractNumber', 'NL-31154600-inspecties voor MJPV');
                        setVal('contractorName', 'DHV Royal Haskoning');
                        setVal('contactPersonName', 'van Haandel, Roel');
                        setVal('contactPersonPhone', '06-58877256');
                        setVal('contactPersonEmail', 'roel.van.haandel@haskoning.com');
                    }""")
                    page.wait_for_timeout(1500)

                    # Click Bewaren
                    all_btns = w.query_selector_all("button, .x-btn-text")
                    for b in all_btns:
                        if b.is_visible() and b.inner_text().strip().lower() == "bewaren":
                            log("6. Klikken op 'Bewaren'...")
                            b.click(force=True)
                            page.wait_for_timeout(8000)
                            break

        # Check if saved
        log("7. Dashboard verversen om opgeslagen concept te verifiëren...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(5000)

        wissen_btn = page.locator(".x-btn", has_text="Wissen").first
        if wissen_btn.is_visible():
            wissen_btn.click()
            page.wait_for_timeout(1000)

        toepassen_btn = page.locator(".x-btn", has_text="Toepassen").first
        if toepassen_btn.is_visible():
            toepassen_btn.click()
            page.wait_for_timeout(5000)

        rows = page.query_selector_all(".x-grid3-row")
        log(f"   Totaal rijen op het dashboard: {len(rows)}")
        for r_idx, r in enumerate(rows[:8]):
            txt = r.inner_text().strip().replace("\n", " | ")
            log(f"   Rij {r_idx}: {txt[:140]}")
            if "06.09.2026" in txt:
                log(f"   [🎉🎉🎉] EXTREME VICTORY! VLUCHTSTROOK/BERM CONCEPT OPGEGESLAGEN EN BEVESTIGD IN HET OVERZICHT: Rij {r_idx}: {txt}")

        browser.close()

if __name__ == "__main__":
    run()
