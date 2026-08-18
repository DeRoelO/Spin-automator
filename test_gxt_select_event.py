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
    log("===   FIRE GXT 'select' EVENT ON VLUCHTSTROOK/BERM MENU ITEM           ===")
    log("=========================================================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-popup-blocking", "--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 1000})

        # Track popup pages
        popup_pages = []
        context.on("page", lambda p_obj: popup_pages.append(p_obj))

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

        # Open Bestand menu
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # Hover Nieuwe maatregel
        page.locator(".x-menu-item", has_text="Nieuwe maatregel").first.hover()
        page.wait_for_timeout(1500)

        # Execute GXT 'select' event on Vluchtstrook/berm component
        log("3. Ext.getCmp / ComponentMgr fireEvent('select') afvuren op 'Vluchtstrook/berm'...")
        res = page.evaluate("""() => {
            if (!window.Ext || !window.Ext.ComponentMgr) return { status: 'no_ext' };
            const comps = window.Ext.ComponentMgr.all.array || [];
            const match = comps.find(c => c.text && c.text.trim() === 'Vluchtstrook/berm');
            if (match) {
                try {
                    if (match.fireEvent) {
                        match.fireEvent('select');
                        match.fireEvent('click');
                    }
                    if (match.onClick) match.onClick();
                    return { status: 'fired', id: match.id };
                } catch(e) {
                    return { status: 'error', error: e.toString() };
                }
            }
            return { status: 'not_found' };
        }""")
        log(f"   GXT event execution resultaat: {res}")
        page.wait_for_timeout(6000)

        log(f"4. Totaal aantal geopende browser pagina's: {len(context.pages)}")
        for idx, p_obj in enumerate(context.pages):
            log(f"   Pagina {idx}: URL = '{p_obj.url}', Titel = '{p_obj.title()}'")

        wins = page.query_selector_all(".x-window")
        log(f"5. Aantal modal vensters op hoofd-pagina: {len(wins)}")

        browser.close()

if __name__ == "__main__":
    run()
