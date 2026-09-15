import base64
import json
import os
import tempfile
from flask import Flask, jsonify, request
from google.cloud import firestore, pubsub_v1, storage
import yt_dlp

app = Flask(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT", "sparring-ai-prod")
BUCKET_NAME = "sparring-ai-raw-videos"
TOPIC_NAME = "video-downloaded"

storage_client = storage.Client(project=PROJECT_ID)
db = firestore.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)


class DownloadAgent:

  def __init__(self, bucket_name):
    self.bucket = storage_client.bucket(bucket_name)

  def download_and_upload(self, video_id, video_url):
    with tempfile.TemporaryDirectory() as temp_dir:
      # Modèle souple : laisse yt-dlp attribuer la vraie extension (ex: .webm, .mp4, .mkv)
      output_template = os.path.join(temp_dir, f"{video_id}.%(ext)s")

      ydl_opts = {
          "outtmpl": output_template,
          "quiet": True,
          "no_warnings": True,
      }

      print(f"Téléchargement de la vidéo {video_id}...")
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

      # Récupération automatique du fichier généré dans le dossier temporaire
      downloaded_files = os.listdir(temp_dir)
      if not downloaded_files:
        raise FileNotFoundError(
            f"Aucun fichier n'a été téléchargé pour la vidéo {video_id}."
        )

      file_name = downloaded_files[0]
      local_file_path = os.path.join(temp_dir, file_name)

      # Définition du nom sur Cloud Storage avec l'extension réelle
      gcs_blob_name = f"raw/{file_name}"
      blob = self.bucket.blob(gcs_blob_name)

      print(
          f"Transfert de {file_name} vers Cloud Storage"
          f" gs://{BUCKET_NAME}/{gcs_blob_name}..."
      )
      blob.upload_from_filename(local_file_path)

      gcs_uri = f"gs://{BUCKET_NAME}/{gcs_blob_name}"
      return gcs_uri


@app.route("/download", methods=["POST"])
def download_endpoint():
  data = request.get_json() or {}

  if "message" in data and "data" in data["message"]:
    payload = base64.b64decode(data["message"]["data"]).decode("utf-8")
    payload_data = json.loads(payload)
  else:
    payload_data = data

  video_id = payload_data.get("video_id")
  video_url = payload_data.get("url")

  if not video_id or not video_url:
    return jsonify({"error": "Paramètres 'video_id' et 'url' requis."}), 400

  try:
    agent = DownloadAgent(BUCKET_NAME)
    gcs_uri = agent.download_and_upload(video_id, video_url)

    # 1. Mise à jour dans Firestore
    doc_ref = db.collection("videos_metadata").document(video_id)
    doc_ref.update({"status": "DOWNLOADED", "gcs_uri": gcs_uri})

    # 2. Notification Pub/Sub
    event_data = {
        "video_id": video_id,
        "gcs_uri": gcs_uri,
        "fighter_name": payload_data.get("fighter_name"),
    }
    publisher.publish(topic_path, json.dumps(event_data).encode("utf-8"))

    return (
        jsonify({"status": "success", "video_id": video_id, "gcs_uri": gcs_uri}),
        200,
    )

  except Exception as e:
    print(f"Erreur lors du traitement : {e}")
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8081))
  app.run(host="0.0.0.0", port=port)