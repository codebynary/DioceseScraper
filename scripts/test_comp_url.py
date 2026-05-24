import requests
from bs4 import BeautifulSoup

comp_val = "Y3R0OjEsZ3JvdXA6MSxncm91cDoxLHBhZ2U6L3Bhcm9xdWlhcyxncDpjb250ZW50cy5wYXJvcXVpYXMuZ3JvdXAuMi5ncm91cC4xLmdyb3VwLjI="
url = f"https://arquidiocesechapeco.com.br/?ajax=get&comp={comp_val}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"Requesting component URL: {url}")
try:
    r = requests.get(url, headers=headers, timeout=15)
    print("Status Code:", r.status_code)
    print("Response Length:", len(r.text))
    
    # Check if the response is JSON or HTML
    try:
        data = r.json()
        print("Response is JSON!")
        print("Keys:", data.keys())
        if 'html' in data:
            html = data['html']
        else:
            html = str(data)
    except:
        print("Response is raw text/HTML")
        html = r.text
        
    # Parse and inspect HTML for parish details
    soup = BeautifulSoup(html, 'html.parser')
    print("\n--- Parsed Text Content ---")
    print(soup.get_text(separator=' | ', strip=True)[:1000])
    
    # Save the component html to a file to examine
    with open("chapeco_comp_example.html", "w", encoding="utf-8") as f:
        f.write(html)
        
except Exception as e:
    print("Error fetching component URL:", e)
