import requests
from bs4 import BeautifulSoup
import urllib3
import re
import os
import time

urllib3.disable_warnings()

output_file = r'dados\import_md\Paroquias da Arquidiocese do Rio de Janeiro RJ.md'

print("Iniciando varredura das páginas da Arquidiocese do Rio de Janeiro...")
ids = []

# As páginas vão de 1 a 6 (tem cerca de 280 paróquias)
for page in range(1, 7):
    url = f'https://www.arqrio.com.br/curia/paroquias.php?pagina={page}'
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Encontrar todos os links de sanfona
    links = soup.select('a[data-toggle="collapse"]')
    for a in links:
        onclick = a.get('onclick', '')
        # onclick="recuperaDetalhes('panel-body1','3','3')"
        match = re.search(r"recuperaDetalhes\('.*?','(\d+)','(\d+)'\)", onclick)
        if match:
            id_paroquia = match.group(1)
            id_culto = match.group(2)
            # O JS usa id_culto se for != 0, senao usa id_paroquia
            final_id = id_culto if id_culto != '0' else id_paroquia
            if final_id not in ids:
                ids.append(final_id)
                
print(f"Total de {len(ids)} paróquias/locais de culto encontrados!")

# Agora baixar os detalhes de cada um
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Paróquias da Arquidiocese de São Sebastião do Rio de Janeiro\n\n")
    
    for i, pid in enumerate(ids):
        print(f"Baixando detalhes do ID {pid} ({i+1}/{len(ids)})...")
        detail_url = f'https://www.arqrio.com.br/curia/ajaxParoquiasRecuperarDetalhes.php?id={pid}'
        try:
            r = requests.get(detail_url, verify=False, timeout=10)
            
            html_content = r.text
            
            # Limpar html
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            
            # Escrever no MD
            f.write(text + "\n\n")
            time.sleep(0.1) # Pausa amigável
        except Exception as e:
            print(f"Erro ao baixar ID {pid}: {e}")

print("\nProcesso finalizado com sucesso! Arquivo MD gerado na pasta de importação.")
