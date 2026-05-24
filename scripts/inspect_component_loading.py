import requests
import re

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15)
data = r.json()
js_content = data.get('js', '')

print("JS Length:", len(js_content))

# Search for componentLoadNow or related loading functions
matches = list(re.finditer(r'componentLoad|loadComponent|\.component|component\s*=', js_content, re.IGNORECASE))
print(f"Total matches for component loading keywords: {len(matches)}")

for m in matches[:10]:
    start = max(0, m.start() - 150)
    end = min(len(js_content), m.end() + 200)
    print(f"Snippet at {m.start()}:\n{js_content[start:end]}\n{'-'*40}")
