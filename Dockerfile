FROM python:3.11-slim

# Evita que o Python escreva arquivos .pyc e bufferize a saída do log
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Força Playwright a usar Chromium instalado internamente
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Instala dependências do sistema (inclui libs necessárias para o Chromium do Playwright)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    # Dependências do Chromium/Playwright
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala o Chromium do Playwright (sem outros browsers para economizar espaço)
RUN playwright install chromium

# Copia o código da aplicação
COPY . .

# Expõe a porta que o Coolify usará para o tráfego externo
EXPOSE 5000

# Executa com o Gunicorn (servidor WSGI estável de produção)
# Timeout aumentado para 300s pois sites Wix/SPA demoram mais para renderizar
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "app.server:app"]
