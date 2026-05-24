with open("chapeco_raw.html", "r", encoding="utf-8") as f:
    html = f.read()

print("HTML Length:", len(html))

# Search for parish names or links
import re
print("\n--- Occurrences of 'paroq' or 'paróq' ---")
matches = [m.start() for m in re.finditer(r'paro[qó]?', html, re.IGNORECASE)]
print(f"Total occurrences found: {len(matches)}")
for idx in matches[:10]:
    start = max(0, idx - 100)
    end = min(len(html), idx + 100)
    print(f"Context at {idx}:\n{html[start:end]}\n{'-'*40}")

print("\n--- Script tags contents ---")
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
for i, script in enumerate(soup.find_all('script')):
    src = script.get('src')
    text = script.string or ''
    print(f"Script {i}: src={src}, content length={len(text)}")
    if not src and len(text) > 0:
        print(f"Snippet of Script {i} content (first 300 chars):")
        print(text[:300])
        print(f"{'-'*40}")
