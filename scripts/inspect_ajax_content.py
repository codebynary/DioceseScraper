import requests
import json

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15)
data = r.json()

html_content = data.get('html', '')
js_content = data.get('js', '')

print("HTML Content Length:", len(html_content))
print("JS Content Length:", len(js_content))

# Save the html content to a file to look at it
with open("chapeco_ajax_html.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Search for some keywords in the HTML content
import re
keywords = ["paroquia", "paróquia", "catedral", "são", "santo", "santo antônio", "href", "click", "div"]
for kw in keywords:
    matches = list(re.finditer(re.escape(kw), html_content, re.IGNORECASE))
    print(f"Keyword '{kw}' matches count in HTML content: {len(matches)}")

# Search for hrefs
hrefs = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html_content)
print("Hrefs found by regex in HTML:", len(hrefs))
for h in hrefs[:15]:
    print("  ", h)

# Check if there are any standard HTML tags
from bs4 import BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')
print("Soup Title:", soup.title)
print("Soup total elements:", len(soup.find_all()))
# Let's count some elements
for tag in ['div', 'span', 'p', 'a', 'img', 'li', 'ul']:
    print(f"  Tag '{tag}': {len(soup.find_all(tag))}")

# Check first 500 characters of html_content
print("\nHTML snippet (first 1000 chars):")
print(html_content[:1000])
