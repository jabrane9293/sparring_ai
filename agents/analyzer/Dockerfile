# Utiliser une image Python très légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source de l'agent (main.py, etc.)
COPY . .

# Définir le port par défaut (l'Agent 3 utilise le 8082)
ENV PORT=8082

# Lancer le serveur web Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app