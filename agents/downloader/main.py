import json
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

def load_config():
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/config.json'))
    docker_path = '/app/config/config.json'
    path = local_path if os.path.exists(local_path) else docker_path
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

@app.route("/download", methods=["POST"])
def download():
    payload = request.get_json() or {}
    video_url = payload.get("video_url")
    video_title = payload.get("video_title", "Titre inconnu")
    fighter_name = payload.get("fighter_name", "Combattant inconnu")

    if not video_url:
        return jsonify({"error": "video_url manquant"}), 400

    print(f"Action reçue : Téléchargement de '{video_title}' ({video_url}) pour {fighter_name}")

    # TODO : Télécharger la vidéo avec yt-dlp
    # TODO : Uploader la vidéo brute vers gs://sparring-ai-raw-videos
    # TODO : Publier un message Pub/Sub pour l'Agent 3 (Analyzer)

    return jsonify({
        "status": "success", 
        "message": f"Requête de téléchargement acceptée pour {video_title}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)