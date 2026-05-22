# Diocese Scraper ⛪🤖

O **Diocese Scraper** é uma ferramenta inteligente e automatizada para a extração de dados de paróquias (como clero, telefones, e-mails, horários de missas, redes sociais e imagens) de múltiplos sites de dioceses e arquidioceses brasileiras. 

A aplicação utiliza a inteligência artificial do **Gemini 2.5** para analisar dinamicamente a estrutura de qualquer site de diocese informado, gerando e testando as regras de extração automaticamente em uma interface web interativa de alta fidelidade (Modo Escuro / Glassmorphism).

---

## 🌟 Funcionalidades

1. **Análise de Estrutura por IA**: Digite a URL de listagem de paróquias de qualquer diocese e o Gemini gera automaticamente a configuração de raspagem (com seletores CSS e rotas de paginação).
2. **Visualização de Teste**: Revise uma paróquia de teste simulada e edite o JSON de configuração diretamente na interface antes de rodar o processo completo.
3. **Logs em Tempo Real**: Acompanhe o processo de raspagem através de um console integrado na tela com streaming de logs ao vivo (via Server-Sent Events).
4. **Dashboard de Paróquias**: Visualize os dados coletados em uma tabela premium e faça buscas/filtros rápidos em tempo real.
5. **Persistência de Dados**: Os dados são organizados e salvos localmente na pasta `dados/<nome-diocese>/paroquias.json` e as configurações em `configs/`.

---

## 🚀 Como Rodar Localmente

### Pré-requisitos
* Python 3.10 ou superior instalado.

### Passo a Passo

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/codebynary/DioceseScraper.git
   cd DioceseScraper
   ```

2. **Crie e ative o ambiente virtual**:
   * No Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * No Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o painel**:
   ```bash
   python run.py
   ```
   *O navegador deve abrir automaticamente no endereço: `http://127.0.0.1:5000/`.*

---

## 🐳 Implantação em Produção (Coolify / Docker)

Esta aplicação está totalmente preparada para ser publicada em servidores como o **Coolify** ou qualquer ambiente que suporte Docker.

### Passos no Coolify:

1. Adicione a sua aplicação no painel apontando para o seu repositório Git.
2. O Coolify detectará automaticamente o arquivo `Dockerfile` na raiz e configurará o build.
3. **Importante (Persistência)**: Na aba **Storage / Volumes**, crie os seguintes mapeamentos para garantir que seus dados e configurações não sejam apagados caso o container reinicie:
   * `diocese-scraper-configs:/app/configs`
   * `diocese-scraper-dados:/app/dados`
4. **Configuração da Chave da API**: Se desejar, adicione a variável de ambiente `GEMINI_API_KEY` diretamente nas configurações de variáveis do Coolify.

---

## 🛠️ Tecnologias Utilizadas

* **Backend**: Python, Flask, Beautiful Soup 4, Requests, Python-dotenv.
* **Inteligência Artificial**: Google GenAI SDK (`gemini-2.5-flash`).
* **Frontend**: HTML5 Semântico, CSS3 (Vanilla com Glassmorphism), JavaScript Vanilla (SSE para logs em tempo real).
* **Produção**: Docker & Gunicorn.
