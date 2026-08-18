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
    log("===   POPUP VENSTER AFHANDELING TEST (DISABLE-POPUP-BLOCKING)          ===")
    log("=========================================================================")
    with sync_playwright() as p:
        # Launch chromium with popup blocking explicitly disabled
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-popup-blocking", "--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 1000})

        # Track all opened popup pages
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

        # Clear popup pages list
        popup_pages.clear()

        # STAP 1: Klik Bestand
        log("3. STAP 1: Klikken op 'Bestand'...")
        page.locator("div.x-menubar-item", has_text="Bestand").first.click()
        page.wait_for_timeout(1000)

        # STAP 2: Klik Nieuwe maatregel
        log("4. STAP 2: Klikken op 'Nieuwe maatregel'...")
        nieuw_item = page.locator(".x-menu-item", has_text="Nieuwe maatregel").first
        nieuw_item.hover()
        page.wait_for_timeout(500)
        nieuw_item.click(force=True)
        page.wait_for_timeout(1500)

        # STAP 3: Klik Vluchtstrook/berm
        log("5. STAP 3: Klikken op 'Vluchtstrook/berm'...")
        page.evaluate("""() => {
            const els = Array.from(document.querySelectorAll('a, div.x-menu-list-item, .x-menu-item'));
            const match = els.find(el => el.innerText && el.innerText.trim() === 'Vluchtstrook/berm');
            if (match) {
                match.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
                match.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
                match.click();
            }
        }""")
        page.wait_for_timeout(6000)

        # Check for popup pages in context
        log(f"6. Totaal aantal geopende pagina's in browser context: {len(context.pages)}")
        for idx, p_obj in enumerate(context.pages):
            log(f"   Pagina {idx}: URL = '{p_obj.url}', Titel = '{p_obj.title()}'")
            if p_idx := idx > 0:
                log(f"   [🎉🎉🎉] POPUP VENSTER DETECTED! PAGINA {p_idx} IS POPUP VENSTER!")

        # Check for modal window in main page
        wins = page.query_selector_all(".x-window")
        log(f"7. Aantal geopende modal vensters op hoofd-pagina: {len(wins)}")
        for idx, w in enumerate(wins):
            if w.is_visible():
                title = ""
                try:
                    title = w.query_selector(".x-window-header-text").inner_text().strip()
                except:
                    pass
                log(f"   [🎉🎉🎉] MODAL VENSTER GEOPEND! Titel: '{title}'")

        browser.close()

if __name__ == "__main__":
    run()
