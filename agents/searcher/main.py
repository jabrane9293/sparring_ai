import os
import json
import yt_dlp
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1, firestore

app = Flask(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT", "sparring-ai-prod")
TOPIC_NAME = "video-discovered"

db = firestore.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

class SearchAgent:
    def __init__(self, max_results=3):
        self.max_results = max_results
        self.ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }

    def search_and_publish(self, fighter_name):
        search_query = f"ytsearch{self.max_results}:{fighter_name} sparring training vlog"
        discovered_videos = []

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                result = ydl.extract_info(search_query, download=False)
                if 'entries' in result:
                    for entry in result['entries']:
                        video_id = entry.get('id')
                        if not video_id:
                            continue

                        video_data = {
                            'video_id': video_id,
                            'title': entry.get('title'),
                            'url': entry.get('url'),
                            'duration': entry.get('duration'),
                            'uploader': entry.get('uploader'),
                            'fighter_name': fighter_name,
                            'status': 'DISCOVERED'
                        }

                        # 1. Sauvegarde dans Firestore
                        db.collection('videos_metadata').document(video_id).set(video_data)

                        # 2. Notification aux autres agents via Pub/Sub
                        message_bytes = json.dumps(video_data).encode('utf-8')
                        publisher.publish(topic_path, message_bytes)

                        discovered_videos.append(video_data)
            except Exception as e:
                print(f"Erreur lors de la recherche : {e}")

        return discovered_videos

@app.route('/search', methods=['POST'])
def search_endpoint():
    data = request.get_json() or {}
    fighter_name = data.get('fighter_name')

    if not fighter_name:
        return jsonify({"error": "Le paramètre 'fighter_name' est requis."}), 400

    agent = SearchAgent(max_results=3)
    results = agent.search_and_publish(fighter_name)

    return jsonify({
        "status": "success",
        "fighter": fighter_name,
        "count": len(results),
        "videos": results
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)