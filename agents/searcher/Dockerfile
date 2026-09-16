FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY main.py .

# La configuration est maintenant copiée depuis le dossier local de l'agent
COPY config ./config
COPY cookies.txt .

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app