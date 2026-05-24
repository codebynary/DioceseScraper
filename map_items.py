from bs4 import BeautifulSoup
import re

with open("chapeco_ajax_html.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Let's search for "ctt_modal_20" and its surroundings, or elements related to it
modal_id = "ctt_modal_20"
modal = soup.find('div', id=modal_id)

print("=== Sibling / Parent of Modal ctt_modal_20 ===")
if modal:
    print("Modal tag:", modal.name)
    parent = modal.parent
    print("Parent tag name:", parent.name, "attrs:", parent.attrs)
    # Find all siblings or check if the button ctt_button_20 is in the same parent
    button = parent.find(id="ctt_button_20")
    if button:
        print("Found ctt_button_20 in same parent! Button attrs:", button.attrs)
        print("Button text:", button.text.strip())
        print("Button HTML snippet:", str(button)[:500])
    else:
        print("ctt_button_20 NOT found in same parent.")
        # Find where ctt_button_20 is
        btn = soup.find(id="ctt_button_20")
        if btn:
            print("Found ctt_button_20 elsewhere. Parent of button:", btn.parent.name, btn.parent.attrs)
            print("Button html:", str(btn)[:500])
else:
    print("Modal not found")
