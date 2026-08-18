import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
SCREENSHOT_FILE = r"c:\Users\908071\OneDrive - Haskoning\Desktop\Test\HA\spin-aanvrager\form_save_test.png"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   EXACT GXT FIELD POPULATION & VALIDATION TEST                    ===")
    log("=========================================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-popup-blocking", "--start-maximized"]
        )
        context = browser.new_context(no_viewport=True)
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

        # Open form via keyboard navigation
        log("3. Schoon Vluchtstrook/berm formulier openen via snelmenu...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(800)

        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)

        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)

        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(400)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(400)

        popup_page = None
        try:
            with context.expect_page(timeout=8000) as popup_info:
                page.keyboard.press("Enter")
            popup_page = popup_info.value
            log(f"-> [✓] POPUP VENSTER GEOPEND! URL = '{popup_page.url}'")
        except Exception as e:
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)
            if len(context.pages) > 1:
                popup_page = context.pages[-1]

        if popup_page:
            popup_page.wait_for_timeout(5000)

            log("4. Alle 60 GXT velden en radio-groepen instellen...")
            popup_page.evaluate("""() => {
                const setField = (name, val) => {
                    if (val === undefined || val === null) return;
                    const els = document.querySelectorAll(`input[name='${name}'], textarea[name='${name}']`);
                    els.forEach(el => {
                        el.removeAttribute('readonly');
                        el.removeAttribute('disabled');
                        el.value = val;
                        ['input', 'change', 'blur', 'keyup'].forEach(evt => {
                            el.dispatchEvent(new Event(evt, { bubbles: true }));
                        });
                    });
                };

                // Section 1: Algemene Eigenschappen
                setField('bestekId', 'NL-31154600-inspecties voor MJPV');
                setField('bestekId-hidden', '2898');
                setField('start', '06.09.2026, 09:00');
                setField('end', '06.09.2026, 15:00');
                setField('roadworkType', 'inspectie algemeen');
                setField('roadworkType-hidden', '29');
                setField('managingDistrict', 'ON District Zuid');
                setField('managingDistrict-hidden', '136');
                setField('status', 'Concept');
                setField('status-hidden', '4');

                // Section 2: Locatie
                setField('location.fromRoadNumber', 'A15');
                setField('location.fromRoadSide', 'Re');
                setField('location.fromMeter', '150,000');
                setField('location.toRoadNumber', 'A15');
                setField('location.toRoadSide', 'Re');
                setField('location.toMeter', '165,000');

                // Section 3: Verkeer
                setField('trafficHindranceClass', '1 (geen file)');
                setField('trafficHindranceClass-hidden', 'SPIN_HINDRANCE_CLASS_1');
                setField('outsideWorkableHours', 'Nee');
                setField('outsideWorkableHours-hidden', 'NO');
                setField('roadblockType', '96a-430');
                setField('roadblockType-hidden', '179');
                setField('widthConstraint', '7,00');

                // Radio Groups
                const setRadio = (groupName, val) => {
                    const rad = document.querySelector(`input[name='${groupName}'][value='${val}']`);
                    if (rad) {
                        rad.checked = true;
                        rad.dispatchEvent(new Event('change', { bubbles: true }));
                        rad.dispatchEvent(new Event('click', { bubbles: true }));
                    }
                };
                setRadio('gxt.RadioGroup.2', 'false'); // Spoedreparatie Nee
                setRadio('gxt.RadioGroup.3', 'true');  // Weergevoelig Ja
                setRadio('gxt.RadioGroup.4', 'false'); // Reserveafzetting Nee
                setRadio('gxt.RadioGroup.5', 'false'); // Snelheidslimiet Nee
                setRadio('gxt.RadioGroup.6', 'false'); // Hoogte Nee
                setRadio('gxt.RadioGroup.7', 'false'); // Lengte Nee
                setRadio('gxt.RadioGroup.8', 'false'); // Complete wegafsluiting Nee
                setRadio('gxt.RadioGroup.9', 'true');  // Doorgang hulpdiensten Ja

                // Section 4: Aannemer & Contactpersoon
                setField('trafficDesk', 'ON District Zuid');
                setField('trafficDesk-hidden', '136');
                setField('contractor', 'DHV Royal Haskoning');
                setField('contractor-hidden', '124');
                setField('submitters.id', 'van Haandel, Roel');
                setField('submitters.id-hidden', '6470');
                setField('submitters.mobilePhone', '06-58877256');
                setField('submitters.email', 'roel.van.haandel@haskoning.com');
                setField('trafficCentre', 'VC-NON');
                setField('trafficCentre-hidden', 'VC-NON');
                setField('trafficCentreContactInfo', 'VC-NON - 088-798 4333');
                setField('trafficCentreContactInfo-hidden', 'VC-NON - 088-798 4333');
            }""")

            popup_page.wait_for_timeout(3000)

            # Screenshot form before saving
            popup_page.screenshot(path=SCREENSHOT_FILE)
            log(f"   [✓] Screenshot opgeslagen in '{SCREENSHOT_FILE}'!")

            # Click Bewaren
            log("5. Knop 'Bewaren' aanklikken...")
            btn_res = popup_page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, .x-btn-text'));
                const match = btns.find(b => b.innerText && b.innerText.trim().toLowerCase() === 'bewaren');
                if (match) {
                    match.focus();
                    ['mousedown', 'mouseup', 'click'].forEach(evt => {
                        match.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    });
                    return { status: 'clicked', id: match.id };
                }
                return { status: 'not_found' };
            }""")
            log(f"   Resultaat knop actie: {btn_res}")

            popup_page.wait_for_timeout(8000)
            popup_page.screenshot(path=SCREENSHOT_FILE.replace(".png", "_after_save.png"))
            log("6. Screenshot na bewaren opgeslagen.")

            popup_page.wait_for_timeout(10000)

        browser.close()
        log("7. Klaar.")

if __name__ == "__main__":
    run()
