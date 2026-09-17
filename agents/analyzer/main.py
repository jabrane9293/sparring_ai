import base64
import json
import os
from flask import Flask, jsonify, request
from google.cloud import firestore, pubsub_v1
from google import genai
from google.genai import types

app = Flask(__name__)

# --- CHARGEMENT INTELLIGENT DE LA CONFIGURATION ---
def load_config():
    # Cherche le fichier en local ou dans le conteneur Docker
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/config.json'))
    docker_path = '/app/config/config.json'
    path = local_path if os.path.exists(local_path) else docker_path
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

# --- VARIABLES GLOBALES DYNAMIQUES ---
PROJECT_ID = config["project_id"]
LOCATION = config["region"]
MODEL_NAME = config["ai"]["model_name"]
FIRESTORE_COLLECTION = config["firestore"]["collection_videos"]
TOPIC_ANALYZED = config["pubsub"]["sparring_detected_topic"]

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
db = firestore.Client(project=PROJECT_ID)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ANALYZED)

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
    fighter_name = payload.get("fighter_name", "l'athlète") # Récupération dynamique

    # Prompt orienté "Activité Sportive" (plus permissif et évite les blocages)
    prompt = f"""
    Tu es un expert en analyse vidéo de détection d'activité sportive.
    Analyse cette vidéo et trouve tous les moments d'action dynamiques (entraînement intensif, temps forts). 
    La vidéo concerne {fighter_name}. Si tu ne peux pas l'identifier formellement (casque, angle de vue), renvoie quand même toutes les séquences d'action intenses.
    
    Règles strictes :
    1. Retourne le résultat UNIQUEMENT sous forme d'une liste JSON d'objets.
    2. Chaque objet doit avoir les clés "start_time" (en secondes, nombre) et "end_time" (en secondes, nombre).
    
    Exemple de format attendu :
    [
      {{"start_time": 12.5, "end_time": 45.0}},
      {{"start_time": 80.0, "end_time": 110.5}}
    ]
    """

    try:
        # Note : On met video/mp4 car l'Agent 2 télécharge en mp4
        video_part = types.Part.from_uri(file_uri=video_uri, mime_type="video/mp4")
        
        # Configuration permissive pour éviter les faux négatifs de sécurité
        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                )
            ]
        )

        # 1. Analyse IA
        response = client.models.generate_content(
            model=MODEL_NAME, contents=[video_part, prompt], config=config
        )
        clips_data = json.loads(response.text)

        # 2. Sauvegarde Firestore
        db.collection(FIRESTORE_COLLECTION).document(video_id).set(
            {"video_id": video_id, "video_gcs_uri": video_uri, "clips": clips_data, "status": "ANALYZED", "analyzed_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )

        # 3. DÉCLENCHEMENT PUB/SUB POUR L'AGENT 4
        message_data = json.dumps({"video_id": video_id}).encode("utf-8")
        publisher.publish(topic_path, message_data)

        # 4. Retour HTTP pour l'interface Streamlit (Ajout de la clé 'timestamps')
        return jsonify({
            "status": "success", 
            "video_id": video_id, 
            "timestamps": clips_data,
            "pubsub_triggered": True
        })
        
    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)