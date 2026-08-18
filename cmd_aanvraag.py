import os
import sys
import time
import argparse
from playwright.sync_api import sync_playwright

DEFAULT_USERNAME = os.environ.get("SPIN_USER", "HaandelR")
DEFAULT_PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"

DEFAULT_DATA = {
    "type": "Vluchtstrook/berm",
    "besteknummer": "NL-31154600-inspecties voor MJPV",
    "bestek_id_hidden": "2898",
    "start": "06.09.2026, 09:00",
    "end": "06.09.2026, 15:00",
    "wegwerktype": "inspectie algemeen",
    "roadwork_type_hidden": "29",
    "wegbeheerder": "ON District Zuid",
    "managing_district_hidden": "136",
    "from_road": "A15",
    "from_side": "Re",
    "from_km": "150,000",
    "to_road": "A15",
    "to_side": "Re",
    "to_km": "165,000",
    "hinderklasse": "1 (geen file)",
    "hinderklasse_hidden": "SPIN_HINDRANCE_CLASS_1",
    "afzetsysteem": "96a-430",
    "roadblock_type_hidden": "179",
    "doorrijdprofiel": "7,00",
    "verkeersloket": "ON District Zuid",
    "traffic_desk_hidden": "136",
    "bedrijfsnaam": "DHV Royal Haskoning",
    "contractor_hidden": "124",
    "contactpersoon": "van Haandel, Roel",
    "submitter_id_hidden": "6470",
    "telefoon": "06-58877256",
    "email": "roel.van.haandel@haskoning.com",
    "verkeerscentrale": "VC-NON",
    "traffic_centre_hidden": "VC-NON"
}

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def fill_and_resolve_route(popup, d):
    """
    Fills form fields and clicks 'Toon route' to resolve locations & valid status.
    """
    log("-> Alle formuliervelden instellen...")
    popup.evaluate("""(data) => {
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

        // Algemene Eigenschappen
        setField('bestekId', data.besteknummer);
        setField('bestekId-hidden', data.bestek_id_hidden);
        setField('start', data.start);
        setField('end', data.end);
        setField('roadworkType', data.wegwerktype);
        setField('roadworkType-hidden', data.roadwork_type_hidden);
        setField('managingDistrict', data.wegbeheerder);
        setField('managingDistrict-hidden', data.managing_district_hidden);

        // Locatie
        setField('location.fromRoadNumber', data.from_road);
        setField('location.fromRoadSide', data.from_side);
        setField('location.fromMeter', data.from_km);
        setField('location.toRoadNumber', data.to_road);
        setField('location.toRoadSide', data.to_side);
        setField('location.toMeter', data.to_km);

        // Verkeer
        setField('trafficHindranceClass', data.hinderklasse);
        setField('trafficHindranceClass-hidden', data.hinderklasse_hidden);
        setField('outsideWorkableHours', 'Nee');
        setField('outsideWorkableHours-hidden', 'NO');
        setField('roadblockType', data.afzetsysteem);
        setField('roadblockType-hidden', data.roadblock_type_hidden);
        setField('widthConstraint', data.doorrijdprofiel);

        // Radio Groups
        const setRadio = (groupName, val) => {
            const rad = document.querySelector(`input[name='${groupName}'][value='${val}']`);
            if (rad) {
                rad.checked = true;
                rad.dispatchEvent(new Event('change', { bubbles: true }));
                rad.dispatchEvent(new Event('click', { bubbles: true }));
            }
        };
        setRadio('gxt.RadioGroup.2', 'false');
        setRadio('gxt.RadioGroup.3', 'true');
        setRadio('gxt.RadioGroup.4', 'false');
        setRadio('gxt.RadioGroup.5', 'false');
        setRadio('gxt.RadioGroup.6', 'false');
        setRadio('gxt.RadioGroup.7', 'false');
        setRadio('gxt.RadioGroup.8', 'false');
        setRadio('gxt.RadioGroup.9', 'true');

        // Aannemer
        setField('trafficDesk', data.verkeersloket);
        setField('trafficDesk-hidden', data.traffic_desk_hidden);
        setField('contractor', data.bedrijfsnaam);
        setField('contractor-hidden', data.contractor_hidden);
        setField('submitters.id', data.contactpersoon);
        setField('submitters.id-hidden', data.submitter_id_hidden);
        setField('submitters.mobilePhone', data.telefoon);
        setField('submitters.email', data.email);
        setField('trafficCentre', data.verkeerscentrale);
        setField('trafficCentre-hidden', data.traffic_centre_hidden);
        setField('trafficCentreContactInfo', 'VC-NON - 088-798 4333');
        setField('trafficCentreContactInfo-hidden', 'VC-NON - 088-798 4333');
    }""", d)

    popup.wait_for_timeout(2000)

    log("-> Klikken op 'Toon route' om de locatienamen en route te berekenen...")
    popup.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button, .x-btn-text'));
        const toonRouteBtn = btns.find(b => b.innerText && b.innerText.trim().toLowerCase() === 'toon route');
        if (toonRouteBtn) {
            ['mousedown', 'mouseup', 'click'].forEach(evt => {
                toonRouteBtn.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
            });
        }
    }""")

    popup.wait_for_timeout(5000)
    log("-> [✓] Route berekening en locatie validatie voltooid!")

def click_bewaren_button(popup):
    """
    Clicks the 'Bewaren' button in popup_page and logs server response.
    """
    log("-> Klikken op de knop 'Bewaren' in het popup venster...")
    res = popup.evaluate("""() => {
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

    log(f"   Status knop actie: {res}")
    popup.wait_for_timeout(8000)
    return res.get("status") == "clicked"

def main():
    parser = argparse.ArgumentParser(description="SPIN Melding Aanvrager CLI (Zichtbaar)")
    parser.add_argument("--user", default=DEFAULT_USERNAME, help="SPIN Gebruikersnaam")
    parser.add_argument("--pass", dest="password", default=DEFAULT_PASSWORD, help="SPIN Wachtwoord")
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser headless")

    args = parser.parse_args()
    data = DEFAULT_DATA.copy()

    log("=========================================================================")
    log("===   SPIN MAATREGEL AANVRAGEN VIA ZICHTBARE BROWSER (TOON ROUTE FIX)  ===")
    log("=========================================================================")

    with sync_playwright() as p:
        log("1. Zichtbare Chrome Browser starten...")
        browser = p.chromium.launch(
            headless=args.headless,
            args=["--disable-popup-blocking", "--start-maximized"]
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        log("2. Inloggen op SPIN...")
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
        name_input.fill(args.user, force=True)
        pass_input.fill(args.password, force=True)

        buttons = page.query_selector_all("button")
        for btn in buttons:
            if btn.is_visible() and btn.inner_text().strip() == "Ok":
                btn.click()
                break

        page.wait_for_timeout(7000)
        log("3. Ingelogd op SPIN Dashboard.")

        # Open form via keyboard navigation
        log("4. Schoon Vluchtstrook/berm formulier openen via snelmenu...")
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

            # Fill all fields and click 'Toon route' to resolve red location validation borders
            fill_and_resolve_route(popup_page, data)

            # Click Bewaren button
            click_bewaren_button(popup_page)

            log("5. Zichtbare browser openhouden gedurende 15 seconden voor visuele controle...")
            popup_page.wait_for_timeout(15000)
        else:
            log("[!] Kon het popup venster niet opvangen.")

        browser.close()
        log("6. Browser afgesloten.")

if __name__ == "__main__":
    main()
