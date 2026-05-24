import requests
import json
import time

url = "http://127.0.0.1:5000/api/analyze"
payload = {
    "nome": "Arquidiocese Chapeco Test",
    "url_base": "https://arquidiocesechapeco.com.br/paroquias"
}
headers = {
    "Content-Type": "application/json"
}

# Wait a moment for server to initialize
print("Waiting for server to be fully ready...")
time.sleep(2)

print(f"Sending POST to {url}...")
try:
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    print("Status Code:", r.status_code)
    try:
        response_data = r.json()
        print("\nResponse Keys:", list(response_data.keys()))
        if response_data.get("success"):
            print("Success!")
            print("Config is_sitexpresso:", response_data.get("config", {}).get("is_sitexpresso"))
            print("Test Parish Name:", response_data.get("test_parish", {}).get("nome"))
            print("Test Parish Details:", json.dumps(response_data.get("test_parish"), indent=2, ensure_ascii=False))
        else:
            print("Error message:", response_data.get("message"))
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Response text:", r.text[:1000])
except Exception as e:
    print("Request failed:", e)
