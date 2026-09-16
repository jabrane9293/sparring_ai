# 🥊 Sparring AI - Multi-Agent Video Analysis

Ce projet est un pipeline d'Intelligence Artificielle multi-agents conçu pour automatiser la détection et l'extraction de séquences de sparring à partir de vidéos brutes (vlogs, entraînements) disponibles sur le web.

## 🏗️ Architecture Cloud (GCP)

Le système repose sur une architecture de microservices pilotée par les événements (Event-Driven) sur Google Cloud Platform :

* **Agent 1 : Scraper (Cloud Run)** - Reçoit les requêtes de recherche et identifie les vidéos pertinentes.
* **Agent 2 : Downloader (Cloud Run)** - Récupère les vidéos et les stocke sur Cloud Storage (GCS).
* **Agent 3 : Analyzer (Cloud Run + Vertex AI)** - Utilise les capacités de vision de **Gemini 2.5 Flash** pour détecter les moments spécifiques de sparring (casques, gants, configuration du ring).
* **Agent 4 : Clipper (Cloud Run)** - Découpe automatiquement les segments validés et génère les highlights finaux.

## 🛠️ Stack Technique & MLOps

* **Langage & Framework :** Python, Flask
* **Orchestration :** Google Cloud Pub/Sub
* **Stockage :** Cloud Storage (GCS) pour les vidéos, Firestore pour les métadonnées.
* **Modèle IA :** Vertex AI (Large Vision Models)
* **CI/CD :** Cloud Build (Déploiement continu automatisé à chaque `git push`)

## 🚀 Déploiement

Le déploiement est entièrement automatisé. Un push sur la branche `main` déclenche le pipeline `cloudbuild.yaml` qui :
1. Injecte la configuration centralisée (`config.json`).
2. Construit les 4 images Docker en parallèle sur Artifact Registry.
3. Déploie les mises à jour en mode serverless sur Cloud Run.