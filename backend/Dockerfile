# Use uma imagem Python slim oficial
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Criar diretório para o banco de dados SQLite (se necessário)
RUN mkdir -p /app/data

# Expor a porta (Render usa a variável PORT)
EXPOSE $PORT

# Comando de inicialização
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]