import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
DADOS_DIR = os.path.join(BASE_DIR, "dados")
SETTINGS_FILE = os.path.join(CONFIGS_DIR, "settings.json")

def ensure_dirs():
    """Ensures that configs and dados directories exist."""
    os.makedirs(CONFIGS_DIR, exist_ok=True)
    os.makedirs(DADOS_DIR, exist_ok=True)

def save_api_key(api_key):
    """Saves the Gemini API key in settings.json."""
    ensure_dirs()
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            pass
    settings["GEMINI_API_KEY"] = api_key
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

def get_api_key():
    """Retrieves the Gemini API key. First checks environment, then settings.json."""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY")
    ensure_dirs()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("GEMINI_API_KEY")
        except Exception:
            pass
    return None

def save_diocese_config(name, config_data):
    """Saves a diocese configuration json file."""
    ensure_dirs()
    filename = name.lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c")
    filepath = os.path.join(CONFIGS_DIR, f"{filename}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    return filepath

def list_diocese_configs():
    """Lists all saved diocese configurations."""
    ensure_dirs()
    configs = []
    for file in os.listdir(CONFIGS_DIR):
        if file.endswith(".json") and file != "settings.json":
            filepath = os.path.join(CONFIGS_DIR, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    configs.append({
                        "id": file.replace(".json", ""),
                        "nome": data.get("nome", file.replace(".json", "")),
                        "url_base": data.get("url_base", ""),
                        "config": data
                    })
            except Exception:
                pass
    return configs

def get_diocese_config(config_id):
    """Gets details for a specific diocese config by its ID."""
    ensure_dirs()
    filepath = os.path.join(CONFIGS_DIR, f"{config_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def delete_diocese_config(config_id):
    """Deletes a diocese configuration and its associated scraped data."""
    config = get_diocese_config(config_id)
    if not config:
        return False
        
    config_path = os.path.join(CONFIGS_DIR, f"{config_id}.json")
    if os.path.exists(config_path):
        try:
            os.remove(config_path)
        except OSError:
            pass
            
    # Delete data folder if exists
    name = config.get('nome')
    if name:
        data_path = get_diocese_data_path(name)
        data_dir = os.path.dirname(data_path)
        if os.path.exists(data_dir):
            import shutil
            try:
                shutil.rmtree(data_dir)
            except OSError:
                pass
    return True

def get_diocese_data_path(name):
    """Gets the path where a diocese's scraped data should be saved."""
    ensure_dirs()
    folder_name = name.lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c")
    diocese_folder = os.path.join(DADOS_DIR, folder_name)
    os.makedirs(diocese_folder, exist_ok=True)
    return os.path.join(diocese_folder, "paroquias.json")

def get_scraped_data(name):
    """Reads scraped data for a diocese if it exists."""
    path = get_diocese_data_path(name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def merge_scraped_data(name, new_results, is_append=False):
    """
    Intelligently merges new crawl results with existing scraped data for a diocese,
    preserving curated fields and updating timestamps.
    If is_append is True, old parishes not found in the new scrape are kept as active.
    """
    import datetime
    
    path = get_diocese_data_path(name)
    old_results = get_scraped_data(name)
    
    # Create mapping of old results by URL
    old_map = {p['url']: p for p in old_results}
    
    merged_results = []
    new_urls = {p['url'] for p in new_results}
    now_str = datetime.datetime.now().isoformat()
    
    # Fields to preserve if curated, otherwise copy new scraped value
    standard_fields = [
        'nome', 'setor', 'telefone', 'email', 'funcionamento_secretaria',
        'endereco', 'clero', 'redes_sociais', 'horarios_missa_texto', 'imagem_thumbnail'
    ]
    
    # 1. Process new scraped results (either update or add)
    from core import enricher
    for p_new in new_results:
        url = p_new['url']
        if url in old_map:
            p_old = old_map[url]
            
            # Start with a copy of old data to preserve curations and metadata
            merged_p = p_old.copy()
            
            # Set/Update status and timestamps
            merged_p['status'] = 'ativo'
            is_curated = p_old.get('curado', False)
            
            has_changes = False
            for field in standard_fields:
                new_val = p_new.get(field)
                old_val = p_old.get(field)
                
                # Check for list/dict types or clean values
                if is_curated:
                    # Keep old curated value if it's not empty, otherwise backfill with new
                    if old_val is None or old_val == "" or old_val == [] or old_val == {}:
                        if new_val is not None and new_val != "" and new_val != [] and new_val != {}:
                            merged_p[field] = new_val
                            has_changes = True
                else:
                    # Not curated, overwrite with newly crawled data if different
                    if old_val != new_val:
                        merged_p[field] = new_val
                        has_changes = True
            
            # Re-enrich the merged flat fields to sync structured fields
            enriched_merged_p = enricher.enrich_parish(merged_p, name, p_new.get("fonte", {}).get("url", ""))
            
            # Detect changes in non-metadata fields to set last update timestamp
            has_structured_diff = False
            for k, v in enriched_merged_p.items():
                if k not in p_old or p_old[k] != v:
                    if k not in ['ultima_atualizacao', 'data_criacao', 'status']:
                        has_structured_diff = True
                        break
                        
            if has_structured_diff:
                enriched_merged_p['ultima_atualizacao'] = now_str
            else:
                # Keep original timestamps
                if 'data_criacao' in p_old:
                    enriched_merged_p['data_criacao'] = p_old['data_criacao']
                if 'ultima_atualizacao' in p_old:
                    enriched_merged_p['ultima_atualizacao'] = p_old['ultima_atualizacao']
                
            merged_results.append(enriched_merged_p)
        else:
            # It's a brand new parish!
            fonte_dict_new = p_new.get("fonte") or {}
            enriched_new = enricher.enrich_parish(p_new, name, fonte_dict_new.get("url", ""))
            enriched_new['curado'] = False
            enriched_new['status'] = 'novo'
            enriched_new['data_criacao'] = now_str
            enriched_new['ultima_atualizacao'] = now_str
            merged_results.append(enriched_new)
            
    # 2. Process old parishes that were NOT found in the new scrape (removed/archived)
    for url, p_old in old_map.items():
        if url not in new_urls:
            p_old_copy = p_old.copy()
            # If it was already marked as removed, keep it. Otherwise flag it.
            if not is_append and p_old_copy.get('status') != 'removido':
                p_old_copy['status'] = 'removido'
                p_old_copy['ultima_atualizacao'] = now_str
            fonte_dict = p_old_copy.get("fonte") or {}
            enriched_old = enricher.enrich_parish(p_old_copy, name, fonte_dict.get("url", ""))
            merged_results.append(enriched_old)
            
    # Write back to disk
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)
        
    return merged_results
