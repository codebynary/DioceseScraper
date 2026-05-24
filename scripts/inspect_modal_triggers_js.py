import requests
import re

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15)
data = r.json()
js_content = data.get('js', '')

# Search for the block containing ctt_modal_20 or ctt_button_20
# Let's search for ctt_modal_20
matches = list(re.finditer(r'ctt_modal_20', js_content))
print(f"ctt_modal_20 matches: {len(matches)}")
for m in matches:
    start = max(0, m.start() - 200)
    end = min(len(js_content), m.end() + 1000) # Print a larger block
    print(f"Block at {m.start()}:\n{js_content[start:end]}\n{'='*80}")
