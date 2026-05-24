from bs4 import BeautifulSoup
import re

with open("chapeco_raw.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')

# We want to inspect Script 4 (index 4)
script_4_text = scripts[4].string or ''

print("Script 4 length:", len(script_4_text))

# Search for patterns like url, fetch, ajax, post, get, base64, etc.
keywords = ['url', 'ajax', 'fetch', 'get', 'post', 'http', 'api', 'json', 'data', 'NTEwMg']
for kw in keywords:
    matches = list(re.finditer(re.escape(kw), script_4_text, re.IGNORECASE))
    print(f"Keyword '{kw}' matches count: {len(matches)}")

# Let's write the script content to a file to examine it or look for URLs in it
urls = re.findall(r'https?://[^\s\'"()]+', script_4_text)
print("URLs in script 4:", urls[:10])

# Let's inspect functions/variables in script 4
# Let's search for any strings or URLs in script 4:
strings = re.findall(r'["\']([^"\']{4,100})["\']', script_4_text)
print("Sample strings in script 4:")
for s in strings[:30]:
    if '/' in s or 'http' in s or '.' in s or '=' in s:
        print("  String:", s)
