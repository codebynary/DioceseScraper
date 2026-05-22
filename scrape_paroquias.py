import requests
from bs4 import BeautifulSoup
import json
import time
import sys

# Diocese de Jales - Parish Web Scraper
# This script extracts all parish details and saves them to paroquias.json

BASE_URL = "https://diocesedejales.org.br/paroquias/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_page_with_retry(url, retries=3, delay=2):
    """Fetches a URL with a retry mechanism and custom headers."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r
            elif r.status_code == 404:
                return r # Return 404 immediately, no need to retry
            print(f"  [Attempt {attempt + 1}/{retries}] Received status code {r.status_code} for {url}. Retrying...")
        except requests.RequestException as e:
            print(f"  [Attempt {attempt + 1}/{retries}] Request failed: {e}. Retrying...")
        time.sleep(delay)
    return None

def get_parish_list():
    """Paginates through list pages and returns basic info of all parishes found."""
    page = 1
    parishes = []
    seen_urls = set()
    print("=== Phase 1: Collecting Parish URLs ===")
    
    while True:
        url = f"{BASE_URL}page/{page}/" if page > 1 else BASE_URL
        print(f"Fetching listing page {page}...")
        
        response = fetch_page_with_retry(url)
        if not response:
            print(f"Failed to fetch page {page}. Stopping listing phase.")
            break
            
        if response.status_code == 404:
            print(f"Page {page} returned 404. End of list reached.")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article', class_='elementor-post')
        
        if not articles:
            print(f"No parish articles found on page {page}. Stopping.")
            break
            
        print(f"Found {len(articles)} parishes on page {page}.")
        
        has_new_parish = False
        for art in articles:
            title_tag = art.find('h3', class_='elementor-post__title')
            if title_tag and title_tag.find('a'):
                a_tag = title_tag.find('a')
                name = a_tag.text.strip()
                href = a_tag['href']
            else:
                continue
                
            # If we see a URL we have already collected, it means the website is repeating 
            # the list (common in WordPress when pagination is not active but pages still load).
            if href in seen_urls:
                continue
                
            seen_urls.add(href)
            has_new_parish = True
            
            img_tag = art.find('img')
            img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
            
            parishes.append({
                'nome': name,
                'url': href,
                'imagem_thumbnail': img_url
            })
            
        # If a page contains absolutely no new parishes, we stop listing.
        if not has_new_parish:
            print("No new parishes found on this page (reached duplicate list). Stopping listing phase.")
            break
            
        page += 1
        time.sleep(0.5) # Polite delay
        
    print(f"Completed Phase 1. Total unique parishes found: {len(parishes)}\n")
    return parishes

def scrape_parish_details(parish_list):
    """Visits each parish URL and extracts contact details, clergy, and mass times."""
    total = len(parish_list)
    print("=== Phase 2: Scraping Parish Details ===")
    
    labels = {
        'Setor:': 'setor',
        'Telefone:': 'telefone',
        'E-mail:': 'email',
        'Fucionamentos na Secretaria': 'funcionamento_secretaria',
        'Funcionamento na Secretaria': 'funcionamento_secretaria',
        'Endereço': 'endereco',
        'Clero': 'clero'
    }
    
    for idx, p in enumerate(parish_list, 1):
        print(f"[{idx}/{total}] Scraping details for: {p['nome']}")
        
        # Initialize default values
        p['setor'] = None
        p['telefone'] = None
        p['email'] = None
        p['funcionamento_secretaria'] = None
        p['endereco'] = None
        p['clero'] = None
        p['redes_sociais'] = {}
        p['horarios_missa_texto'] = None
        
        response = fetch_page_with_retry(p['url'])
        if not response or response.status_code != 200:
            print(f"  Warning: Could not fetch details for {p['nome']}. Skipping detail fields.")
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Heading lists to extract label-value pairs
        all_headings = soup.find_all(class_='elementor-heading-title')
        headings_list = []
        for h in all_headings:
            text = h.text.strip()
            if not text:
                continue
            if any(x in text for x in ['Vaticano', 'CNBB', 'MITRA DIOCESANA', 'LINKS ÚTEIS', 'ASSINE NOSSA NEWSLETTER', 'Fique por dentro']):
                continue
            headings_list.append(text)
            
        # Parse fields based on known label sequence
        for h_idx, heading in enumerate(headings_list):
            for label_key, field_name in labels.items():
                if heading.lower() == label_key.lower():
                    # The value is expected to be the next heading element in DOM
                    if h_idx + 1 < len(headings_list):
                        next_heading = headings_list[h_idx + 1]
                        # Verify the next element is not another label or separator
                        is_label = False
                        for l_k in labels.keys():
                            if next_heading.lower() == l_k.lower() or next_heading.lower() in ['informações', 'media social', 'horários de missas', 'leia mais']:
                                is_label = True
                                break
                        if not is_label:
                            p[field_name] = next_heading
                            
        # 2. Extract Mass Times Text
        post_content = soup.find(class_='elementor-widget-theme-post-content')
        if post_content:
            p['horarios_missa_texto'] = post_content.text.strip()
            
        # 3. Extract Parish Social Media Links
        info_header = soup.find(lambda tag: tag.name == 'h2' and 'INFORMAÇÕES' in tag.text.upper())
        if info_header:
            container = info_header.parent
            for _ in range(4): # Ascend up to 4 parents to get the column/section wrap
                if container and container.parent:
                    container = container.parent
            if container:
                social_widget = container.find(class_='elementor-widget-social-icons')
                if social_widget:
                    for a in social_widget.find_all('a', href=True):
                        href = a['href']
                        # Exclude general diocese links
                        if href and 'diocesedejales' not in href:
                            classes = a.get('class', [])
                            network = 'link'
                            for c in classes:
                                if 'facebook' in c:
                                    network = 'facebook'
                                elif 'instagram' in c:
                                    network = 'instagram'
                                elif 'youtube' in c:
                                    network = 'youtube'
                                elif 'whatsapp' in c:
                                    network = 'whatsapp'
                            p['redes_sociais'][network] = href
                            
        time.sleep(0.5) # Polite delay between requests
        
    print(f"Completed Phase 2. Details scraped for all parishes.")

def main():
    start_time = time.time()
    parish_list = get_parish_list()
    
    if not parish_list:
        print("No parishes found! Exiting.")
        sys.exit(1)
        
    scrape_parish_details(parish_list)
    
    # Save output to paroquias.json
    output_file = 'paroquias.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parish_list, f, indent=2, ensure_ascii=False)
        print(f"\nSUCCESS: Data written to {output_file}")
    except IOError as e:
        print(f"\nERROR: Could not write to {output_file}: {e}")
        sys.exit(1)
        
    elapsed = time.time() - start_time
    print(f"Total time elapsed: {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
