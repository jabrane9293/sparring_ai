import os
import glob
from flask import Flask, jsonify, request
from google.cloud import storage
import yt_dlp

app = Flask(__name__)

RAW_BUCKET_NAME = "sparring-ai-raw-videos"
storage_client = storage.Client()


@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json() or {}
    video_id = data.get("video_id")
    video_url = data.get("video_url")
    fighter_name = data.get("fighter_name", "inconnu")

    if not video_id or not video_url:
        return jsonify({"error": "video_id et video_url sont obligatoires"}), 400

    # Sauvegarde dans le dossier courant (plus sûr sur Windows)
    tmp_filename = f"{video_id}.mp4"
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": tmp_filename,
        "quiet": True,
    }

    try:
        print(f"Téléchargement de {video_id}...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Upload vers GCS dans un sous-dossier au nom du combattant
        bucket = storage_client.bucket(RAW_BUCKET_NAME)
        gcs_blob_name = f"{fighter_name.replace(' ', '_')}/{video_id}.mp4"
        blob = bucket.blob(gcs_blob_name)

        print(f"Upload vers gs://{RAW_BUCKET_NAME}/{gcs_blob_name}...")
        blob.upload_from_filename(tmp_filename)
        gcs_uri = f"gs://{RAW_BUCKET_NAME}/{gcs_blob_name}"

        return jsonify({
            "status": "success",
            "video_id": video_id,
            "gcs_uri": gcs_uri,
        })

    except Exception as e:
        print(f"Erreur : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Nettoyage GARANTI (exécuté quoi qu'il arrive, succès ou erreur)
        try:
            # Supprime la vidéo finale si elle existe
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)
            # Supprime les fragments incomplets (.part, .ytdl, etc.)
            for temp_file in glob.glob(f"{tmp_filename}*"):
                os.remove(temp_file)
            print("Nettoyage local terminé.")
        except Exception as cleanup_error:
            print(f"Erreur lors de la suppression locale : {cleanup_error}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)