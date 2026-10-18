FROM python:3.13-slim

# Evita gravação de ficheiros .pyc no disco
ENV PYTHONDONTWRITEBYTECODE=1

# Logs no terminal
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do projeto backend
COPY . .

# Expõe a porta interna do container
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]