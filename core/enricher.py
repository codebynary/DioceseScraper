import re
import datetime
import urllib.parse

def parse_endereco(original, diocese_name=""):
    """
    Parses a Brazilian address text into structured components:
    logradouro, numero, complemento, bairro, cidade, uf, cep, pais.
    Assigns confidence rating (HIGH, MEDIUM, LOW).
    """
    if not original:
        return {
            "original": "",
            "logradouro": "",
            "numero": "",
            "complemento": "",
            "bairro": "",
            "cidade": "",
            "uf": "",
            "cep": "",
            "pais": "Brasil",
            "confidence": "LOW"
        }
        
    original = str(original).strip()
    
    addr = {
        "original": original,
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cidade": "",
        "uf": "",
        "cep": "",
        "pais": "Brasil",
        "confidence": "LOW"
    }
    
    # 1. Extract CEP
    cep_match = re.search(r'\b(\d{5}-\d{3})\b|\b(\d{8})\b', original)
    if cep_match:
        addr["cep"] = cep_match.group(0)
        temp_addr = original.replace(cep_match.group(0), "").strip()
    else:
        temp_addr = original
        
    # Clean up trailing/leading separators
    temp_addr = re.sub(r'^[,\-\s\./:]+|[,\-\s\./:]+$', '', temp_addr).strip()
    
    # 2. Extract UF
    states = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", 
              "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
    uf_pattern = r'\b(' + '|'.join(states) + r')\b'
    uf_match = list(re.finditer(uf_pattern, temp_addr, re.IGNORECASE))
    if uf_match:
        last_match = uf_match[-1]
        addr["uf"] = last_match.group(1).upper()
        before_uf = temp_addr[:last_match.start()].strip()
        before_uf = re.sub(r'[,\-\s\./:]+$', '', before_uf).strip()
    else:
        before_uf = temp_addr
        
    # 3. Clean prefixes like MATRIZ:
    matriz_match = re.match(r'^(matriz|capela|quase-paróquia|santuário)\s*[:\-]\s*', before_uf, re.IGNORECASE)
    if matriz_match:
        addr["complemento"] = matriz_match.group(1).capitalize()
        before_uf = before_uf[matriz_match.end():].strip()
        
    # 4. Split by commas to find logradouro, number, and others
    parts = [p.strip() for p in re.split(r',', before_uf) if p.strip()]
    
    if len(parts) >= 1:
        log_candidate = parts[0]
        num_found = False
        
        # Check if second part starts with a number
        if len(parts) >= 2:
            next_part = parts[1]
            num_match = re.match(r'^(?:n[º°ª]\s*|n[o0]\s*|número\s*|numero\s*)?(\d+[\w\-]*)\b|^(s/n|s/nº)\b', next_part, re.IGNORECASE)
            if num_match:
                addr["numero"] = num_match.group(0).strip()
                parts[1] = next_part[num_match.end():].strip()
                parts[1] = re.sub(r'^[,\-\s\./:]+|[,\-\s\./:]+$', '', parts[1]).strip()
                num_found = True
                
        # Fallback: check if log_candidate itself is purely numeric or s/n
        if not num_found:
            pure_num_match = re.match(r'^(?:\d+[\w\-]*)$|^(s/n|s/nº)$', log_candidate, re.IGNORECASE)
            if pure_num_match:
                addr["numero"] = log_candidate
                log_candidate = ""
                num_found = True
                
        # Fallback: check if log_candidate ends with a number/sn
        if not num_found:
            end_num_match = re.search(r'\s+(\d+[\w\-]*)$|\s+(s/n|s/nº)$', log_candidate, re.IGNORECASE)
            if end_num_match:
                addr["numero"] = end_num_match.group(1) or end_num_match.group(2)
                log_candidate = log_candidate[:end_num_match.start()].strip()
                
        addr["logradouro"] = log_candidate
        
    # Re-evaluate remaining parts for Bairro and Cidade
    remaining_parts = []
    for p in parts[1:]:
        subparts = [sp.strip() for sp in re.split(r'\s+-\s+', p) if sp.strip()]
        remaining_parts.extend(subparts)
        
    remaining_parts = [rp for rp in remaining_parts if rp]
    
    if len(remaining_parts) == 1:
        addr["cidade"] = remaining_parts[0]
    elif len(remaining_parts) == 2:
        addr["bairro"] = remaining_parts[0]
        addr["cidade"] = remaining_parts[1]
    elif len(remaining_parts) > 2:
        addr["bairro"] = remaining_parts[0]
        addr["cidade"] = remaining_parts[-1]
        addr["complemento"] = (addr["complemento"] + ", " if addr["complemento"] else "") + ", ".join(remaining_parts[1:-1])
        
    # Clean up fields
    for k in ["logradouro", "bairro", "cidade", "complemento"]:
        addr[k] = re.sub(r'^[,\-\s\./:]+|[,\-\s\./:]+$', '', addr[k]).strip()
        
    # ViaCEP Integration for Enrichment
    if addr["cep"]:
        cep_clean = re.sub(r'\D', '', addr["cep"])
        if len(cep_clean) == 8:
            try:
                import requests
                response = requests.get(f"https://viacep.com.br/ws/{cep_clean}/json/", timeout=5)
                if response.status_code == 200:
                    viacep_data = response.json()
                    if "erro" not in viacep_data:
                        # Overwrite with official data ONLY if the field is currently empty
                        log_via = viacep_data.get("logradouro", "")
                        if log_via and not addr["logradouro"]:
                            addr["logradouro"] = log_via
                            
                        bairro_via = viacep_data.get("bairro", "")
                        if bairro_via and not addr["bairro"]:
                            addr["bairro"] = bairro_via
                            
                        cidade_via = viacep_data.get("localidade", "")
                        if cidade_via and not addr["cidade"]:
                            addr["cidade"] = cidade_via
                            
                        uf_via = viacep_data.get("uf", "")
                        if uf_via and not addr["uf"]:
                            addr["uf"] = uf_via
            except Exception as e:
                print(f"ViaCEP Error for {cep_clean}: {e}")
                
    # Fallback to Diocese Name if ViaCEP failed and string was incomplete
    if diocese_name and (not addr["cidade"] or not addr["uf"]):
        uf_match = re.search(r'\b([A-Z]{2})\b$', diocese_name)
        fallback_uf = uf_match.group(1) if uf_match else ''
        city_match = re.search(r'(?:Diocese|Arquidiocese|Prelazia|Ordinariado Militar|Eparquia)(?: do| da| de)? (.+?)(?:\s*(?:-|–)?\s*[A-Z]{2})?$', diocese_name)
        fallback_cidade = city_match.group(1).strip() if city_match else ''
        fallback_cidade = re.sub(r'\s+[A-Z]{2}$', '', fallback_cidade).strip()
        
        if not addr["cidade"] and fallback_cidade:
            addr["cidade"] = fallback_cidade
        if not addr["uf"] and fallback_uf:
            addr["uf"] = fallback_uf

    # Set Confidence
    if addr["logradouro"] and addr["cidade"] and addr["uf"]:
        addr["confidence"] = "HIGH"
    elif addr["cidade"] and addr["uf"]:
        addr["confidence"] = "MEDIUM"
    else:
        addr["confidence"] = "LOW"
        
    return addr

