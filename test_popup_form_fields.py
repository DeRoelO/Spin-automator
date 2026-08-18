import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
WINDOW_OPEN_URL = "https://spin.rijkswaterstaat.nl/spin/?winId=GE_MEASURE_WINDOW_NEW&viewType=GE_MEASURE_WINDOW&phaseId=0&eventId=0&isCopy=false&isInverse=false&mode=CREATE&measureType=SHOULDER"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=== INSPECTING ALL INPUT FIELDS INSIDE THE MINIMAL POPUP WINDOW ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-popup-blocking", "--no-sandbox", "--disable-setuid-sandbox"]
        )
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

        # Open minimal popup window
        log("3. Minimaal Vluchtstrook/berm popup venster openen...")
        with context.expect_page() as popup_info:
            page.evaluate(f"window.open('{WINDOW_OPEN_URL}', 'GE_MEASURE_WINDOW_NEW', 'toolbar=no,menubar=no,width=1100,height=850,scrollbars=yes,resizable=yes');")
        
        popup = popup_info.value
        popup.wait_for_timeout(6000)

        # Dump all form input fields in the popup window
        inputs = popup.evaluate("""() => {
            const els = Array.from(document.querySelectorAll('input, select, textarea, button'));
            return els.map(el => ({
                tag: el.tagName,
                name: el.getAttribute('name') || '',
                id: el.id,
                type: el.getAttribute('type') || '',
                text: el.innerText ? el.innerText.trim() : ''
            })).filter(x => x.name || x.id || x.text);
        }""")

        log(f"4. Gevonden velden in het popup venster ({len(inputs)} totaal):")
        for inp in inputs[:15]:
            log(f"   Field: {inp}")

        browser.close()

if __name__ == "__main__":
    run()
