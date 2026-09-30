# Imagem base oficial do Python
FROM python:3.11-slim

# Evita geração de bytecode .pyc e força flush imediato de logs no stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

WORKDIR /app

# Instala dependências do sistema necessárias para compilação de pacotes C/C++ se houver
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte e configurações
COPY src/ /app/src/
COPY config/ /app/config/

# Ponto de entrada padrão para o Servidor FastAPI (Cloud Run ou local)
ENV PORT=8000
EXPOSE 8000
CMD ["python", "src/server.py"]
