import re

with open(r"c:\Users\908071\OneDrive - Haskoning\Desktop\Test\HA\spin-aanvrager\form_window.html", "r", encoding="utf-8") as f:
    html = f.read()

print("HTML Total Size:", len(html))

# Search for x-window
windows = re.findall(r'<div[^>]*class="[^"]*x-window[^"]*"[^>]*>.*?</div>', html, re.DOTALL)
print("Found x-window matches:", len(windows))

# Extract all buttons
buttons = re.findall(r'<button[^>]*>.*?</button>', html, re.IGNORECASE)
print("\nAll <button> elements in page:")
for b in buttons:
    print("  ", b)

# Extract all input fields with their names and IDs
inputs = re.findall(r'<input[^>]*>', html, re.IGNORECASE)
print(f"\nAll <input> elements in page ({len(inputs)} total):")
for inp in inputs:
    if "name=" in inp or "id=" in inp or "type=" in inp:
        print("  ", inp[:140])
