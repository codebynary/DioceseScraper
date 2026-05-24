import os
import re

filepath = r'dados\import_md\Paroquias da Arquidiocese de Feira de Santana BA.md'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
parishes = []
current_parish = None
current_setor = None
current_responsavel = None
parish_prefixes = r'^(Paróquia|Quase-Paróquia|Área Missionária|Área Pastoral|Santuário|Catedral|Basílica|Reitoria|Capelania|Comunidade|Nossa Senhora do Perpétuo Socorro)'

for line in lines:
    line = line.strip()
    if not line: continue
    lower_line = line.lower()
    if lower_line.startswith('link para') or lower_line.startswith('telefone das'): continue
    if lower_line.startswith('zonal') or lower_line.startswith('forania') or lower_line.startswith('setor') or lower_line.startswith('vicariato'):
        current_setor = line
        continue
    if lower_line.startswith('vigário forâneo') or lower_line.startswith('responsável forânico') or lower_line.startswith('vigario foraneo'):
        current_responsavel = line
        continue
        
    is_title = bool(re.match(parish_prefixes, line, re.IGNORECASE))
    if is_title:
        has_data = current_parish and (current_parish['endereco'] or current_parish['telefone'] or current_parish['email'] or current_parish['clero'])
        if current_parish and not has_data:
            current_parish['nome'] += ' - ' + line
            continue
        if current_parish: parishes.append(current_parish)
        current_parish = {'nome': line, 'endereco': '', 'telefone': '', 'email': '', 'clero': '', 'setor': current_setor, 'obs': current_responsavel}
        continue
        
    if current_parish:
        if 'whatsapp' in lower_line or 'telefone' in lower_line or 'celular' in lower_line or 'fone' in lower_line or re.search(r'\(\d{2}\)', line):
            current_parish['telefone'] += line + ' | '
        elif 'email' in lower_line or 'e-mail' in lower_line or ('@' in lower_line and 'instagram' not in lower_line):
            current_parish['email'] += line + ' | '
        elif 'padre' in lower_line or 'pároco' in lower_line or 'diácono' in lower_line or 'vigário' in lower_line or 'clero' in lower_line or 'pe.' in lower_line:
            current_parish['clero'] += line + ' | '
        elif 'endereço' in lower_line or 'rua' in lower_line or 'avenida' in lower_line or 'av.' in lower_line or 'cep' in lower_line or 'praça' in lower_line or 'pç ' in lower_line:
            current_parish['endereco'] += line + ' | '
        else:
            if len(line) > 5:
                current_parish['endereco'] += line + ' | '

if current_parish: parishes.append(current_parish)

erros = 0
for p in parishes:
    print(f"{p['nome']} -> End: {bool(p['endereco'])} | Tel: {bool(p['telefone'])} | Email: {bool(p['email'])}")
    if not p['endereco'] and not p['telefone'] and not p['email']:
        erros += 1

print(f'\nTotal: {len(parishes)} | Paroquias sem NENHUM dado: {erros}')
