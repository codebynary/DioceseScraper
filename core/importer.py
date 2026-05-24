import os
from core.md_parser import parse_markdown_file
from core import config_manager

def import_markdown_file(filepath):
    """
    Processa um único arquivo markdown e importa os dados como uma nova configuração de Diocese.
    Retorna uma tupla (sucesso: bool, mensagem: str, dados_config: dict_ou_none)
    """
    filename = os.path.basename(filepath)
    
    try:
        diocese_name, enriched_results = parse_markdown_file(filepath)
        
        if not enriched_results:
            return False, f"Nenhuma paróquia identificada em '{filename}'.", None

        # Gerar uma Configuração vazia/fictícia
        config_data = {
            "nome": diocese_name,
            "url_base": f"importacao_md/{filename}",
            "is_sitexpresso": False,
            "paginacao": {"tipo": "single_page"},
            "observacao": "Paróquias importadas via arquivo Markdown."
        }
        
        # Salva a configuração
        config_manager.save_diocese_config(diocese_name, config_data)
        
        # Salva os dados json curáveis
        config_manager.merge_scraped_data(diocese_name, enriched_results)
        
        return True, f"{len(enriched_results)} registros processados de '{diocese_name}'.", config_data
        
    except Exception as e:
        return False, f"Erro ao processar '{filename}': {str(e)}", None