def parse_telefones(original_tel):
    """
    Splits multiple phone numbers and formats them. Identifies WhatsApp.
    """
    if not original_tel:
        return []
        
    # Split by separators
    parts = re.split(r'[\n;,/]+| ou |\s*\|\s*', str(original_tel))
    telefones = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        is_whatsapp = False
        if any(w in part.lower() for w in ["whats", "wpp", "whatsapp", "celular", "whats:", "whatsapp:"]):
            is_whatsapp = True
            
        # Clean text descriptions
        clean_val = re.sub(r'(?i)whats(app)?|wpp|celular|fone|tel|ou|contato', '', part).strip()
        clean_val = re.sub(r'\(\s*\)|\[\s*\]|\{\s*\}', '', clean_val).strip()
        clean_val = re.sub(r'^[^\d+(]+|[^\d)]+$', '', clean_val).strip()
        
        digits = re.sub(r'\D', '', clean_val)
        if len(digits) >= 8:
            telefones.append({
                "tipo": "celular" if (len(digits) >= 11 or is_whatsapp) else "fixo",
                "valor": clean_val,
                "rotulo": "WhatsApp" if is_whatsapp else "Telefone",
                "whatsapp": is_whatsapp
            })
            
    return telefones

def parse_emails(original_email):
    """
    Extracts valid email addresses from text.
    """
    if not original_email:
        return []
        
    email_pattern = r'[\w.\-]+@[\w.\-]+\.\w+'
    matches = re.findall(email_pattern, str(original_email))
    
    emails = []
    for match in matches:
        emails.append({
            "valor": match.strip(),
            "rotulo": "E-mail"
        })
    return emails

