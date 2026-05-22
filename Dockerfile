FROM python:3.11-slim

# Evita que o Python escreva arquivos .pyc e bufferize a saída do log
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Expõe a porta que o Coolify usará para o tráfego externo
EXPOSE 5000

# Executa com o Gunicorn (servidor WSGI estável de produção)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app.server:app"]
