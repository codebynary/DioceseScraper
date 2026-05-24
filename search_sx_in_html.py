from bs4 import BeautifulSoup
import re

with open("chapeco_raw.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')

print(f"Total script tags in raw HTML: {len(scripts)}")

for idx, script in enumerate(scripts):
    text = script.string or ''
    if not text:
        continue
    # Search for sx.check or check
    matches = list(re.finditer(r'sx\.check|check\s*=\s*function', text))
    if matches:
        print(f"Found matches in Script {idx} (length {len(text)}):")
        for m in matches:
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 500)
            print(f"  Match '{m.group()}' context:\n{text[start:end]}")
            print("-" * 50)
