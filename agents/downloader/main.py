import json
import os
import uuid
from flask import Flask, jsonify, request
import yt_dlp
from google.cloud import storage, pubsub_v1

app = Flask(__name__)

# --- CONFIGURATION ---
def load_config():
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/config.json'))
    docker_path = '/app/config/config.json'
    path = local_path if os.path.exists(local_path) else docker_path
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
PROJECT_ID = config["project_id"]

# Noms des ressources créées précédemment sur GCP
RAW_BUCKET_NAME = "sparring-ai-raw-videos"
TOPIC_DOWNLOADED = "video-downloaded"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_DOWNLOADED)
storage_client = storage.Client()

@app.route("/download", methods=["POST"])
def download():
    payload = request.get_json() or {}
    video_url = payload.get("video_url")
    video_title = payload.get("video_title", "Titre inconnu")
    fighter_name = payload.get("fighter_name", "Combattant inconnu")

    if not video_url:
        return jsonify({"error": "video_url manquant"}), 400

    print(f"Début du traitement pour '{video_title}'...")

    try:
        # 1. Télécharger la vidéo avec yt-dlp dans le dossier temporaire de Cloud Run
        tmp_filename = f"/tmp/{uuid.uuid4().hex}.mp4"
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': tmp_filename,
            'quiet': True,
            'no_warnings': True,
        }
        
        print("Téléchargement en cours depuis YouTube...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # 2. Uploader la vidéo vers Google Cloud Storage
        bucket = storage_client.bucket(RAW_BUCKET_NAME)
        # On crée un dossier au nom du combattant pour s'y retrouver
        gcs_blob_name = f"{fighter_name.replace(' ', '_')}/{uuid.uuid4().hex[:8]}.mp4"
        blob = bucket.blob(gcs_blob_name)
        
        print(f"Upload vers le bucket gs://{RAW_BUCKET_NAME}/{gcs_blob_name}...")
        blob.upload_from_filename(tmp_filename)
        gcs_uri = f"gs://{RAW_BUCKET_NAME}/{gcs_blob_name}"
        
        # Nettoyage de l'espace local (très important sur Cloud Run pour ne pas saturer la RAM)
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)

        # 3. Publier un message Pub/Sub pour déclencher l'Agent Analyzer (IA)
        message_data = {
            "gcs_uri": gcs_uri,
            "fighter_name": fighter_name,
            "video_title": video_title
        }
        publisher.publish(topic_path, json.dumps(message_data).encode("utf-8"))
        print("Notification envoyée à l'Agent 3 (Analyzer) via Pub/Sub !")

        return jsonify({
            "status": "success", 
            "message": f"Vidéo téléchargée et stockée avec succès.",
            "gcs_uri": gcs_uri
        })

    except Exception as e:
        print(f"Erreur durant le processus : {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Cloud Run injecte dynamiquement le port dans la variable d'environnement PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)