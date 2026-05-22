import os
import sys
import requests
import traceback
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import config_manager
from core import agent
from core import scraper

api_key = config_manager.get_api_key()
diocese_name = "Arquidiocese Chapeco Test"
url_base = "https://arquidiocesechapeco.com.br/paroquias"

print("Gemini API Key exists:", api_key is not None)

try:
    # 1. Fetch listing HTML
    print("Fetching listing page...")
    list_resp = requests.get(url_base, headers=scraper.HEADERS, timeout=15)
    print("Listing status:", list_resp.status_code)
    
    list_html = list_resp.text
    is_sitexp = False
    if 'sitexpresso' in list_html.lower() or 'sx.check' in list_html or 'sx.start' in list_html or 'window.sxid' in list_html:
        is_sitexp = True
    print("Is SitExpresso:", is_sitexp)
    
    import urllib.parse
    parsed = urllib.parse.urlparse(url_base)
    
    if is_sitexp:
        # Construct AJAX listing URL
        ajax_url = f"{parsed.scheme}://{parsed.netloc}/?ajax=get&path={parsed.path}"
        print(f"Fetching AJAX listing from {ajax_url}...")
        ajax_resp = requests.get(ajax_url, headers=scraper.HEADERS, timeout=15)
        print("AJAX listing status:", ajax_resp.status_code)
        if ajax_resp.status_code == 200:
            ajax_data = ajax_resp.json()
            list_html = ajax_data.get('html', '')
            
    list_soup = BeautifulSoup(list_html, 'html.parser')
    detail_url = None
    
    if is_sitexp:
        comp_div = list_soup.find(lambda tag: tag.has_attr('component'))
        if comp_div:
            comp_val = comp_div['component']
            detail_url = f"{parsed.scheme}://{parsed.netloc}/?ajax=get&comp={comp_val}"
    else:
        # standard anchors lookup
        all_anchors = list_soup.find_all('a', href=True)
        for a in all_anchors:
            href = a['href']
            full_url = scraper.resolve_url(url_base, href)
            if (full_url.startswith(url_base) and 
                full_url != url_base and 
                '/page/' not in full_url and 
                '/categoria/' not in full_url and 
                '/feed/' not in full_url and
                '?' not in full_url):
                detail_url = full_url
                break
                
    print("Detail URL found:", detail_url)
    
    if not detail_url:
        print("No detail URL found!")
        sys.exit(1)
        
    # 3. Fetch detail page HTML
    print("Fetching detail page...")
    detail_resp = requests.get(detail_url, headers=scraper.HEADERS, timeout=15)
    print("Detail status:", detail_resp.status_code)
    
    detail_html = detail_resp.text
    if is_sitexp:
        detail_data = detail_resp.json()
        detail_html = detail_data.get('html', '')
        
    # 4. Run Gemini layout analysis
    print("Running Gemini layout analysis...")
    config_data = agent.analyze_diocese_layout(
        api_key, diocese_name, url_base, list_html, detail_html
    )
    print("Gemini Config Generated:", config_data is not None)
    print("Config data keys:", list(config_data.keys()) if config_data else [])
    
    # Inject is_sitexpresso
    if is_sitexp and config_data:
        config_data['is_sitexpresso'] = True
        if 'listagem' not in config_data:
            config_data['listagem'] = {}
        config_data['listagem']['item_selector'] = 'div.ctt-group-button'
        config_data['listagem']['link_selector'] = 'div[component]'
        config_data['paginacao'] = {'tipo': 'single_page', 'url_pattern': None, 'next_selector': None}
        
    # 5. Run test scrape
    print("Running test scrape...")
    test_parish = scraper.scrape_single_parish(detail_url, config_data)
    print("Test Parish Result:", test_parish)
    
except Exception as e:
    print("\n--- ERROR DETECTED ---")
    print(f"Exception message: {e}")
    traceback.print_exc()
