FROM python:3.11-slim

WORKDIR /app

# Installer ffmpeg (requis par yt-dlp pour fusionner vidéo/audio)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY config ./config

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app