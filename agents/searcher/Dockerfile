FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# La configuration est maintenant copiée depuis le dossier local de l'agent
COPY config ./config

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app