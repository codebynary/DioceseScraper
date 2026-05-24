from bs4 import BeautifulSoup

with open("chapeco_ajax_html.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
modal = soup.find('div', id='ctt_modal_20')
print("--- Modal ctt_modal_20 HTML ---")
print(modal.prettify() if modal else "Modal not found")
