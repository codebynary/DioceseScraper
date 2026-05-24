import re
from bs4 import BeautifulSoup

with open("chapeco_ajax_html.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's search for "modal" in HTML content
print("Occurrences of 'modal' in HTML content:", len(re.findall(r'modal', html, re.IGNORECASE)))

soup = BeautifulSoup(html, 'html.parser')
# Find elements with class modal or modal-related attributes
modal_elements = soup.find_all(class_=re.compile(r'modal', re.IGNORECASE))
print(f"Total modal class elements in HTML: {len(modal_elements)}")
for idx, el in enumerate(modal_elements):
    print(f"Modal {idx}: tag={el.name}, id={el.get('id')}, class={el.get('class')}")

# Let's inspect the JS content for click events on the figure/images
with open("search_js.py", "r") as f:
    # We will reuse the JS read pattern but looking for specific click handlers
    import requests
    url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    r = requests.get(url, headers=headers, timeout=15)
    data = r.json()
    js_content = data.get('js', '')

print("\nOccurrences of 'click' in JS content:", len(re.findall(r'\.click|\.on\([\'"]click', js_content)))

# Let's search for any '.ctt-image' click handlers
matches = list(re.finditer(r'ctt-image|figure', js_content, re.IGNORECASE))
print(f"Occurrences of 'ctt-image' or 'figure' in JS: {len(matches)}")
for m in matches[:10]:
    start = max(0, m.start() - 100)
    end = min(len(js_content), m.end() + 100)
    print(f"Snippet near ctt-image/figure:\n{js_content[start:end]}\n{'-'*40}")
