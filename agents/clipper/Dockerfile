# Utilisation d'une image Python légère
FROM python:3.11-slim

# Étape critique pour l'Agent 4 : Installation de FFmpeg au niveau de l'OS
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY main.py .

# Port d'écoute pour Cloud Run / Local
EXPOSE 8083

# Lancement du serveur avec Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8083", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]