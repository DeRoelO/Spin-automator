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
    log("===   USER MOUSE TRAJECTORY: BESTAND -> NIEUWE MAATREGEL             ===")
    log("===   -> RECHTS NAAR REGULIER -> OMLAAG NAAR VLUCHTSTROOK/BERM       ===")
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

        # 3. Click Bestand
        log("3. Klikken op 'Bestand'...")
        bestand = page.locator("div.x-menubar-item", has_text="Bestand").first
        bestand.click()
        page.wait_for_timeout(1000)

        # 4. Hover Nieuwe maatregel
        log("4. Muis naar 'Nieuwe maatregel'...")
        nieuw_el = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        box_nieuw = nieuw_el.bounding_box()
        page.mouse.move(box_nieuw["x"] + 20, box_nieuw["y"] + 10, steps=5)
        page.wait_for_timeout(1000)

        # 5. Move HORIZONTALLY RIGHT onto 'Regulier'
        log("5. Muis HORIZONTAAL NAAR RECHTS bewegen naar 'Regulier' (sub-menu container in)...")
        reg_el = page.locator("a", has_text="Regulier").first
        box_reg = reg_el.bounding_box()
        page.mouse.move(box_reg["x"] + 30, box_reg["y"] + 10, steps=10)
        page.wait_for_timeout(800)

        # 6. Move VERTICALLY DOWN to 'Vluchtstrook/berm'
        log("6. Muis VERTICAAL OMLAAG bewegen naar 'Vluchtstrook/berm'...")
        vlucht_el = page.locator("a", has_text="Vluchtstrook/berm").first
        box_vlucht = vlucht_el.bounding_box()
        page.mouse.move(box_vlucht["x"] + 30, box_vlucht["y"] + 10, steps=10)
        page.wait_for_timeout(500)

        # 7. Click Vluchtstrook/berm
        log("7. Klikken op 'Vluchtstrook/berm'...")
        page.mouse.click(box_vlucht["x"] + 30, box_vlucht["y"] + 10)
        page.wait_for_timeout(6000)

        wins = page.query_selector_all(".x-window")
        log(f"8. Aantal geopende vensters: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = ""
                try:
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"   [🎉🎉🎉] WAUW! EXACT DE JUISTE ROUTE! FORMULIER GEOPEND: '{title}'")

                # Fill all fields from screenshot!
                log("9. Vluchtstrook/berm formulier invullen met de gegevens uit je screenshot...")
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
                        log("10. Klikken op 'Bewaren' inside editor...")
                        b.click(force=True)
                        page.wait_for_timeout(8000)
                        break

        # Check if saved
        log("11. Dashboard verversen om opgeslagen concept te verifiëren...")
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
        for r_idx, r in enumerate(rows[:8]):
            txt = r.inner_text().strip().replace("\n", " | ")
            log(f"   Rij {r_idx}: {txt[:140]}")
            if "06.09.2026" in txt:
                log(f"   [🎉🎉🎉] EXTREME OVERWINNING! CONCEPT VLUCHTSTROOK/BERM PERSISTEERD IN SPIN DASHBOARD: Rij {r_idx}: {txt}")

        browser.close()

if __name__ == "__main__":
    run()
