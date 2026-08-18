import os
import sys
import time
from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("SPIN_USER", "HaandelR")
PASSWORD = os.environ.get("SPIN_PASS", "#RvHl1981xibspin")
BASE_URL = "https://spin.rijkswaterstaat.nl/spin/"
DUMP_FILE = r"c:\Users\908071\OneDrive - Haskoning\Desktop\Test\HA\spin-aanvrager\form_window.html"

def log(msg):
    safe_msg = str(msg).encode("ascii", "replace").decode("ascii")
    print(safe_msg, flush=True)

def run():
    log("=========================================================================")
    log("===   DUMPING FORM WINDOW HTML (HEADFUL VISIBLE BROWSER MODE)          ===")
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
        log("3. Formulier Vluchtstrook/berm openen via toetsenbordnavigatie...")
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

        page.keyboard.press("Enter")
        page.wait_for_timeout(6000)

        # Check pages & windows
        wins = page.query_selector_all(".x-window")
        log(f"4. Aantal geopende .x-window vensters op hoofdpagina: {len(wins)}")

        target_win = None
        for w in wins:
            if w.is_visible():
                target_win = w
                break

        if target_win:
            html = target_win.evaluate("el => el.outerHTML")
            with open(DUMP_FILE, "w", encoding="utf-8") as f:
                f.write(html)
            log(f"   [🎉] SUCCES! OuterHTML opgeslagen in '{DUMP_FILE}'!")

            # Field details
            fields = target_win.evaluate("""el => {
                const results = [];
                const inputs = el.querySelectorAll('input, select, textarea, button, .x-btn');
                inputs.forEach(inp => {
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

            log(f"5. Aantal gevulde velden: {len(fields)}")
            for idx, f in enumerate(fields):
                log(f"   Field {idx:02d}: label='{f['label']}', name='{f['name']}', id='{f['id']}', tag='{f['tag']}'")

        else:
            log("[!] Geen zichtbaar .x-window op hoofdpagina. Heel de body HTML dumpen...")
            with open(DUMP_FILE, "w", encoding="utf-8") as f:
                f.write(page.content())
            log(f"   [✓] Hele body HTML opgeslagen in '{DUMP_FILE}'.")

        browser.close()

if __name__ == "__main__":
    run()
