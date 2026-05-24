import requests
from bs4 import BeautifulSoup
import time
import random
import urllib.parse
from core import config_manager
from core import enricher

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

# Delay educado entre requisições: base + jitter aleatório
POLITE_DELAY_BASE = 1.5   # segundos entre cada paróquia
POLITE_DELAY_JITTER = 0.5 # ±variação aleatória

def polite_sleep(base=POLITE_DELAY_BASE, jitter=POLITE_DELAY_JITTER):
    """Espera educada com jitter para não parecer um bot previsível."""
    time.sleep(base + random.uniform(-jitter, jitter))

def _is_spa_or_wix(html_text):
    """
    Detecta se um HTML retornado é de um site SPA/Wix que precisa de renderização JS.
    Retorna True se o conteúdo visível for mínimo ou houver marcadores de frameworks JS.
    """
    markers = [
        'wix.com', 'wixstatic.com', 'wix-essential',
        '__NEXT_DATA__', '__nuxt', 'window.__NUXT__',
        'data-reactroot', 'ng-version',
        'thunderbolt', 'parastorage.com',
    ]
    html_lower = html_text.lower()
    for marker in markers:
        if marker.lower() in html_lower:
            return True

    # Verifica se o body tem pouco conteúdo visível (menos de 500 chars de texto)
    try:
        from bs4 import BeautifulSoup as _BS
        soup = _BS(html_text, 'html.parser')
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        visible_text = soup.get_text(strip=True)
        if len(visible_text) < 500:
            return True
    except Exception:
        pass
    return False


def fetch_page_with_browser(url, wait_for='networkidle', timeout=30000):
    """
    Renderiza uma página usando Playwright (Chromium headless real).
    Usado automaticamente para sites Wix, React, Vue e outros SPAs.
    Retorna um objeto fake-response com .text e .status_code para compatibilidade.
    """
    try:
        from playwright.sync_api import sync_playwright

        class BrowserResponse:
            def __init__(self, text, status_code=200):
                self.text = text
                self.status_code = status_code

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-zygote',
                ]
            )
            context = browser.new_context(
                user_agent=HEADERS['User-Agent'],
                locale='pt-BR',
                viewport={'width': 1280, 'height': 800},
            )
            page = context.new_page()

            # Bloqueia recursos desnecessários para acelerar (imagens, fontes, mídias)
            page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,mp4,mp3}", lambda route: route.abort())

            response = page.goto(url, wait_until=wait_for, timeout=timeout)
            status = response.status if response else 200

            # Aguarda o conteúdo principal aparecer
            try:
                page.wait_for_load_state('networkidle', timeout=15000)
            except Exception:
                pass  # Timeout ok, pega o que tiver

            html = page.content()
            browser.close()
            return BrowserResponse(html, status)

    except ImportError:
        print("[fetch_page_with_browser] Playwright não instalado. Usando requests.")
        return fetch_page_requests(url)
    except Exception as e:
        print(f"[fetch_page_with_browser] Erro ao renderizar {url}: {e}")
        return None


