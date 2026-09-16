from flask import Flask, jsonify, request
import yt_dlp

app = Flask(__name__)


@app.route("/search", methods=["POST"])
def search_videos():
  data = request.get_json() or {}
  fighter_name = data.get("fighter_name", "").strip()

  if not fighter_name:
    return jsonify({"error": "Le nom du combattant est requis"}), 400

  search_query = f"ytsearch5:{fighter_name} sparring OR highlights"
  ydl_opts = {
      "extract_flat": True,
      "quiet": True,
      "no_warnings": True,
      "extractor_args": {"youtube": ["player_client=android"]},
  }

  videos_list = []
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(search_query, download=False)
      entries = info.get("entries", [])

      for entry in entries:
        video_id = entry.get("id")
        title = entry.get("title")
        uploader = entry.get("uploader", "Inconnu")
        duration = entry.get("duration", 0)

        videos_list.append({
            "video_id": video_id,
            "title": title,
            "uploader": uploader,
            "duration": duration,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })
  except Exception as e:
    return jsonify({"error": str(e)}), 500

  return jsonify({"fighter": fighter_name, "videos": videos_list})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080)