def parse_clero(original_clero):
    """
    Parses clergy block into title, name, cargo, and original line.
    """
    if not original_clero:
        return []
        
    lines = [line.strip() for line in str(original_clero).split('\n') if line.strip()]
    clero_list = []
    
    titulos = ["Pe", "Padre", "Dom", "Frei", "Ir", "Diác", "Diácono", "Côn", "Cônego", "Mons", "Monsenhor", "Seminarista"]
    cargos = ["Pároco", "Vigário", "Administrador Paroquial", "Reitor", "Bispo", "Arcebispo", "Diácono", "Colaborador", "Residente"]
    
    titulos_esc = [re.escape(t) for t in titulos]
    cargos_esc = [re.escape(c) for c in cargos]
    
    for line in lines:
        member = {
            "nome": "",
            "titulo": "",
            "cargo": "",
            "texto_original": line
        }
        
        # 1. Detect title
        title_pattern = r'^(' + '|'.join(titulos_esc) + r')\b\.?'
        title_match = re.match(title_pattern, line, re.IGNORECASE)
        name_part = line
        if title_match:
            member["titulo"] = title_match.group(0)
            name_part = line[title_match.end():].strip()
            
        # 2. Detect cargo
        cargo_pattern = r'\b(' + '|'.join(cargos_esc) + r')\b'
        cargo_match = list(re.finditer(cargo_pattern, name_part, re.IGNORECASE))
        
        if cargo_match:
            last_match = cargo_match[-1]
            member["cargo"] = last_match.group(1)
            name_part = name_part[:last_match.start()].strip()
            name_part = re.sub(r'^[,\-\s\./:]+|[,\-\s\./:]+$', '', name_part).strip()
        else:
            # Full phrases search
            for c_full in ["Vigário Paroquial", "Vigário Cooperador", "Administrador Paroquial", "Diácono Transitório", "Diácono Permanente"]:
                if c_full.lower() in name_part.lower():
                    member["cargo"] = c_full
                    name_part = re.sub(r'(?i)' + re.escape(c_full), '', name_part).strip()
                    name_part = re.sub(r'^[,\-\s\./:]+|[,\-\s\./:]+$', '', name_part).strip()
                    break
                    
        member["nome"] = name_part
        clero_list.append(member)
        
    return clero_list

