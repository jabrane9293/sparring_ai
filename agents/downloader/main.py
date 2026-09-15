import base64
import json
import os
import tempfile
import yt_dlp
from flask import Flask, jsonify, request
from google.cloud import storage, firestore, pubsub_v1

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
RAW_BUCKET_NAME = config["gcs"]["raw_videos_bucket"]
TOPIC_DOWNLOADED = config["pubsub"]["video_downloaded_topic"]
FIRESTORE_COLLECTION = config["firestore"]["collection_videos"]

storage_client = storage.Client(project=PROJECT_ID)
db = firestore.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_DOWNLOADED)

def extract_payload(request_data):
    if request_data and "message" in request_data and "data" in request_data["message"]:
        decoded = base64.b64decode(request_data["message"]["data"]).decode("utf-8")
        return json.loads(decoded)
    return request_data or {}

@app.route("/download", methods=["POST"])
def download():
    payload = extract_payload(request.get_json())
    video_id = payload.get("video_id")
    video_url = payload.get("url")

    if not video_id or not video_url:
        return jsonify({"status": "error", "message": "video_id ou url manquant"}), 400

    try:
        # 1. Télécharger la vidéo localement
        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_path = os.path.join(tmpdirname, f"{video_id}.webm")
            
            ydl_opts = {
                'format': 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best',
                'outtmpl': temp_path,
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # 2. Uploader sur Cloud Storage (GCS)
            bucket = storage_client.bucket(RAW_BUCKET_NAME)
            blob = bucket.blob(f"raw/{video_id}.webm")
            blob.upload_from_filename(temp_path)
            gcs_uri = f"gs://{RAW_BUCKET_NAME}/raw/{video_id}.webm"

        # 3. Initialiser le document dans Firestore
        db.collection(FIRESTORE_COLLECTION).document(video_id).set({
            "video_id": video_id,
            "source_url": video_url,
            "video_gcs_uri": gcs_uri,
            "status": "DOWNLOADED",
            "created_at": firestore.SERVER_TIMESTAMP
        })

        # 4. Déclencher l'Agent 3 (Analyzer) via Pub/Sub
        message_data = json.dumps({"video_id": video_id, "video_gcs_uri": gcs_uri}).encode("utf-8")
        publisher.publish(topic_path, message_data)

        return jsonify({"status": "success", "video_id": video_id})

    except Exception as e:
        print(f"Erreur de téléchargement: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)