import base64
import json
import os
from flask import Flask, jsonify, request
from google.cloud import firestore, pubsub_v1
from google import genai
from google.genai import types

app = Flask(__name__)

PROJECT_ID = "sparring-ai-prod"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-flash"

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
db = firestore.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, "topic-video-analyzed")

def extract_payload(request_data):
    """Décode les données de la requête (Appel direct HTTP ou Push Pub/Sub)"""
    if request_data and "message" in request_data and "data" in request_data["message"]:
        decoded = base64.b64decode(request_data["message"]["data"]).decode("utf-8")
        return json.loads(decoded)
    return request_data or {}

@app.route("/analyze", methods=["POST"])
def analyze():
  payload = extract_payload(request.get_json())
  video_id = payload.get("video_id", "BCESF0pDe6Q")
  video_uri = payload.get("video_gcs_uri", f"gs://sparring-ai-raw-videos/raw/{video_id}.webm")

  prompt = """Analyse cette vidéo de combat/sparring.
    Identifie avec précision chaque segment où il y a un échange de sparring actif.
    Renvoie le résultat sous forme de liste JSON d'objets avec les clés "start", "end" et "label".
    Exemple: [{"start": "00:10", "end": "00:45", "label": "sparring"}]"""

  try:
    video_part = types.Part.from_uri(file_uri=video_uri, mime_type="video/webm")
    config = types.GenerateContentConfig(response_mime_type="application/json")

    # 1. Analyse IA
    response = client.models.generate_content(
        model=MODEL_NAME, contents=[video_part, prompt], config=config
    )
    clips_data = json.loads(response.text)

    # 2. Sauvegarde Firestore
    db.collection("videos_metadata").document(video_id).set(
        {"video_id": video_id, "video_gcs_uri": video_uri, "clips": clips_data, "status": "ANALYZED", "analyzed_at": firestore.SERVER_TIMESTAMP},
        merge=True,
    )

    # 3. DÉCLENCHEMENT PUB/SUB POUR L'AGENT 4
    message_data = json.dumps({"video_id": video_id}).encode("utf-8")
    publisher.publish(topic_path, message_data)

    return jsonify({"status": "success", "video_id": video_id, "pubsub_triggered": True})
  except Exception as e:
    print(f"Erreur: {e}")
    return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8082)