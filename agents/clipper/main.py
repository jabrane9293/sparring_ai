import base64
import json
import os
import subprocess
import tempfile
from flask import Flask, jsonify, request
from google.cloud import firestore, storage

app = Flask(__name__)

# --- CHARGEMENT INTELLIGENT DE LA CONFIGURATION ---
def load_config():
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/config.json'))
    docker_path = '/app/config/config.json'
    path = local_path if os.path.exists(local_path) else docker_path
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

# --- VARIABLES GLOBALES DYNAMIQUES ---
PROJECT_ID = config["project_id"]
RAW_BUCKET_NAME = config["gcs"]["raw_videos_bucket"]
CLIPS_BUCKET_NAME = config["gcs"]["processed_clips_bucket"]
FIRESTORE_COLLECTION = config["firestore"]["collection_videos"]

db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)


def ensure_bucket_exists(bucket_name):
  """Crée le bucket de clips S'il n'existe pas encore."""
  bucket = storage_client.bucket(bucket_name)
  if not bucket.exists():
    storage_client.create_bucket(bucket, location="us-central1")
  return bucket

def extract_payload(request_data):
    if request_data and "message" in request_data and "data" in request_data["message"]:
        decoded = base64.b64decode(request_data["message"]["data"]).decode("utf-8")
        return json.loads(decoded)
    return request_data or {}


@app.route("/clip", methods=["POST"])
def clip_video():
  payload = extract_payload(request.get_json())
  video_id = payload.get("video_id", "BCESF0pDe6Q")

  # 1. Récupérer les métadonnées depuis Firestore
  doc_ref = db.collection(FIRESTORE_COLLECTION).document(video_id)
  doc = doc_ref.get()

  if not doc.exists:
    return (
        jsonify({
            "status": "error",
            "message": f"Document {video_id} introuvable dans Firestore",
        }),
        404,
    )

  metadata = doc.to_dict()
  clips_info = metadata.get("clips", [])

  if not clips_info:
    return (
        jsonify({
            "status": "error",
            "message": "Aucun timestamp de clip trouvé dans Firestore",
        }),
        400,
    )

  raw_blob_name = f"raw/{video_id}.webm"
  raw_bucket = storage_client.bucket(RAW_BUCKET_NAME)
  raw_blob = raw_bucket.blob(raw_blob_name)

  if not raw_blob.exists():
    return (
        jsonify({
            "status": "error",
            "message": f"Fichier vidéo {raw_blob_name} introuvable dans GCS",
        }),
        404,
    )

  generated_clips = []
  clips_bucket = ensure_bucket_exists(CLIPS_BUCKET_NAME)

  with tempfile.TemporaryDirectory() as tmpdir:
    # 2. Télécharger la vidéo brute localement
    local_raw_path = os.path.join(tmpdir, f"{video_id}.webm")
    raw_blob.download_to_filename(local_raw_path)

    # 3. Découper chaque segment avec FFmpeg
    for idx, clip in enumerate(clips_info, start=1):
      start_time = clip.get("start")
      end_time = clip.get("end")
      output_filename = f"{video_id}_clip_{idx}.mp4"
      local_output_path = os.path.join(tmpdir, output_filename)

      ffmpeg_cmd = [
          "ffmpeg",
          "-y",
          "-ss",
          start_time,
          "-to",
          end_time,
          "-i",
          local_raw_path,
          "-c:v",
          "libx264",
          "-c:a",
          "aac",
          "-avoid_negative_ts",
          "make_zero",
          local_output_path,
      ]

      subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

      # 4. Téléverser le clip vers GCS (sparring-ai-clips)
      gcs_clip_path = f"clips/{video_id}/{output_filename}"
      clip_blob = clips_bucket.blob(gcs_clip_path)
      clip_blob.upload_from_filename(local_output_path)

      generated_clips.append({
          "clip_id": f"{video_id}_{idx}",
          "gcs_uri": f"gs://{CLIPS_BUCKET_NAME}/{gcs_clip_path}",
          "start": start_time,
          "end": end_time,
      })

  # 5. Mettre à jour Firestore avec la liste des clips découpés
  doc_ref.set(
      {
          "processed_clips": generated_clips,
          "status": "CLIPPED",
          "clipped_at": firestore.SERVER_TIMESTAMP,
      },
      merge=True,
  )

  return jsonify({
      "status": "success",
      "video_id": video_id,
      "clips_count": len(generated_clips),
      "clips": generated_clips,
  })


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8083)