def fetch_page_requests(url, retries=4, delay=2):
    """Fetch simples via requests (sem JS). Uso interno."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r
            elif r.status_code == 404:
                return r
            elif r.status_code == 429:
                wait = delay * (2 ** attempt) + random.uniform(0, 2)
                time.sleep(wait)
                continue
        except requests.RequestException as e:
            print(f"[fetch_page_requests] Tentativa {attempt+1}/{retries} falhou para {url}: {e}")
        time.sleep(delay * (attempt + 1))
    return None


def fetch_page(url, retries=4, delay=2):
    """
    Busca uma URL de forma inteligente:
    1. Tenta com requests (rápido)
    2. Se detectar site SPA/Wix (conteúdo vazio ou marcadores JS), usa Playwright
    """
    response = fetch_page_requests(url, retries=retries, delay=delay)

    if response and response.status_code == 200:
        if _is_spa_or_wix(response.text):
            print(f"[fetch_page] SPA/Wix detectado em {url}. Usando Playwright...")
            browser_response = fetch_page_with_browser(url)
            if browser_response:
                return browser_response
    return response


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

def _extract_sitexpresso_text_block(soup, result):
    """
    Para sites SitExpresso (ex: Chapecó), os dados vêm em blocos de texto corrido.
    Encontra o bloco específico de detalhes ctt-text no HTML e extrai de forma estruturada.
    """
    import re
    # Encontrar o bloco de detalhes ctt-text
    detail_block = None
    for div in soup.select('div.ctt-text'):
        div_text = div.get_text()
        if any(k in div_text for k in ['Endereço:', 'Contato:', 'Padre(s):', 'Padres:']):
            detail_block = div
            break
            
    if not detail_block:
        text = soup.get_text(separator='\n', strip=True)
    else:
        text = detail_block.get_text(separator='\n', strip=True)
        
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    sections = {
        'endereco': [],
        'contato': [],
        'clero': [],
        'setor': [],
        'secretaria': [],
        'outros': []
    }
    
    current_section = None
    
    for line in lines:
        line_lower = line.lower()
        if 'endereço' in line_lower:
            current_section = 'endereco'
            content = re.sub(r'^Endereço\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if content:
                sections['endereco'].append(content)
        elif 'contato' in line_lower:
            current_section = 'contato'
            content = re.sub(r'^Contato\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if content:
                sections['contato'].append(content)
        elif any(k in line_lower for k in ['padre', 'presbítero', 'clero']):
            current_section = 'clero'
            content = re.sub(r'^(?:Padre[s]?|Presbítero[s]?|Clero)\s*(?:\([s]\))?\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if content:
                sections['clero'].append(content)
        elif 'setor' in line_lower:
            current_section = 'setor'
            content = re.sub(r'^Setor\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if content:
                sections['setor'].append(content)
        elif any(k in line_lower for k in ['secretaria', 'atendimento', 'funcionamento']):
            current_section = 'secretaria'
            content = re.sub(r'^(?:Secretaria|Atendimento|Funcionamento)\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if content:
                sections['secretaria'].append(content)
        elif any(k in line_lower for k in ['organização', 'história', 'acompanhe']):
            current_section = 'outros'
        else:
            if current_section:
                sections[current_section].append(line)
                
    # 1. Endereço
    if sections['endereco']:
        result['endereco'] = ", ".join(sections['endereco'])
        
    # 2. Clero
    if sections['clero']:
        result['clero'] = "\n".join(sections['clero'])
        
    # 3. Contatos (Telefone e E-mail)
    tels = []
    emails = []
    for line in sections['contato']:
        email_match = re.search(r'[\w.\-]+@[\w.\-]+\.\w{2,}', line)
        if email_match:
            emails.append(email_match.group(0))
        else:
            clean_tel = re.sub(r'^(?:Fone|Whats(?:App)?|Telefone|Contato|Celular)\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if clean_tel:
                tels.append(clean_tel)
                
    if tels:
        result['telefone'] = " / ".join(tels)
    if emails:
        result['email'] = emails[0]
        
    # 4. Setor
    if sections['setor']:
        result['setor'] = ", ".join(sections['setor'])
        
    # 5. Secretaria / Funcionamento
    if sections['secretaria']:
        result['funcionamento_secretaria'] = ", ".join(sections['secretaria'])
        
    return result


def _extract_blind_regex_fallback(soup, result):
    """
    Se o site não possui rótulos visuais (Ex: Ordinariado Militar) e os seletores falharam,
    varre o texto bruto e tenta pescar telefone, e-mail e endereço via Expressão Regular.
    """
    import re
    # Copia o soup para não afetar as outras buscas caso precise
    import copy
    temp_soup = copy.copy(soup)
    
    # Remove header, footer, etc to avoid false positives
    for tag in temp_soup(['header', 'footer', 'nav', 'aside', 'script', 'style', 'title']):
        if tag:
            tag.decompose()
            
    # Try to target the main content wrapper
    main_content = temp_soup.find('main') or temp_soup.find(class_=re.compile(r'elementor-widget-theme-post-content|page-content'))
    
    text = ""
    if main_content:
        text = main_content.get_text(separator='\n', strip=True)
        
    if len(text) < 50:
        text = temp_soup.get_text(separator='\n', strip=True)
        
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    tels = []
    emails = []
    enderecos = []
    
    for line in lines:
        # Match email
        email_match = re.search(r'[\w.\-]+@[\w.\-]+\.\w{2,}', line)
        if email_match:
            emails.append(email_match.group(0))
            
        # Match phone (DDD and dashes, e.g. (35) 3239-4126, 3229-4100)
        phone_matches = re.findall(r'\(?\d{2}\)?\s*\d{4,5}-?\d{4}', line)
        if phone_matches:
            tels.extend(phone_matches)
            
        # Match Address: Has CEP or starts with Rua, Avenida, etc.
        line_lower = line.lower()
        has_cep = re.search(r'\b\d{5}-?\d{3}\b', line)
        starts_with_street = any(line_lower.startswith(prefix) for prefix in ['rua ', 'av ', 'avenida ', 'praça ', 'praca ', 'rodovia ', 'estr ', 'estrada ', 'cep '])
        
        # se tem CEP ou começa com rua/avenida, é endereço garantido
        if has_cep or starts_with_street:
            # limpar lixo antes
            clean_addr = re.sub(r'^(?:Endereço|End):?\s*', '', line, flags=re.IGNORECASE)
            enderecos.append(clean_addr)
            
    if not result.get('telefone') and tels:
        result['telefone'] = " / ".join(list(set(tels)))
    if not result.get('email') and emails:
        result['email'] = emails[0]
    if not result.get('endereco') and enderecos:
        result['endereco'] = "\n".join(enderecos)
        
    return result


def scrape_single_parish(url, config):
    """Scrapes detail fields of a single parish page using config rules."""
    if not config:
        config = {}
    response = fetch_page(url)
    if not response or response.status_code != 200:
        return None
        
    if config.get("is_sitexpresso"):
        try:
            data = response.json()
            html_text = data.get('html', '')
        except Exception as e:
            print(f"Error parsing SitExpresso detail JSON from {url}: {e}")
            html_text = response.text
    else:
        html_text = response.text
        
    soup = BeautifulSoup(html_text, 'html.parser')
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

    # Para SitExpresso, tenta extração por regex de texto corrido primeiro
    if config.get("is_sitexpresso"):
        result = _extract_sitexpresso_text_block(soup, result)
    
    # 1. Extract detail fields based on layout strategy
    if not config.get("is_sitexpresso"):
        if tipo_layout == "label_value":
            headings_selector = details_cfg.get("headings_selector") or next((v for v in campos_seletores.values() if v), '.elementor-heading-title')
            if not headings_selector:
                headings_selector = '.elementor-heading-title'
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
                    if not labels:
                        continue
                    if isinstance(labels, str):
                        labels = [labels]
                    # Check if heading matches any known labels for this field
                    if any(heading.lower() == label.lower() for label in labels):
                        # Value is expected to be the next element in the headings list
                        if idx + 1 < len(filtered_headings):
                            next_heading = filtered_headings[idx + 1]
                            # Verify the next element isn't another label
                            is_label = False
                            for f_name, l_list in campos_labels.items():
                                if not l_list:
                                    continue
                                if isinstance(l_list, str):
                                    l_list = [l_list]
                                if any(next_heading.lower() == l.lower() for l in l_list):
                                    is_label = True
                                    break
                            # Verify against common section title headers too
                            if next_heading.lower() in ['informações', 'media social', 'horários de missas', 'leia mais', 'clero']:
                                is_label = True
                                
                            if not is_label:
                                result[field] = next_heading
                                
        # Direct selector parsing for selector layout or as a fallback for missing fields
        for field, selector in campos_seletores.items():
            if selector and (tipo_layout == "selector" or result[field] is None):
                if field == 'clero':
                    elements = soup.select(selector)
                    if elements:
                        clero_members = []
                        for el in elements:
                            name_span = el.find('span', class_=lambda c: c and 'font-semibold' in c)
                            role_span = el.find('span', class_=lambda c: c and ('text-secondary' in c or 'text-sm' in c))
                            if name_span:
                                name = name_span.text.strip()
                                role = role_span.text.strip() if role_span else ""
                                clero_members.append(f"{name} - {role}" if role else name)
                            else:
                                # For Campinas style: role is in the parent element, name is in anchor
                                if el.name == 'a' and el.get('href') and '/clero/' in el.get('href') and el.parent and el.parent.name == 'h4':
                                    txt = el.parent.text.strip()
                                else:
                                    txt = el.text.strip()
                                lines = [l.strip() for l in txt.split('\n') if l.strip()]
                                clero_members.extend(lines)
                        seen = set()
                        unique_members = []
                        for m in clero_members:
                            if m not in seen:
                                seen.add(m)
                                unique_members.append(m)
                        result[field] = "\n".join(unique_members)
                        continue
                        
                elements = soup.select(selector)
                if elements:
                    element = elements[-1]
                    
                    if field == 'email':
                        cf_email = element.get('data-cfemail') or (element.find('a', class_='__cf_email__').get('data-cfemail') if element.find('a', class_='__cf_email__') else None)
                        if not cf_email and 'data-cfemail' in str(element):
                            import re
                            m = re.search(r'data-cfemail="([0-9a-fA-F]+)"', str(element))
                            if m:
                                cf_email = m.group(1)
                        if cf_email:
                            try:
                                enc = bytes.fromhex(cf_email)
                                key = enc[0]
                                dec = bytes([b ^ key for b in enc[1:]])
                                decoded = dec.decode('utf-8')
                                if decoded:
                                    result[field] = decoded
                                    continue
                            except:
                                pass
                                
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
        
    # 4. Fallback Extraction (Blind Regex) if everything failed
    core_fields_empty = not any([result['endereco'], result['telefone'], result['email'], result['clero']])
    if core_fields_empty:
        result = _extract_blind_regex_fallback(soup, result)
        
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
        
        if config.get("is_sitexpresso"):
            parsed = urllib.parse.urlparse(url)
            ajax_url = f"{parsed.scheme}://{parsed.netloc}/?ajax=get&path={parsed.path}"
            response = fetch_page(ajax_url)
            if response:
                try:
                    data = response.json()
                    html_text = data.get('html', '')
                except Exception as e:
                    print(f"Error parsing AJAX listing JSON: {e}")
                    html_text = response.text
            else:
                html_text = None
        elif config.get("is_wpbakery_grid"):
            response = fetch_page(url)
            if not response:
                html_text = None
            else:
                try:
                    main_soup = BeautifulSoup(response.text, 'html.parser')
                    grid_container = main_soup.find(class_='vc_grid-container')
                    if grid_container:
                        settings_str = grid_container.get('data-vc-grid-settings')
                        nonce = grid_container.get('data-vc-public-nonce')
                        post_id = grid_container.get('data-vc-post-id')
                        ajax_endpoint = grid_container.get('data-vc-request') or "https://arquidiocesecampinas.com/wp-admin/admin-ajax.php"
                        
                        import json
                        settings = json.loads(settings_str)
                        settings["items_per_page"] = "-1"
                        
                        # Build flat payload
                        flat_payload = {
                            "action": "vc_get_vc_grid_data",
                            "vc_action": "vc_get_vc_grid_data",
                            "tag": "vc_basic_grid",
                            "vc_post_id": post_id,
                            "_vcnonce": nonce
                        }
                        for sk, sv in settings.items():
                            if sk != "btn_data":
                                flat_payload[f"data[{sk}]"] = str(sv)
                                
                        # Make POST request
                        yield "Carregando listagem completa de paróquias via WPBakery AJAX..."
                        ajax_resp = requests.post(ajax_endpoint, data=flat_payload, headers=HEADERS, timeout=30)
                        if ajax_resp.status_code == 200:
                            html_text = ajax_resp.text
                            response = ajax_resp
                        else:
                            yield f"Erro na requisição WPBakery AJAX: Status {ajax_resp.status_code}"
                            html_text = None
                            response = ajax_resp
                    else:
                        yield "Não foi possível encontrar o container de grid do WPBakery. Usando HTML estático."
                        html_text = response.text
                except Exception as ex:
                    yield f"Erro ao processar WPBakery Grid: {ex}. Usando HTML estático."
                    html_text = response.text
        else:
            response = fetch_page(url)
            html_text = response.text if response else None

        if not html_text:
            yield f"Erro ao acessar listagem da página {page}. Encerrando busca."
            break
            
        if response and response.status_code == 404:
            yield f"Página {page} retornou 404. Fim da paginação."
            break
            
        soup = BeautifulSoup(html_text, 'html.parser')
        
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
            
            if config.get("is_sitexpresso"):
                if not a_tag:
                    a_tag = item.select_one('[component]')
                
                comp_val = a_tag.get('component') if a_tag else None
                if not comp_val:
                    comp_div = item.select_one('[component]')
                    comp_val = comp_div.get('component') if comp_div else None
                    
                if not comp_val:
                    continue
                    
                parsed = urllib.parse.urlparse(url_base)
                href = f"{parsed.scheme}://{parsed.netloc}/?ajax=get&comp={comp_val}"
                
                name = None
                caption_tag = item.select_one('figcaption')
                if caption_tag:
                    name = caption_tag.text.strip()
                if not name:
                    btn_tag = item.select_one('div.btn.btn-modal-images')
                    if btn_tag:
                        name = btn_tag.text.strip()
                if not name and a_tag:
                    name = a_tag.text.strip()
                if not name:
                    name = "Paróquia desconhecida"
                name = " ".join(name.split())
            else:
                if not a_tag or not a_tag.get('href'):
                    continue
                href = resolve_url(url_base, a_tag['href'])
                name = a_tag.text.strip()
                if not name and a_tag.get('title'):
                    name = a_tag.get('title').strip()
                if not name or name.lower() in ['ver mais', 'saiba mais', 'leia mais', 'detalhes', 'visualizar', 'link']:
                    # Try to find a header or span inside the parent container that contains the name
                    title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if not title_elem:
                        # Find spans with large or bold text or containing class name like 'title' or 'name'
                        title_elem = item.select_one('[class*="title"], [class*="name"], .wp-parresia-register-principal-color-text')
                    if not title_elem:
                        # Fallback to the first span or div
                        title_elem = item.find('span')
                    if title_elem:
                        name = title_elem.text.strip()
                if not name:
                    name = "Paróquia desconhecida"
                name = " ".join(name.split())
                
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
        polite_sleep(base=1.0)
        
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
        
        # Enriquecer o payload com dados estruturados
        enriched_p = enricher.enrich_parish(p, nome_diocese, url_base)
        results.append(enriched_p)
        
        # Delay educado com jitter: evita bloqueio e parece comportamento humano
        polite_sleep()
        
    # Save output
    output_path = config_manager.get_diocese_data_path(nome_diocese)
    try:
        merged = config_manager.merge_scraped_data(nome_diocese, results)
        
        # Gerar relatório qualitativo de validação
        report = enricher.generate_enrichment_report(nome_diocese, merged)
        yield report
        
        yield f"\nSUCESSO: Dados mesclados e salvos em {output_path}"
    except Exception as e:
        yield f"\nERRO ao salvar dados em {output_path}: {e}"
