import requests
import re

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15)
data = r.json()
js_content = data.get('js', '')

# Search for componentLoadNow
m = re.search(r'componentLoadNow\s*=\s*function', js_content)
if m:
    print("Found definition at index:", m.start())
    start = max(0, m.start() - 100)
    end = min(len(js_content), m.start() + 1500)
    print(js_content[start:end])
else:
    print("componentLoadNow definition not found")
    # Search for sx.check
    m2 = re.search(r'check\s*=\s*function', js_content)
    if m2:
        print("Found sx.check definition at index:", m2.start())
        print(js_content[m2.start()-100 : m2.start()+1500])
