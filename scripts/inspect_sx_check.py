import requests
import re

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15)
data = r.json()
js_content = data.get('js', '')

# Find all occurrences of sx.something = function
matches = re.finditer(r'sx\.[a-zA-Z0-9_.]+\s*=\s*function', js_content)
for m in matches:
    print(f"Match: {m.group()} at index {m.start()}")
    # print a small snippet
    print(js_content[m.start():m.start()+200])
    print("-"*40)