def parse_horarios_missa(texto_original):
    """
    Parses a textual mass times block into structured elements.
    """
    if not texto_original:
        return []
        
    lines = [l.strip() for l in str(texto_original).split('\n') if l.strip()]
    horarios_list = []
    
    dias_canonicos = {
        "segunda": "Segunda-feira",
        "terça": "Terça-feira",
        "quarta": "Quarta-feira",
        "quinta": "Quinta-feira",
        "sexta": "Sexta-feira",
        "sábado": "Sábado",
        "sabado": "Sábado",
        "domingo": "Domingo"
    }
    
    time_pattern = r'\b(?:[0-2]?\d[h:]\d{2}|[0-2]?\d\s*h\b)'
    current_tipo = "Missa"
    
    for line in lines:
        times_found = re.findall(time_pattern, line, re.IGNORECASE)
        
        dias_encontrados = []
        line_lower = line.lower()
        for d_key, d_canon in dias_canonicos.items():
            if d_key in line_lower:
                dias_encontrados.append(d_canon)
                
        if not times_found and not dias_encontrados:
            if len(line) < 40 and not any(k in line_lower for k in ["rua", "av.", "telefone", "cep"]):
                current_tipo = line.replace(":", "").strip()
            continue
            
        clean_times = []
        for t in times_found:
            t_clean = t.lower().replace(" ", "").replace("h", ":")
            if t_clean.endswith(":"):
                t_clean += "00"
            parts = t_clean.split(":")
            if len(parts) == 2:
                try:
                    h = int(parts[0])
                    m = int(parts[1])
                    clean_times.append(f"{h:02d}:{m:02d}")
                except:
                    pass
                    
        # Check range "Segunda a Sexta"
        if " a " in line_lower or " à " in line_lower or " às " in line_lower:
            if len(dias_encontrados) >= 2:
                ordem_dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
                try:
                    d_start = dias_encontrados[0]
                    d_end = dias_encontrados[1]
                    idx_start = ordem_dias.index(d_start)
                    idx_end = ordem_dias.index(d_end)
                    if idx_start < idx_end:
                        dias_encontrados = ordem_dias[idx_start:idx_end+1]
                except:
                    pass
                    
        if dias_encontrados or clean_times:
            horarios_list.append({
                "tipo": current_tipo,
                "dias_semana": dias_encontrados,
                "horarios": clean_times,
                "local": "",
                "observacoes": line,
                "texto_original": line
            })
            
    return horarios_list

def parse_secretaria(original_sec):
    """
    Parses office hours into days and times.
    """
    if not original_sec:
        return {
            "texto_original": "",
            "dias": [],
            "horarios": []
        }
        
    original_sec = str(original_sec).strip()
    
    dias_canonicos = {
        "segunda": "Segunda-feira",
        "terça": "Terça-feira",
        "quarta": "Quarta-feira",
        "quinta": "Quinta-feira",
        "sexta": "Sexta-feira",
        "sábado": "Sábado",
        "sabado": "Sábado",
        "domingo": "Domingo"
    }
    
    dias = []
    line_lower = original_sec.lower()
    for d_key, d_canon in dias_canonicos.items():
        if d_key in line_lower:
            dias.append(d_canon)
            
    if " a " in line_lower or " à " in line_lower or " às " in line_lower:
        if len(dias) >= 2:
            ordem_dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
            try:
                idx_start = ordem_dias.index(dias[0])
                idx_end = ordem_dias.index(dias[1])
                if idx_start < idx_end:
                    dias = ordem_dias[idx_start:idx_end+1]
            except:
                pass
                
    time_pattern = r'\b(?:[0-2]?\d[h:]\d{2}|[0-2]?\d\s*h\b)'
    times_found = re.findall(time_pattern, original_sec, re.IGNORECASE)
    
    clean_times = []
    for t in times_found:
        t_clean = t.lower().replace(" ", "").replace("h", ":")
        if t_clean.endswith(":"):
            t_clean += "00"
        parts = t_clean.split(":")
        if len(parts) == 2:
            try:
                h = int(parts[0])
                m = int(parts[1])
                clean_times.append(f"{h:02d}:{m:02d}")
            except:
                pass
                
    return {
        "texto_original": original_sec,
        "dias": list(set(dias)),
        "horarios": clean_times
    }

