import re
from bs4 import BeautifulSoup

with open("chapeco_raw.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
script_4_text = scripts[4].string or ''

# Search for ajax calls and show lines containing them
for line in script_4_text.split(';'):
    if 'ajax' in line or 'get' in line or 'post' in line:
        # Print lines that aren't too long or truncate them
        if len(line) < 300:
            print("Line:", line.strip())
        else:
            print("Line (truncated):", line.strip()[:300] + "...")
