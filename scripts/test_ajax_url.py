import requests
from bs4 import BeautifulSoup
import json

url = "https://arquidiocesechapeco.com.br/?ajax=get&path=/paroquias"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"Fetching: {url}")
try:
    r = requests.get(url, headers=headers, timeout=15)
    print("Response Status Code:", r.status_code)
    print("Response Length:", len(r.text))
    
    # Try to parse as JSON first (since the Javascript says JSON.parse)
    try:
        data = r.json()
        print("Response is JSON!")
        print("Keys:", data.keys())
        if 'html' in data:
            print("Found 'html' key in JSON. Length of HTML content:", len(data['html']))
            # Parse HTML
            soup = BeautifulSoup(data['html'], 'html.parser')
            anchors = soup.find_all('a')
            print(f"Total anchors in parsed HTML: {len(anchors)}")
            for idx, a in enumerate(anchors[:10]):
                print(f"  Anchor {idx}: href={a.get('href')} text='{a.text.strip()}'")
    except Exception as e:
        print("Response is not JSON or parsing failed:", e)
        # Parse directly as HTML
        soup = BeautifulSoup(r.text, 'html.parser')
        anchors = soup.find_all('a')
        print(f"Total anchors in direct HTML: {len(anchors)}")
        for idx, a in enumerate(anchors[:10]):
            print(f"  Anchor {idx}: href={a.get('href')} text='{a.text.strip()}'")
            
except Exception as e:
    print("Request failed:", e)
