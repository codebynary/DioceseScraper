# Diocese Scraper & OmniEcclesia Dashboard

Este projeto é uma ferramenta completa baseada em Inteligência Artificial para realizar a varredura (scraping), extração e curadoria de dados de paróquias em sites institucionais de arquidioceses e dioceses católicas.

Foi projetado para rodar localmente e em ambientes de produção (como o **Coolify** e **Docker**) e integra-se diretamente à API do **Google Gemini** para entender o layout visual e o DOM dos sites-alvo automaticamente.

## 🚀 Funcionalidades Principais

*   **Scraping Inteligente (IA Vision)**: Em vez de depender de seletores CSS fixos, o sistema utiliza a API do Gemini para ler a estrutura HTML de qualquer site de diocese, identificando automaticamente como extrair "Nome", "Endereço", "Pároco", "Telefone", etc.
*   **Apoio a Sites Dinâmicos (SitExpresso)**: O sistema detecta e lida com sites construídos na plataforma SitExpresso que carregam conteúdo via chamadas AJAX pesadas.
*   **Curadoria Integrada e Enriquecimento**: Painel web limpo para que um humano revise os dados extraídos. Inclui consultas automáticas às APIs ViaCEP, BrasilAPI e AwesomeAPI para cruzar endereços e completar CEPs faltantes.
*   **Gestão de Arquivos Markdown**: O sistema permite a importação em lote de dados já pré-processados em formato Markdown.
*   **Exportação JSON (Persistente)**: Geração de arquivos JSON finais estruturados prontos para alimentar bancos de dados ou frontends de aplicativos.

## 🛠️ Stack Tecnológica

*   **Backend**: Python, Flask, Gunicorn.
*   **Web Scraping**: BeautifulSoup4, Requests.
*   **Inteligência Artificial**: Google GenAI SDK (`google-genai`), modelo `gemini-2.5-flash`.
*   **Frontend**: HTML5, CSS Vanilla (variáveis e Glassmorphism), Javascript (Fetch API / SSE).

## 📦 Implantação (Deployment no Coolify / Docker)

A aplicação já conta com o arquivo `Dockerfile` e dependências listadas no `requirements.txt`. Para colocá-la em produção no **Coolify**:

1. Adicione o repositório GitHub ao Coolify e escolha o Nixpacks ou Dockerfile.
2. Certifique-se de que a porta exposta é a `5000`.
3. **MUITO IMPORTANTE - Volumes:** Você deve criar montagens persistentes (*Storage Mappings*) para duas pastas, caso contrário seus dados serão apagados a cada deploy:
    *   `/app/configs` -> Onde o sistema armazena a chave de API e as regras geradas pela IA.
    *   `/app/dados` -> Onde ficam armazenadas as extrações cruas, os uploads de Markdown e os arquivos JSON finais curados.

## ⚙️ Como executar localmente

1. Clone o repositório.
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente: `venv\Scripts\activate` (Windows) ou `source venv/bin/activate` (Linux/Mac)
4. Instale as dependências: `pip install -r requirements.txt`
5. Inicie o servidor: `python run.py` ou `python app/server.py`
6. Acesse via navegador em: `http://localhost:5000`

Na interface, insira a sua Chave de API do Google Gemini para desbloquear as funções de inteligência artificial.

## 🗂 Estrutura de Diretórios
* `/app`: Código-fonte da aplicação Web Flask (Server, Templates, Static).
* `/configs`: Arquivos JSON com seletores CSS extraídos pela IA. (Requer Persistência)
* `/core`: Motor de análise de IA, parser markdown, gerenciamento de configs e funções de scrap.
* `/dados`: Arquivos `.json` de cada diocese extraída e arquivos `.md` importados. (Requer Persistência)
