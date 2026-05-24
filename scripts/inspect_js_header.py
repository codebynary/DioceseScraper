import requests

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15)
data = r.json()
js_content = data.get('js', '')

print("Beginning of JS content (first 2000 chars):")
print(js_content[:2000])

print("\n" + "="*80 + "\n")
print("End of JS content (last 1000 chars):")
print(js_content[-1000:])
