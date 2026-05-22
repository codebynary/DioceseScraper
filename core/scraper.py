import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
from core import config_manager

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_page(url, retries=3, delay=1):
    """Politely fetches a URL with retries."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r
            elif r.status_code == 404:
                return r
        except requests.RequestException:
            pass
        time.sleep(delay)
    return None

def resolve_url(base_url, relative_url):
    """Joins a base URL and a relative URL securely."""
    return urllib.parse.urljoin(base_url, relative_url)

def extract_social_media(soup, social_selector):
    """Extracts social media links from the page matching social_selector."""
    social_links = {}
    if not social_selector:
        return social_links
        
    anchors = soup.select(social_selector)
    for a in anchors:
        href = a.get('href')
        if not href or 'diocesedejales' in href or href.startswith('#'):
            # Filter out general diocesan links
            continue
            
        classes = " ".join(a.get('class', []))
        network = 'link'
        
        # Identify social network by class or href
        href_lower = href.lower()
        if 'facebook' in classes or 'facebook.com' in href_lower:
            network = 'facebook'
        elif 'instagram' in classes or 'instagram.com' in href_lower:
            network = 'instagram'
        elif 'youtube' in classes or 'youtube.com' in href_lower:
            network = 'youtube'
        elif 'whatsapp' in classes or 'wa.me' in href_lower or 'api.whatsapp.com' in href_lower or 'whatsapp.com' in href_lower:
            network = 'whatsapp'
            
        social_links[network] = href
    return social_links

def scrape_single_parish(url, config):
    """Scrapes detail fields of a single parish page using config rules."""
    response = fetch_page(url)
    if not response or response.status_code != 200:
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    details_cfg = config.get("detalhes", {})
    tipo_layout = details_cfg.get("tipo_layout", "label_value")
    campos_labels = details_cfg.get("campos_labels", {})
    campos_seletores = details_cfg.get("campos_seletores", {})
    
    result = {
        'setor': None,
        'telefone': None,
        'email': None,
        'funcionamento_secretaria': None,
        'endereco': None,
        'clero': None,
        'redes_sociais': {},
        'horarios_missa_texto': None
    }
    
    # 1. Extract detail fields based on layout strategy
    if tipo_layout == "label_value":
        # Get selector for headings/labels list
        # E.g. Jales uses '.elementor-heading-title' for both label and value
        headings_selector = list(campos_seletores.values())[0] if campos_seletores else '.elementor-heading-title'
        all_headings = [h.text.strip() for h in soup.select(headings_selector) if h.text.strip()]
        
        # Filter out common header/footer items
        filtered_headings = []
        for h in all_headings:
            if any(x in h.upper() for x in ['VATICANO', 'CNBB', 'MITRA DIOCESANA', 'LINKS ÚTEIS', 'NEWSLETTER', 'FIQUE POR DENTRO']):
                continue
            filtered_headings.append(h)
            
        # Parse fields sequentially
        for idx, heading in enumerate(filtered_headings):
            for field, labels in campos_labels.items():
                # Check if heading matches any known labels for this field
                if any(heading.lower() == label.lower() for label in labels):
                    # Value is expected to be the next element in the headings list
                    if idx + 1 < len(filtered_headings):
                        next_heading = filtered_headings[idx + 1]
                        # Verify the next element isn't another label
                        is_label = False
                        for f_name, l_list in campos_labels.items():
                            if any(next_heading.lower() == l.lower() for l in l_list):
                                is_label = True
                                break
                        # Verify against common section title headers too
                        if next_heading.lower() in ['informações', 'media social', 'horários de missas', 'leia mais', 'clero']:
                            is_label = True
                            
                        if not is_label:
                            result[field] = next_heading
                            
    elif tipo_layout == "selector":
        # Direct selector parsing
        for field, selector in campos_seletores.items():
            if selector:
                element = soup.select_one(selector)
                if element:
                    result[field] = element.text.strip()
                    
    # 2. Extract Mass Times
    mass_selector = details_cfg.get("horarios_missa_seletor")
    if mass_selector:
        mass_elem = soup.select_one(mass_selector)
        if mass_elem:
            result['horarios_missa_texto'] = mass_elem.text.strip()
            
    # 3. Extract Social Media Links
    social_selector = details_cfg.get("social_selector")
    if social_selector:
        result['redes_sociais'] = extract_social_media(soup, social_selector)
        
    return result

def scrape_diocese_iterator(config, limit=None):
    """Yields progress string updates (logs) as it executes the scrape process."""
    nome_diocese = config.get("nome")
    url_base = config.get("url_base")
    list_cfg = config.get("listagem", {})
    paginacao = config.get("paginacao", {})
    
    yield f"Iniciando raspagem para: {nome_diocese}"
    yield f"URL Base: {url_base}"
    
    # Phase 1: Collect parish links
    parish_urls = []
    seen_urls = set()
    page = 1
    
    yield "\n=== Fase 1: Coletando URLs das Paróquias ==="
    
    while True:
        # Construct URL based on pagination type
        pag_tipo = paginacao.get("tipo", "single_page")
        if pag_tipo == "url_page":
            url_pattern = paginacao.get("url_pattern")
            if not url_pattern:
                url = url_base
            else:
                url = url_pattern.replace("{page}", str(page))
        else:
            url = url_base
            
        yield f"Acessando página de listagem {page}: {url}"
        
        response = fetch_page(url)
        if not response:
            yield f"Erro ao acessar listagem da página {page}. Encerrando busca."
            break
            
        if response.status_code == 404:
            yield f"Página {page} retornou 404. Fim da paginação."
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Select parish items
        item_sel = list_cfg.get("item_selector")
        items = soup.select(item_sel) if item_sel else []
        
        if not items:
            yield f"Nenhum item de paróquia encontrado na página {page}. Encerrando busca."
            break
            
        yield f"Encontradas {len(items)} paróquias na página {page}."
        
        new_found = False
        for item in items:
            link_sel = list_cfg.get("link_selector")
            a_tag = item.select_one(link_sel) if link_sel else item.find('a')
            
            if not a_tag or not a_tag.get('href'):
                continue
                
            href = resolve_url(url_base, a_tag['href'])
            name = a_tag.text.strip()
            
            if href in seen_urls:
                continue
                
            seen_urls.add(href)
            new_found = True
            
            img_sel = list_cfg.get("imagem_selector")
            img_url = None
            if img_sel:
                img_tag = item.select_one(img_sel)
                if img_tag:
                    img_url = img_tag.get('src') or img_tag.get('data-src')
            if not img_url:
                img_tag = item.find('img')
                if img_tag:
                    img_url = img_tag.get('src')
                    
            if img_url:
                img_url = resolve_url(url_base, img_url)
                
            parish_urls.append({
                'nome': name,
                'url': href,
                'imagem_thumbnail': img_url
            })
            
            if limit and len(parish_urls) >= limit:
                break
                
        if not new_found:
            yield "Nenhuma nova paróquia encontrada nesta página (lista repetida). Finalizando busca de URLs."
            break
            
        if limit and len(parish_urls) >= limit:
            yield f"Limite de teste ({limit}) atingido."
            break
            
        if pag_tipo == "single_page":
            break
            
        page += 1
        time.sleep(0.5)
        
    total_found = len(parish_urls)
    yield f"Concluída Fase 1. Total de paróquias únicas encontradas: {total_found}\n"
    
    if not parish_urls:
        yield "Nenhuma paróquia para processar. Cancelando extração."
        return
        
    # Phase 2: Scrape details
    yield "=== Fase 2: Extraindo Detalhes das Paróquias ==="
    results = []
    
    for idx, p in enumerate(parish_urls, 1):
        yield f"[{idx}/{total_found}] Extraindo detalhes de: {p['nome']}"
        details = scrape_single_parish(p['url'], config)
        if details:
            p.update(details)
        results.append(p)
        time.sleep(0.5)
        
    # Save output
    output_path = config_manager.get_diocese_data_path(nome_diocese)
    try:
        import json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        yield f"\nSUCESSO: Dados salvos em {output_path}"
    except Exception as e:
        yield f"\nERRO ao salvar dados em {output_path}: {e}"
