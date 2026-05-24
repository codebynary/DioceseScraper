import requests
from bs4 import BeautifulSoup
import re
import time

with open("chapeco_ajax_html.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all divs with component attribute
comp_divs = soup.find_all(lambda tag: tag.has_attr('component'))
print(f"Found {len(comp_divs)} divs with 'component' attribute.")

components = []
for div in comp_divs:
    val = div['component']
    # Filter component values that seem to correspond to parish details
    # E.g. we saw: Y3R0OjEsZ3JvdXA6MSxncm91cDoxLHBhZ2U6L3Bhcm9xdWlhcyxncDpjb250ZW50cy5wYXJvcXVpYXMuZ3JvdXAuMi5ncm91cC4xLmdyb3VwLjI=
    # which decodes to contents.paroquias.group.2.group.1.group.2
    # Let's decode to make sure it contains 'paroquias' and is a detail group
    import base64
    try:
        decoded = base64.b64decode(val).decode('utf-8', errors='ignore')
        if 'paroquias' in decoded:
            components.append((val, decoded))
    except:
        pass

print(f"Filtered {len(components)} parish detail components.")

# Let's fetch the first 5 and print their name
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for idx, (comp, decoded) in enumerate(components[:5]):
    url = f"https://arquidiocesechapeco.com.br/?ajax=get&comp={comp}"
    print(f"\n--- Parish {idx+1} ---")
    print(f"Decoded Component: {decoded}")
    print(f"Fetching: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            parish_html = data.get('html', '')
            # Find name
            p_soup = BeautifulSoup(parish_html, 'html.parser')
            # The title of the parish seems to be in a header or strong tag, let's find the text
            # E.g. print the first few lines of text
            lines = [l.strip() for l in p_soup.get_text().split('\n') if l.strip()]
            if lines:
                print("Name/Title found in component:", lines[0])
                print("Location info:", lines[1] if len(lines) > 1 else "")
            else:
                print("No text found in component HTML.")
        else:
            print(f"Failed with status: {r.status_code}")
    except Exception as e:
        print("Error:", e)
    time.sleep(0.5)
