import requests
import json
import re

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15)
data = r.json()
js_content = data.get('js', '')

print("JS content length:", len(js_content))

# Look for parish names
target_keywords = ["Catedral", "Santo Ant", "Santo Antônio", "Santo Antonio", "São José", "Sao Jose"]
for kw in target_keywords:
    # Use re with ignorecase and support encoded characters or fragments
    matches = list(re.finditer(re.escape(kw), js_content, re.IGNORECASE))
    print(f"Keyword '{kw}' matches count in JS content: {len(matches)}")
    for m in matches[:3]:
        start = max(0, m.start() - 150)
        end = min(len(js_content), m.end() + 150)
        print(f"  Snippet at {m.start()}:\n{js_content[start:end]}\n{'-'*40}")
