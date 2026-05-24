import requests
from bs4 import BeautifulSoup

url = 'https://arquidiocesechapeco.com.br/paroquias'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}

try:
    print(f"Fetching {url}...")
    r = requests.get(url, headers=headers, timeout=10)
    print("Status:", r.status_code)
    print("Response Headers:", r.headers)
    print("\nBody snippet:")
    print(r.text[:2000])
except Exception as e:
    print("Error:", e)
