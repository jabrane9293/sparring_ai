import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    # On récupère bien "fighter_name" envoyé par Streamlit
    fighter_name = data.get("fighter_name", "").strip()

    if not fighter_name:
        return jsonify({"error": "Le nom du combattant est requis"}), 400

    if not YOUTUBE_API_KEY:
        return jsonify({"error": "Clé API YouTube manquante côté serveur."}), 500

    url = "https://www.googleapis.com/youtube/v3/search"
    search_query = f"{fighter_name} sparring OR highlights"
    
    params = {
        "part": "snippet",
        "q": search_query,
        "type": "video",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
        
        videos_list = []
        for item in items:
            video_id = item["id"]["videoId"]
            videos_list.append({
                "video_id": video_id,
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "uploader": item["snippet"]["channelTitle"],
                "duration": "N/A" # L'API search ne donne pas la durée directement
            })
            
        # Structure exacte attendue par app.py
        return jsonify({"fighter": fighter_name, "videos": videos_list})
        
    except Exception as e:
        return jsonify({"error": f"Erreur API YouTube: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)