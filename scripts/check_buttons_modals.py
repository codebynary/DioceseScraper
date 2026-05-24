from bs4 import BeautifulSoup
import re

with open("chapeco_ajax_html.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all modal divs
modals = soup.find_all('div', id=re.compile(r'^ctt_modal_\d+$'))
print(f"Total modals found: {len(modals)}")

# Find all buttons
buttons = soup.find_all('div', id=re.compile(r'^ctt_button_\d+$'))
print(f"Total buttons found: {len(buttons)}")

# Print a few modals to see what is inside them
for idx, modal in enumerate(modals[:5]):
    print(f"\n--- Modal {idx} (ID: {modal.get('id')}) ---")
    modal_title = modal.find(class_='modal-title')
    title_text = modal_title.text.strip() if modal_title else "No Title"
    print("Title:", title_text)
    
    # Check if there are texts like 'Telefone', 'Email', 'Endereço', 'Pároco'
    text_content = modal.text
    print("Has Telefone?", "telefone" in text_content.lower())
    print("Has Endereço?", "endereço" in text_content.lower() or "endereco" in text_content.lower())
    print("Has Email?", "email" in text_content.lower())
    print("Has Pároco?", "pároco" in text_content.lower() or "paroco" in text_content.lower())
    
    # Print the modal-body structure
    body = modal.find(class_='modal-body')
    if body:
        body_text = body.text.strip()
        # Truncate and clean up whitespace
        body_text_clean = " ".join(body_text.split())
        print("Body text snippet (first 300 chars):", body_text_clean[:300])
        # Print sub-elements
        print("Body sub-tags:", [t.name for t in body.find_all(recursive=False)])
    else:
        print("No modal-body found.")
    print("="*60)
