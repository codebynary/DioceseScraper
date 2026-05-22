# Status Atual do Desenvolvimento & Instruções para Continuação

Este arquivo serve para registrar o progresso e o estado atual da ferramenta para que possamos continuar o desenvolvimento a partir de outro computador sem perder o contexto.

---

## 🛠️ O que foi feito até agora
Implementamos suporte completo para scraping dinâmico em portais baseados no CMS **SitExpresso** (ex: Arquidiocese de Chapecó):
1. **Detecção Automática**: O backend detecta assinaturas do SitExpresso (`sx.check`, `window.sxid`) nas páginas de listagem.
2. **Requisições AJAX**:
   - Para listagem: Usa requisições dinâmicas `/?ajax=get&path={path}`.
   - Para detalhes: Extrai o valor codificado em base64 do atributo `component` de cada item e constrói a URL de detalhe `/?ajax=get&comp={component}`.
3. **Robustez no Parser (`core/scraper.py`)**:
   - Tratamos erros onde `headings_selector` resolvia para `None` devido a campos retornados como nulos na análise do Gemini.
   - Normalizamos a lista de rótulos (`labels`) para evitar erros do tipo `'NoneType' object is not iterable`.
4. **Resiliência na API do Gemini (`core/agent.py`)**:
   - Adicionamos um loop de até **5 retentativas com recuo exponencial** (*exponential backoff*) quando ocorrem erros temporários de sobrecarga da API do Gemini (`503 UNAVAILABLE`).

---

## ⚠️ Estado Atual & Próximo Passo
Fizemos commits de todo o código atualizado e demos push para a branch `main`.

No último teste realizado na interface web local, a análise inteligente do portal de Chapecó retornou:
> *"A inteligência artificial falhou em mapear os seletores para este site."*

**Motivo:** A API do Gemini 2.5 Flash estava sob altíssima demanda nos servidores da Google, retornando erro `503 UNAVAILABLE` sucessivamente (mesmo após todas as 5 tentativas com atraso). 

### 🚀 O que fazer para continuar no outro computador:
1. **Clonar/Atualizar o Código**:
   ```bash
   git pull origin main
   ```
2. **Ativar o Ambiente Virtual e Rodar o Servidor**:
   ```powershell
   .\venv\Scripts\python.exe run.py
   ```
3. **Testar novamente a Análise**:
   - Abra a página local no navegador: `http://127.0.0.1:5000/`.
   - Adicione a diocese: **Arquidiocese Chapecó** com a URL `https://arquidiocesechapeco.com.br/paroquias`.
   - Clique em **"Iniciar Análise Inteligente"**.
   - Assim que a sobrecarga temporária da API do Gemini passar, ele gerará a configuração com sucesso.
4. **Revisar Detalhes Coletados**:
   - Valide se a paróquia de teste carrega os dados corretamente. Como o SitExpresso renderiza todas as informações de contato em um único bloco de texto de forma compacta (ex: `Endereço: ... Telefone: ... E-mail: ...`), pode ser necessário conferir se a IA capturou os dados nos campos correspondentes ou se usou a estrutura de texto corrido.
5. **Executar Extração Completa**:
   - Após salvar a configuração, inicie a extração e verifique se as 46 paróquias da listagem de Chapecó são raspadas com sucesso.