def parse_redes_sociais(redes, url_base):
    """
    Parses social networks and assigns scopes (paroquia vs diocese).
    """
    parsed_redes = {
        "facebook": {"url": "", "escopo": ""},
        "instagram": {"url": "", "escopo": ""},
        "youtube": {"url": "", "escopo": ""},
        "whatsapp": {"url": "", "telefone": "", "escopo": ""}
    }
    
    if not redes:
        return parsed_redes
        
    diocese_handle_words = ["diocese", "arquidiocese", "mitra", "curia"]
    
    for net, url in redes.items():
        if not url or net not in parsed_redes:
            continue
            
        scope = "paroquia"
        url_lower = url.lower()
        
        parsed_url = urllib.parse.urlparse(url)
        path_parts = [p for p in parsed_url.path.split('/') if p]
        
        if path_parts:
            handle = path_parts[0].lower()
            if any(w in handle for w in diocese_handle_words) and not any(w in url_lower for w in ["paroquia", "comunidade", "santuario"]):
                scope = "diocese"
                
        if net == "whatsapp":
            num_match = re.search(r'\d+', url)
            tel_num = num_match.group(0) if num_match else ""
            parsed_redes[net] = {
                "url": url,
                "telefone": tel_num,
                "escopo": scope
            }
        else:
            parsed_redes[net] = {
                "url": url,
                "escopo": scope
            }
            
    return parsed_redes

def enrich_parish(p, nome_diocese, url_base):
    """
    Enriches a flat parish record into a structured parish record,
    ensuring backwards compatibility with the original flat keys.
    """
    nome = p.get("nome", "")
    url = p.get("url", "")
    img = p.get("imagem_thumbnail", "")
    
    # 1. Guess type
    tipo = "Paróquia"
    nome_lower = nome.lower()
    if "quase-paróquia" in nome_lower or "quase paróquia" in nome_lower:
        tipo = "Quase-Paróquia"
    elif "santuário" in nome_lower:
        tipo = "Santuário"
    elif "reitoria" in nome_lower:
        tipo = "Reitoria"
    elif "capela" in nome_lower:
        tipo = "Capela"
    elif "catedral" in nome_lower:
        tipo = "Catedral"
    elif "basílica" in nome_lower:
        tipo = "Basílica"
        
    # 2. Fonte
    fonte = p.get("fonte") or {
        "tipo": "site_diocese",
        "nome": nome_diocese,
        "url": url_base,
        "data_coleta": datetime.datetime.now().isoformat(),
        "metodo": "scraper_ia"
    }
    
    # 3. Endereco
    endereco_raw = p.get("endereco", "")
    if isinstance(endereco_raw, dict):
        endereco_struct = endereco_raw
        endereco_flat = p.get("endereco_original") or ""
        if isinstance(endereco_flat, dict):
            endereco_flat = endereco_flat.get("original", "")
    else:
        endereco_struct = parse_endereco(endereco_raw, diocese_name=nome_diocese)
        endereco_flat = endereco_raw
        
    # 4. Contatos
    contatos = p.get("contatos", {})
    if not contatos:
        telefones = parse_telefones(p.get("telefone", ""))
        emails = parse_emails(p.get("email", ""))
        sites = []
        if url:
            sites.append({
                "valor": url,
                "rotulo": "oficial"
            })
        redes_sociais = parse_redes_sociais(p.get("redes_sociais", {}), url_base)
        
        contatos = {
            "telefones": telefones,
            "emails": emails,
            "sites": sites,
            "redes_sociais": redes_sociais
        }
        
    # 5. Clero
    clero_raw = p.get("clero", "")
    if isinstance(clero_raw, list):
        clero_struct = clero_raw
        clero_flat = p.get("clero_original") or ""
    else:
        clero_struct = parse_clero(clero_raw)
        clero_flat = clero_raw
        
    # 6. Horarios de Missa
    missa_raw = p.get("horarios_missa_texto", "")
    if isinstance(p.get("horarios_missa"), list):
        missa_struct = p.get("horarios_missa")
        missa_flat = p.get("horarios_missa_texto") or ""
    else:
        missa_struct = parse_horarios_missa(missa_raw)
        missa_flat = missa_raw
        
    # 7. Funcionamento Secretaria
    sec_raw = p.get("funcionamento_secretaria", "")
    if isinstance(sec_raw, dict):
        sec_struct = sec_raw
        sec_flat = p.get("funcionamento_secretaria_original") or ""
    else:
        sec_struct = parse_secretaria(sec_raw)
        sec_flat = sec_raw
        
    # 8. Estrutura Pastoral
    setor = p.get("setor", "")
    estrutura_pastoral = p.get("estrutura_pastoral") or {
        "setor": setor,
        "forania": "",
        "regiao": "",
        "texto_original": f"Setor: {setor}" if setor else ""
    }
    
    # 9. Observacoes
    observacoes = p.get("observacoes", "")
    
    # 10. Raw payload preserve
    raw_payload = p.get("raw") or {
        "nome": nome,
        "endereco": endereco_flat,
        "telefone": p.get("telefone", ""),
        "email": p.get("email", ""),
        "clero": clero_flat,
        "horarios_missa_texto": missa_flat,
        "funcionamento_secretaria": sec_flat,
        "setor": setor,
        "redes_sociais": p.get("redes_sociais", {})
    }
    
    enriched = {
        "nome": nome,
        "tipo": tipo,
        "url": url,
        "imagem_thumbnail": img,
        "fonte": fonte,
        "endereco": endereco_struct,
        "contatos": contatos,
        "clero": clero_struct,
        "horarios_missa": missa_struct,
        "horarios_missa_texto_original": missa_flat,
        "funcionamento_secretaria": sec_struct,
        "locais_culto": p.get("locais_culto", []),
        "estrutura_pastoral": estrutura_pastoral,
        "observacoes": observacoes,
        "raw": raw_payload,
        
        # Meta flags
        "status": p.get("status", "ativo"),
        "curado": p.get("curado", False),
        "data_criacao": p.get("data_criacao"),
        "ultima_atualizacao": p.get("ultima_atualizacao"),
        
        # Backward compatibility flat fields
        "endereco_original": endereco_flat,
        "telefone": (contatos["telefones"][0]["valor"] if contatos["telefones"] else ""),
        "email": (contatos["emails"][0]["valor"] if contatos["emails"] else ""),
        "clero_original": clero_flat,
        "horarios_missa_texto": missa_flat,
        "funcionamento_secretaria_original": sec_flat,
        "setor": setor
    }
    
    return enriched

