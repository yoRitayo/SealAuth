FROM python:3.11-slim

# Evita gravação de ficheiros .pyc no disco
ENV PYTHONDONTWRITEBYTECODE=1

# Logs no terminal
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do projeto backend
COPY . .

# Expõe a porta interna do container
EXPOSE 8000

# Roda na porta 8000 interna do container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]