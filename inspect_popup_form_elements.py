import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
DUMP_POPUP_FILE = r"c:\Users\908071\OneDrive - Haskoning\Desktop\Test\HA\spin-aanvrager\popup_form.html"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   INSPECTING POPUP BROWSER WINDOW CREATED BY KEYBOARD ENTER      ===")
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

        # Navigate keyboard menu and listen for popup page
        log("3. Menubalk navigeren en luisteren naar geopende POPUP PAGINA...")
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

        # Catch spawned popup page upon Enter
        popup_page = None
        try:
            with context.expect_page(timeout=8000) as popup_info:
                page.keyboard.press("Enter")
            popup_page = popup_info.value
            log(f"   [🎉🎉🎉] EUREKA! POPUP PAGINA OPGEVANGEN! URL = '{popup_page.url}'")
        except Exception as e:
            log(f"   Exception bij opvangen popup: {e}")
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)
            if len(context.pages) > 1:
                popup_page = context.pages[-1]

        if popup_page:
            popup_page.wait_for_timeout(5000)
            html = popup_page.content()
            with open(DUMP_POPUP_FILE, "w", encoding="utf-8") as f:
                f.write(html)
            log(f"4. HTML van het geopende POPUP venster opgeslagen in '{DUMP_POPUP_FILE}' ({len(html)} bytes)!")

            # Extract fields in popup_page
            fields = popup_page.evaluate("""() => {
                const results = [];
                const els = Array.from(document.querySelectorAll('input, select, textarea, button, .x-btn, .x-form-field'));
                els.forEach(inp => {
                    let labelText = '';
                    let p = inp.parentElement;
                    for (let i = 0; i < 4 && p; i++) {
                        const lbl = p.querySelector('label, .x-form-item-label');
                        if (lbl) {
                            labelText = lbl.innerText.trim();
                            break;
                        }
                        p = p.parentElement;
                    }
                    results.push({
                        tag: inp.tagName,
                        name: inp.getAttribute('name') || '',
                        id: inp.id,
                        class: inp.className,
                        type: inp.getAttribute('type') || '',
                        value: inp.value || '',
                        text: inp.innerText ? inp.innerText.trim() : '',
                        label: labelText
                    });
                });
                return results;
            }""")

            log(f"5. Aantal formulierelementen in het POPUP venster: {len(fields)}")
            for idx, f in enumerate(fields):
                log(f"   Field {idx:02d}: label='{f['label']}', name='{f['name']}', id='{f['id']}', tag='{f['tag']}', type='{f['type']}', text='{f['text']}'")

        else:
            log("[!] Geen popup pagina in context.pages gevonden.")

        browser.close()

if __name__ == "__main__":
    run()