def generate_enrichment_report(diocese_name, parishes):
    """
    Computes quality and quantitative validation stats for scraped parishes.
    """
    total = len(parishes)
    if total == 0:
        return "Nenhum registro para validar."
        
    e_high = 0
    e_med = 0
    e_low = 0
    tels_count = 0
    emails_count = 0
    clero_count = 0
    missas_count = 0
    
    for p in parishes:
        # Address confidence
        conf = p.get("endereco", {}).get("confidence", "LOW")
        if conf == "HIGH":
            e_high += 1
        elif conf == "MEDIUM":
            e_med += 1
        else:
            e_low += 1
            
        tels_count += len(p.get("contatos", {}).get("telefones", []))
        emails_count += len(p.get("contatos", {}).get("emails", []))
        clero_count += len(p.get("clero", []))
        missas_count += len(p.get("horarios_missa", []))
        
    report = (
        f"\n==================================================\n"
        f"        RELATÓRIO DE ENRIQUECIMENTO PAROQUIAL       \n"
        f"==================================================\n"
        f"Diocese: {diocese_name}\n"
        f"Total de Paróquias: {total}\n"
        f"--------------------------------------------------\n"
        f"Qualidade do Endereço:\n"
        f"  - Confiança ALTA (HIGH): {e_high} ({round(e_high/total*100, 1)}%)\n"
        f"  - Confiança MÉDIA (MEDIUM): {e_med} ({round(e_med/total*100, 1)}%)\n"
        f"  - Confiança BAIXA (LOW): {e_low} ({round(e_low/total*100, 1)}%)\n"
        f"--------------------------------------------------\n"
        f"Métricas Quantitativas:\n"
        f"  - Telefones extraídos: {tels_count}\n"
        f"  - E-mails extraídos: {emails_count}\n"
        f"  - Clérigos catalogados: {clero_count}\n"
        f"  - Horários de missa estruturados: {missas_count}\n"
        f"=================================================="
    )
    return report
