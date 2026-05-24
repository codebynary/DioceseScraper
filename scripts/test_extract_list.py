from bs4 import BeautifulSoup

with open("chapeco_ajax_html.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

items = soup.select('div.ctt-group-button')
print(f"Total ctt-group-button items: {len(items)}")

for idx, item in enumerate(items[:10]):
    print(f"\n--- Item {idx+1} ---")
    # Button text (clean it up by removing extra whitespace/newlines)
    btn = item.select_one('div.btn.btn-modal-images')
    # Find figcaption or take button text
    caption = btn.find('figcaption') if btn else None
    name = caption.text.strip() if caption else (btn.text.strip() if btn else "Unknown")
    name = " ".join(name.split())
    
    # Image
    img = item.find('img')
    img_src = img.get('src') if img else None
    
    # Component inside modal
    comp_div = item.select_one('div[component]')
    comp_val = comp_div['component'] if comp_div else None
    
    print("Name:", name)
    print("Image Src:", img_src)
    print("Component:", comp_val)
