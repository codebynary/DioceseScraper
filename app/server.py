from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import os
import sys
import requests
import urllib.parse
from bs4 import BeautifulSoup

# Add parent directory to path so we can import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config_manager
from core import agent
from core import scraper

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/api-key', methods=['GET', 'POST'])
def handle_api_key():
    if request.method == 'POST':
        data = request.json or {}
        key = data.get('api_key', '').strip()
        if not key:
            return jsonify({'success': False, 'message': 'Chave de API vazia.'}), 400
            
        # Validate key
        is_valid, error_message = agent.validate_gemini_key(key)
        if is_valid:
            config_manager.save_api_key(key)
            return jsonify({'success': True, 'message': 'Chave de API salva e validada com sucesso!'})
        else:
            return jsonify({
                'success': False, 
                'message': f'Falha na validação: {error_message}'
            }), 400
            
    # GET method
    key_exists = config_manager.get_api_key() is not None
    return jsonify({'key_exists': key_exists})

@app.route('/api/dioceses', methods=['GET'])
def list_dioceses():
    configs = config_manager.list_diocese_configs()
    for c in configs:
        scraped = config_manager.get_scraped_data(c['nome'])
        c['total_paroquias'] = len(scraped)
    return jsonify(configs)

@app.route('/api/analyze', methods=['POST'])
def analyze_diocese():
    api_key = config_manager.get_api_key()
    if not api_key:
        return jsonify({'success': False, 'message': 'Chave da API do Gemini não configurada. Defina-a primeiro.'}), 400
        
    data = request.json or {}
    diocese_name = data.get('nome', '').strip()
    url_base = data.get('url_base', '').strip()
    
    if not diocese_name or not url_base:
        return jsonify({'success': False, 'message': 'Nome e URL Base são obrigatórios.'}), 400
        
    try:
        # 1. Fetch listing HTML
        list_resp = requests.get(url_base, headers=scraper.HEADERS, timeout=15)
        if list_resp.status_code != 200:
            return jsonify({'success': False, 'message': f'Falha ao acessar a URL da listagem: Status {list_resp.status_code}'}), 400
            
        list_html = list_resp.text
        is_sitexp = False
        if 'sitexpresso' in list_html.lower() or 'sx.check' in list_html or 'sx.start' in list_html or 'window.sxid' in list_html:
            is_sitexp = True
            
        parsed = urllib.parse.urlparse(url_base)
        
        if is_sitexp:
            # Construct AJAX listing URL
            ajax_url = f"{parsed.scheme}://{parsed.netloc}/?ajax=get&path={parsed.path}"
            ajax_resp = requests.get(ajax_url, headers=scraper.HEADERS, timeout=15)
            if ajax_resp.status_code == 200:
                try:
                    ajax_data = ajax_resp.json()
                    list_html = ajax_data.get('html', '')
                except Exception as e:
                    print(f"Error parsing AJAX listing JSON: {e}")
            else:
                return jsonify({'success': False, 'message': f'Falha ao acessar listagem dinâmica via AJAX: Status {ajax_resp.status_code}'}), 400
                
        list_soup = BeautifulSoup(list_html, 'html.parser')
        detail_url = None
        
        if is_sitexp:
            # Find the first element with component attribute in the dynamically loaded HTML
            comp_div = list_soup.find(lambda tag: tag.has_attr('component'))
            if comp_div:
                comp_val = comp_div['component']
                detail_url = f"{parsed.scheme}://{parsed.netloc}/?ajax=get&comp={comp_val}"
        else:
            # 2. Try to find at least one link to a parish details page
            # Let's inspect all anchors. We look for anchors that contain '/paroquias/' or look like subpaths.
            all_anchors = list_soup.find_all('a', href=True)
            
            for a in all_anchors:
                href = a['href']
                # Resolve relative URL
                full_url = scraper.resolve_url(url_base, href)
                # Avoid the main base URL, categories, feed, or page URLs
                if (full_url.startswith(url_base) and 
                    full_url != url_base and 
                    '/page/' not in full_url and 
                    '/categoria/' not in full_url and 
                    '/feed/' not in full_url and
                    '?' not in full_url):
                    detail_url = full_url
                    break
                    
            if not detail_url:
                # Fallback: search for any anchor in body
                for a in all_anchors:
                    href = a['href']
                    full_url = scraper.resolve_url(url_base, href)
                    if full_url.startswith(url_base) and full_url != url_base:
                        detail_url = full_url
                        break
                        
        if not detail_url:
            return jsonify({'success': False, 'message': 'Não foi possível detectar links de paróquias na página de listagem. Verifique se a URL está correta.'}), 400
            
        # 3. Fetch detail page HTML
        detail_resp = requests.get(detail_url, headers=scraper.HEADERS, timeout=15)
        if detail_resp.status_code != 200:
            return jsonify({'success': False, 'message': f'Falha ao acessar a página de exemplo de detalhes ({detail_url}): Status {detail_resp.status_code}'}), 400
            
        detail_html = detail_resp.text
        if is_sitexp:
            try:
                detail_data = detail_resp.json()
                detail_html = detail_data.get('html', '')
            except Exception as e:
                print(f"Error parsing AJAX detail JSON: {e}")
                
        # 4. Run Gemini layout analysis
        config_data = agent.analyze_diocese_layout(
            api_key, diocese_name, url_base, list_html, detail_html
        )
        
        if not config_data:
            return jsonify({'success': False, 'message': 'A inteligência artificial falhou em mapear os seletores para este site.'}), 500
            
        # Inject is_sitexpresso and specific overrides if it is a SitExpresso site
        if is_sitexp:
            config_data['is_sitexpresso'] = True
            
            # Setup listagem configs if missing or generic
            if 'listagem' not in config_data:
                config_data['listagem'] = {}
                
            item_sel = config_data['listagem'].get('item_selector')
            if not item_sel or item_sel in ['a', 'div']:
                comp_tag = list_soup.find(lambda tag: tag.has_attr('component'))
                parent = comp_tag.parent if comp_tag else None
                parent_class = None
                while parent and parent.name != 'body':
                    if parent.get('class'):
                        parent_class = "." + ".".join(parent.get('class'))
                        if any(x in parent_class for x in ['ctt', 'item', 'button', 'card']):
                            break
                    parent = parent.parent
                config_data['listagem']['item_selector'] = parent_class or 'div.ctt-group-button'
                
            link_sel = config_data['listagem'].get('link_selector')
            if not link_sel or link_sel in ['a', 'div'] or 'href' in link_sel:
                config_data['listagem']['link_selector'] = 'div[component]'
                
            if 'paginacao' not in config_data:
                config_data['paginacao'] = {}
            config_data['paginacao']['tipo'] = 'single_page'
            config_data['paginacao']['url_pattern'] = None
            config_data['paginacao']['next_selector'] = None
            
        # 5. Run a quick test scrape using the generated config on the detail page
        test_parish = scraper.scrape_single_parish(detail_url, config_data)
        if test_parish:
            test_parish['nome'] = "Paróquia Teste (Exemplo)"
            test_parish['url'] = detail_url
            
        return jsonify({
            'success': True,
            'config': config_data,
            'test_parish': test_parish
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro durante a análise: {str(e)}'}), 500

@app.route('/api/confirm', methods=['POST'])
def confirm_config():
    data = request.json or {}
    config_data = data.get('config')
    diocese_name = config_data.get('nome') if config_data else None
    
    if not config_data or not diocese_name:
        return jsonify({'success': False, 'message': 'Configuração inválida.'}), 400
        
    # Save config
    config_id = config_manager.save_diocese_config(diocese_name, config_data)
    
    return jsonify({
        'success': True, 
        'config_id': os.path.basename(config_id).replace('.json', ''),
        'message': 'Configuração salva com sucesso!'
    })

@app.route('/api/scrape/stream/<config_id>')
def stream_scrape(config_id):
    config = config_manager.get_diocese_config(config_id)
    if not config:
        return Response("data: Configuração não encontrada.\n\n", mimetype='text/event-stream')
        
    def event_stream():
        for log in scraper.scrape_diocese_iterator(config):
            yield f"data: {log}\n\n"
            
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/data/<config_id>', methods=['GET'])
def get_data(config_id):
    config = config_manager.get_diocese_config(config_id)
    if not config:
        return jsonify({'success': False, 'message': 'Configuração não encontrada.'}), 404
        
    data = config_manager.get_scraped_data(config['nome'])
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
