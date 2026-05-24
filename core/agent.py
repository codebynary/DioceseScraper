from google import genai
from google.genai import types
import json
import re

# System prompt guiding the Gemini model to parse HTML structure and return a JSON config
SYSTEM_PROMPT = """
You are an expert web scraping configuration generator. 
Given the HTML snippets of a Diocese website (listing page and detail page), your goal is to identify the correct CSS selectors and extraction strategies to scrape the parishes.

You must return a JSON object conforming exactly to this schema:
{
  "nome": "Name of the Diocese/Archdiocese",
  "url_base": "The listing URL provided",
  "listagem": {
    "item_selector": "CSS selector for each parish item container on the list page",
    "link_selector": "CSS selector for the anchor tag (href) relative to the item container",
    "imagem_selector": "CSS selector for the thumbnail image src relative to the item container (optional, null if none)"
  },
  "paginacao": {
    "tipo": "url_page | link_next | single_page",
    "url_pattern": "URL template containing {page} if tipo is url_page, e.g. https://domain.org/paroquias/page/{page}/, otherwise null",
    "next_selector": "CSS selector for next page button if tipo is link_next, otherwise null"
  },
  "detalhes": {
    "tipo_layout": "label_value | selector",
    "campos_labels": {
      "setor": ["Setor:", "Setor"],
      "telefone": ["Telefone:", "Telefone", "Fone:", "Contato:"],
      "email": ["E-mail:", "Email:"],
      "funcionamento_secretaria": ["Funcionamento na Secretaria", "Fucionamentos na Secretaria", "Secretaria:", "Secretaria Paroquial:"],
      "endereco": ["Endereço", "Endereço:", "Localização:"],
      "clero": ["Clero", "Clero:", "Pároco:", "Pároco", "Padre:", "Padres:"]
    },
    "campos_seletores": {
      "setor": "CSS selector if tipo_layout is 'selector', or CSS selector of label tags list if 'label_value' (e.g. '.elementor-heading-title')",
      "telefone": "CSS selector if tipo_layout is 'selector', or CSS selector of label tags list if 'label_value'",
      "email": "CSS selector if tipo_layout is 'selector', or CSS selector of label tags list if 'label_value'",
      "funcionamento_secretaria": "CSS selector if tipo_layout is 'selector', or CSS selector of label tags list if 'label_value'",
      "endereco": "CSS selector if tipo_layout is 'selector', or CSS selector of label tags list if 'label_value'",
      "clero": "CSS selector if tipo_layout is 'selector', or CSS selector of label tags list if 'label_value'"
    },
    "horarios_missa_seletor": "CSS selector for mass times text/container",
    "social_selector": "CSS selector for social media anchor tags (e.g. '.elementor-widget-social-icons a')"
  }
}

Definitions for detalhes.tipo_layout:
- 'label_value': Selected elements represent sequential label-value headers/lines (e.g. Elementor where one heading says 'Telefone:' and the next heading contains the phone number). The campos_seletores will contain the selector of the headers (e.g. '.elementor-heading-title').
- 'selector': Each field is directly mapped to a specific CSS selector (e.g. a div with class '.parish-phone').

Make sure your selectors are robust and avoid header/footer elements.
"""

def clean_html(html_str):
    """Strips heavy tags (script, style, svg) and limits size to fit tokens."""
    # Remove script, style and svg elements
    html_str = re.sub(r'<script.*?</script>', '', html_str, flags=re.DOTALL)
    html_str = re.sub(r'<style.*?</style>', '', html_str, flags=re.DOTALL)
    html_str = re.sub(r'<svg.*?</svg>', '', html_str, flags=re.DOTALL)
    # Remove large comment blocks
    html_str = re.sub(r'<!--.*?-->', '', html_str, flags=re.DOTALL)
    # Collapse multiple whitespaces
    html_str = re.sub(r'\s+', ' ', html_str)
    return html_str[:100000] # Increased size to fit large Elementor pages

def validate_gemini_key(api_key):
    """Tests connection to Gemini API with the provided key.
    Returns (is_valid, error_message)
    """
    import time
    for attempt in range(5):
        try:
            client = genai.Client(api_key=api_key)
            # Call a very cheap/simple model to check if key is active
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents='Respond only "OK".'
            )
            if response.text and "OK" in response.text.upper():
                return True, ""
            return False, "Resposta inesperada da API (não continha 'OK')."
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg or "ResourceExhausted" in error_msg:
                sleep_time = 2 ** attempt
                print(f"Gemini API 503/UNAVAILABLE, retrying key validation in {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            print(f"Error validating Gemini API key: {error_msg}")
            return False, error_msg
    return False, "Gemini API unavailable (503) after multiple retries."

def analyze_diocese_layout(api_key, diocese_name, url_base, list_html, detail_html):
    """Sends HTML samples to Gemini to determine selectors and returns the config JSON."""
    import time
    client = genai.Client(api_key=api_key)
    
    clean_list = clean_html(list_html)
    clean_detail = clean_html(detail_html)
    
    prompt = f"""
    Analyze the layout of the diocese website "{diocese_name}" with listing URL: {url_base}.
    
    Here is a snippet of the LISTING PAGE HTML:
    ```html
    {clean_list}
    ```
    
    Here is a snippet of a DETAIL PAGE HTML (representing a single parish):
    ```html
    {clean_detail}
    ```
    
    Identify the selectors for:
    1. The list items, detail page link, and thumbnail image.
    2. Pagination type (check if it uses page/N/ style URLs or a next page link).
    3. The detail fields (Setor, Telefone, E-mail, Funcionamento da Secretaria, Endereço, Clero).
       Determine if it follows a 'label_value' layout (label elements followed by value elements, e.g. headers) or if each has a specific 'selector'.
    4. The mass schedules (horarios_missa_seletor) and social media links.
    
    Return the config JSON matching the requested schema.
    """
    
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            # Parse result to ensure it is valid JSON
            config_data = json.loads(response.text)
            return config_data
        except Exception as e:
            error_msg = str(e)
            print(f"Attempt {attempt + 1} failed: {error_msg}")
            if "503" in error_msg or "UNAVAILABLE" in error_msg or "ResourceExhausted" in error_msg:
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
                continue
            print(f"Error calling Gemini to generate config: {e}")
            return None
    return None
