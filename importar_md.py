import os
import glob
from core.md_parser import parse_markdown_file
from core import config_manager

def main():
    IMPORT_DIR = os.path.join('dados', 'import_md')
    if not os.path.exists(IMPORT_DIR):
        print(f"Erro: A pasta '{IMPORT_DIR}' não existe.")
        return

    md_files = glob.glob(os.path.join(IMPORT_DIR, '*.md'))
    if not md_files:
        print(f"Nenhum arquivo .md encontrado na pasta '{IMPORT_DIR}'.")
        return

    print(f"Encontrados {len(md_files)} arquivos para importar. Iniciando...\n")

    from core import importer
    for filepath in md_files:
        filename = os.path.basename(filepath)
        print(f"Processando arquivo: {filename}")
        
        success, message, config_data = importer.import_markdown_file(filepath)
        if success:
            print(f"  -> SUCESSO: {message}")
        else:
            print(f"  -> ERRO/AVISO: {message}")
            
    print("\nProcesso de importação finalizado! Abra o seu Painel Web para visualizar os dados.")

if __name__ == '__main__':
    main()
