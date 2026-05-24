from bs4 import BeautifulSoup
import re

with open("chapeco_ajax_html.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Search for "catedral"
catedral_elements = soup.find_all(string=re.compile(r'catedral', re.IGNORECASE))
print(f"Found {len(catedral_elements)} elements containing 'catedral'")

for idx, el in enumerate(catedral_elements):
    print(f"\n--- Element {idx} ---")
    print("String content:", el.strip())
    # Traverse up
    parent = el.parent
    print("Parent tag name:", parent.name, "attributes:", parent.attrs)
    
    # Go 3 levels up
    curr = parent
    for _ in range(4):
        if curr.parent:
            curr = curr.parent
        else:
            break
    print("Ancestor tag structure (prettified limit):")
    # Truncate output to avoid massive screen dump
    outer = str(curr)
    if len(outer) > 1500:
        outer = outer[:1500] + "\n...[TRUNCATED]..."
    print(outer)
    print("="*60)
