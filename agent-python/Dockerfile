# Imagem base leve do Python
FROM python:3.12-slim

# Diretório padrão dentro do container
WORKDIR /app

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Instalação das dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia do código-fonte do agente
COPY ./src ./src

# Garante a existência do diretório de configuração caso seja montado via volume
RUN mkdir -p /app/config

# Comando de inicialização do pipeline de governança
CMD ["python", "src/main.py"]

