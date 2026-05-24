import re
import os
from core import enricher

def parse_markdown_file(filepath):
    filename = os.path.basename(filepath)
    # Extrai o nome da diocese limpando os prefixos padrão
    diocese_name = filename.replace("Paroquias da ", "").replace("Paroquias ", "") \
                           .replace("Paróquias da ", "").replace("Paróquias e Áreas Missionárias ", "") \
                           .replace("Paróquias ", "").replace("Clero da ", "") \
                           .replace(".md", "").replace(" - sem endereço", "").strip()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    parishes = []
    current_parish = None
    
    current_setor = None
    current_responsavel = None
    
    # Prefixos que indicam o título de uma paróquia ou estrutura religiosa
    parish_prefixes = r'^(Paróquia|Quase-Paróquia|Área Missionária|Área Pastoral|Santuário|Catedral|Basílica|Reitoria|Capelania|Comunidade|Nossa Senhora do Perpétuo Socorro)'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Pular linhas de cabeçalho 
        lower_line = line.lower()
        if lower_line.startswith('link para') or lower_line.startswith('telefone das'):
            continue
            
        # Identificar Foranias/Zonais e salvar o contexto
        if lower_line.startswith('zonal') or 'forania' in lower_line or \
           lower_line.startswith('setor') or lower_line.startswith('vicariato'):
            current_setor = line
            continue
            
        if lower_line.startswith('vigário forâneo') or lower_line.startswith('responsável forânico') or lower_line.startswith('vigario foraneo'):
            current_responsavel = line
            continue
            
        is_title = False
        # Checa se bate com os prefixos de igreja
        if re.match(parish_prefixes, line, re.IGNORECASE):
            is_title = True
        
        if is_title:
            # Se a paróquia atual não tem NENHUM dado preenchido ainda, essa linha de título pode ser só um subtítulo
            has_data = current_parish and (current_parish['endereco'] or current_parish['telefone'] or current_parish['email'] or current_parish['clero'])
            if current_parish and not has_data:
                current_parish['nome'] += " - " + line
                continue
                
            # Salva a paróquia anterior
            if current_parish:
                parishes.append(current_parish)
                
            # Inicia uma nova
            current_parish = {
                'nome': line,
                'endereco': '',
                'telefone': '',
                'email': '',
                'clero': '',
                'redes_sociais': {},
                'horarios_missa_texto': '',
                'funcionamento_secretaria': '',
                'setor': current_setor,
                'observacoes': current_responsavel if current_responsavel else '',
                'in_locais': False,
                'locais_culto_raw_lines': []
            }
            continue
            
        # Se encontrou dados após o título, começa a tentar adivinhar qual é o campo
        if current_parish:
            if lower_line == 'locais de culto':
                current_parish['in_locais'] = True
                continue
                
            if current_parish.get('in_locais'):
                current_parish['locais_culto_raw_lines'].append(line)
                continue
                
            if 'whatsapp' in lower_line or 'telefone' in lower_line or 'celular' in lower_line or 'fone' in lower_line or re.search(r'\(\d{2}\)', line):
                current_parish['telefone'] += line + " | "
            elif 'email' in lower_line or 'e-mail' in lower_line or ('@' in lower_line and 'instagram' not in lower_line):
                current_parish['email'] += line + " | "
            elif 'padre' in lower_line or 'pároco' in lower_line or 'diácono' in lower_line or 'vigário' in lower_line or 'clero' in lower_line or 'pe.' in lower_line:
                current_parish['clero'] += line + " | "
            elif 'endereço' in lower_line or 'rua ' in lower_line or 'avenida ' in lower_line or 'av.' in lower_line or 'cep' in lower_line or 'praça' in lower_line or 'estrada' in lower_line or 'largo ' in lower_line:
                current_parish['endereco'] += line + " | "
            elif 'instagram' in lower_line or 'facebook' in lower_line or 'youtube' in lower_line:
                pass # Redes sociais podem ser complexas
            elif 'código' in lower_line or 'data de criação' in lower_line or 'data de  criação' in lower_line:
                current_parish['observacoes'] += line + " | "
            else:
                # O que sobrar e não conseguirmos identificar vai para observações,
                # ou podemos supor que é a continuação do endereço.
                if len(line) > 5:
                    if re.search(r'\d{4,}', line) or 'rio de janeiro' in lower_line or 'rj' in lower_line:
                        current_parish['endereco'] += line + " | "
                    else:
                        current_parish['observacoes'] += line + " | "
                
    if current_parish:
        parishes.append(current_parish)
        
    print(f"[{diocese_name}] {len(parishes)} registros brutos encontrados.")
    
    enriched_results = []
    for idx, p in enumerate(parishes):
        # Limpa os " | " que sobram no final
        for k in ['endereco', 'telefone', 'email', 'clero']:
            if isinstance(p[k], str):
                p[k] = p[k].strip(" |").strip()
                if not p[k]:
                    p[k] = None
                    
        # Parse Locais de Culto
        raw_lines = p.get('locais_culto_raw_lines', [])
        locais = []
        current_local = None
        for l in raw_lines:
            l_lower = l.lower()
            if not any(k in l_lower for k in ['rua ', 'av.', 'avenida', 'cep', 'telefone', 'e-mail', 'email', 'fone', 'praça', 'praca', 'rodovia']) and not re.search(r'\d{4,}', l):
                if current_local:
                    locais.append(current_local)
                current_local = {'nome': l, 'endereco': '', 'telefone': '', 'email': ''}
            elif current_local:
                if 'telefone' in l_lower or 'celular' in l_lower or 'fone' in l_lower:
                    current_local['telefone'] += l + " "
                elif 'email' in l_lower or 'e-mail' in l_lower or '@' in l_lower:
                    current_local['email'] += l + " "
                else:
                    current_local['endereco'] += l + " "
        if current_local:
            locais.append(current_local)
            
        for loc in locais:
            loc['endereco'] = loc['endereco'].strip()
            loc['telefone'] = loc['telefone'].strip()
            loc['email'] = loc['email'].strip()
            
        p['locais_culto'] = locais
        
        # O enrich_parish precisa da url_base, passamos uma genérica
        enriched_p = enricher.enrich_parish(p, diocese_name, f"importacao_md/{filename}")
        enriched_results.append(enriched_p)
        
    return diocese_name, enriched_results
