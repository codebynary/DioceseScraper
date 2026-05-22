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
