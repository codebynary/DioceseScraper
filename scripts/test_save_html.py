import requests

url = 'https://arquidiocesechapeco.com.br/paroquias'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    print(f"Fetching {url}...")
    r = requests.get(url, headers=headers, timeout=10)
    print("Status:", r.status_code)
    
    with open("chapeco_raw.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Saved to chapeco_raw.html. Length:", len(r.text))
    
    # Search for keywords
    print("Does 'paroquia' exist in text?", "paroquia" in r.text.lower())
    print("Number of occurrences of 'santo':", r.text.lower().count("santo"))
    print("Number of occurrences of 'paróquia':", r.text.lower().count("paróquia"))
    print("Number of occurrences of 'href=':", r.text.lower().count("href="))
except Exception as e:
    print("Error:", e)
