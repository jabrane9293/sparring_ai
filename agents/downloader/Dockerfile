FROM python:3.10-slim

# Installation de ffmpeg pour la gestion des flux vidéo/audio
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

COPY config ./config

CMD ["gunicorn", "--bind", "0.0.0.0:8081", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]