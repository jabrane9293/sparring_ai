import json
import os
from flask import Flask, jsonify, request
from google.cloud import pubsub_v1

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
TOPIC_DISCOVERED = config["pubsub"]["video_discovered_topic"]

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_DISCOVERED)

@app.route("/scrape", methods=["POST"])
def scrape():
    # Cet agent est appelé directement par Streamlit, on lit donc un JSON classique
    payload = request.get_json() or {}
    fighter = payload.get("fighter", "Default Fighter")
    max_videos = payload.get("max_videos", 1)

    # TODO Phase 3: Intégrer la vraie logique de recherche (ex: API YouTube)
    # Pour le moment, on simule la découverte d'une vidéo (celle qui marche bien)
    print(f"Recherche de {max_videos} vidéos pour {fighter}...")
    
    discovered_videos = [
        {"video_id": "BCESF0pDe6Q", "url": "https://www.youtube.com/watch?v=BCESF0pDe6Q"}
    ]

    # Pour chaque vidéo trouvée, on lance une instance de l'Agent 2 via Pub/Sub
    published_count = 0
    for video in discovered_videos:
        message_data = json.dumps(video).encode("utf-8")
        publisher.publish(topic_path, message_data)
        published_count += 1

    return jsonify({"status": "success", "videos_triggered": published_count, "fighter": fighter})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)