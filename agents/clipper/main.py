import os
import subprocess
import tempfile
from flask import Flask, jsonify, request
from google.cloud import firestore, storage

app = Flask(__name__)

PROJECT_ID = "sparring-ai-prod"
RAW_BUCKET_NAME = "sparring-ai-raw-videos"
CLIPS_BUCKET_NAME = "sparring-ai-clips"

db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

def ensure_bucket_exists(bucket_name):
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        storage_client.create_bucket(bucket, location="us-central1")
    return bucket

@app.route("/clip", methods=["POST"])
def clip_video():
    data = request.get_json() or {}
    video_id = data.get("video_id")
    fighter_name = data.get("fighter_name", "inconnu").replace(' ', '_')
    
    # Récupération des timestamps envoyés par Streamlit
    clips_info = data.get("timestamps", [])
    gcs_uri = data.get("gcs_uri")

    if not clips_info or not gcs_uri:
        return jsonify({"status": "error", "message": "timestamps et gcs_uri sont requis"}), 400

    # Retrouver la vidéo brute sur Cloud Storage
    raw_bucket = storage_client.bucket(RAW_BUCKET_NAME)
    raw_blob_name = gcs_uri.split(f"gs://{RAW_BUCKET_NAME}/")[-1]
    raw_blob = raw_bucket.blob(raw_blob_name)

    if not raw_blob.exists():
        return jsonify({"status": "error", "message": f"Fichier {raw_blob_name} introuvable"}), 404

    generated_clips = []
    clips_bucket = ensure_bucket_exists(CLIPS_BUCKET_NAME)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Télécharger la vidéo brute localement dans le conteneur
        local_raw_path = os.path.join(tmpdir, "raw_video.mp4")
        raw_blob.download_to_filename(local_raw_path)

        # 2. Découper chaque segment avec FFmpeg
        for idx, clip in enumerate(clips_info, start=1):
            
            # CORRECTION : Utilisation des nouvelles clés et conversion forcée en String
            start_time = str(clip.get("start_time", clip.get("start", 0)))
            end_time = str(clip.get("end_time", clip.get("end", 0)))
            
            output_filename = f"{video_id}_clip_{idx}.mp4"
            local_output_path = os.path.join(tmpdir, output_filename)

            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-ss", start_time,
                "-to", end_time,
                "-i", local_raw_path,
                "-c:v", "copy",
                "-c:a", "copy",
                "-avoid_negative_ts", "make_zero",
                local_output_path,
            ]

            # Exécution de FFmpeg
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

            # 3. Téléverser le clip vers GCS (dans un dossier au nom du combattant)
            gcs_clip_path = f"{fighter_name}/{video_id}/{output_filename}"
            clip_blob = clips_bucket.blob(gcs_clip_path)
            clip_blob.upload_from_filename(local_output_path)

            generated_clips.append(f"gs://{CLIPS_BUCKET_NAME}/{gcs_clip_path}")

    # 4. Mettre à jour Firestore
    doc_ref = db.collection("videos_metadata").document(video_id)
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
    port = int(os.environ.get("PORT", 8083))
    app.run(host="0.0.0.0", port=port)