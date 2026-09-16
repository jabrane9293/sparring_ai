import json
import os
from flask import Flask, jsonify, request

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

# On remplace /scrape par /search pour matcher avec Streamlit
@app.route("/search", methods=["POST"])
def search():
    payload = request.get_json() or {}
    # On récupère la bonne clé envoyée par le frontend
    fighter_name = payload.get("fighter_name", "Default Fighter")

    print(f"Recherche de vidéos pour {fighter_name}...")
    
    # TODO Phase 3: Intégrer la vraie API YouTube ici
    # En attendant, on simule des résultats pour remplir ton interface web
    mock_results = [
        {
            "title": f"{fighter_name} - Hard Sparring Session",
            "uploader": "MMA Training Center",
            "url": "https://www.youtube.com/watch?v=BCESF0pDe6Q"
        },
        {
            "title": f"Highlights {fighter_name} Workout",
            "uploader": "Fight Camp",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
    ]

    # On renvoie le dictionnaire sous la clé "results" attendue par Streamlit
    return jsonify({"status": "success", "results": mock_results})

if __name__ == "__main__":
    # Le port 8080 est celui imposé par défaut par Cloud Run
    app.run(host="0.0.0.0", port=8080)