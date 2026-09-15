# 🥊 MMA Sparring AI Pipeline

An event-driven, cloud-native MLOps pipeline designed to automatically source, analyze, and clip mixed martial arts (MMA) sparring footage using Multimodal Generative AI.

## 🏗 Architecture Overview

This project is built on a microservices architecture deployed on **Google Cloud Platform (GCP)**. It utilizes asynchronous event-driven orchestration to ensure high scalability and resilience.

### The 4 AI Agents:
1. **Agent 1 (Scraper):** Receives parameters (fighter name, max videos, time range) and identifies relevant video URLs.
2. **Agent 2 (Downloader):** Downloads raw videos and ingests them into Google Cloud Storage (Data Lake).
3. **Agent 3 (Vision Analyzer):** Uses **Gemini 2.5 Flash** (Vertex AI) to natively analyze video feeds and extract precise sparring timestamps.
4. **Agent 4 (Clipper):** A containerized FFmpeg service that extracts the identified segments and uploads the final clips.

## 🛠 Tech Stack

*   **Compute:** GCP Cloud Run (Serverless)
*   **Orchestration:** GCP Pub/Sub (Push Subscriptions)
*   **State & Metadata:** GCP Firestore (NoSQL)
*   **Storage:** Google Cloud Storage (GCS)
*   **AI / Vision:** Google Vertex AI (Gemini 2.5 Flash)
*   **Video Processing:** FFmpeg
*   **API & Backend:** Python, Flask, Gunicorn, Docker
*   **Frontend (WIP):** Streamlit

## 🚀 Event-Driven Workflow

1. A request is sent to the Scraper.
2. The Downloader uploads the raw file to GCS and creates a Firestore document.
3. A Pub/Sub event `topic-video-downloaded` triggers the Analyzer.
4. Gemini analyzes the video and updates Firestore.
5. A Pub/Sub event `topic-video-analyzed` triggers the Clipper.
6. FFmpeg cuts the video and uploads the final `.mp4` clips to GCS.

## 💻 Local Setup & Development

*(À compléter avec les commandes pour créer le `.venv` et installer les requirements)*

## ☁️ Deployment (CI/CD)

This project uses Google Cloud Build for continuous deployment. Pushing to the `main` branch automatically builds the Docker images and updates the Cloud Run services.