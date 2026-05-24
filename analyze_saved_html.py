from bs4 import BeautifulSoup
import re

with open("chapeco_raw.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=== BeautifulSoup Parsing Stats ===")
print("Title:", soup.title)
print("Total anchors (a):", len(soup.find_all('a')))
print("Total divs:", len(soup.find_all('div')))
print("Total scripts:", len(soup.find_all('script')))

print("\n=== Checking all 'a' tags ===")
for i, a in enumerate(soup.find_all('a')[:20]):
    print(f"Anchor {i}: href={a.get('href')} text='{a.text.strip()}'")

# Search for any references to paroquia details in the HTML text
print("\n=== Searching for URL/text patterns in raw HTML ===")
# Find all strings matching something like a URL or folder structure
urls = re.findall(r'href=[\'"]([^\'"]+)', html)
print(f"Total hrefs in raw HTML regex: {len(urls)}")
for u in urls[:25]:
    print("  Regex href:", u)
