# Imagem base leve do Python
FROM python:3.12-slim

# Diretório padrão dentro do container
WORKDIR /app

# Instalação das dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia do código-fonte e configurações
COPY ./src ./src
COPY ./config ./config

# Comando de inicialização do pipeline
CMD ["python", "src/main.py"]
