import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Sparring AI Pipeline", page_icon="🥊", layout="wide"
)

# --- PARAMÈTRES ET URLS DES AGENTS ---
# Remplace ces URLs par les vraies URLs publiques de tes services Cloud Run
SEARCHER_URL = os.environ.get(
    "SEARCHER_URL", "https://searcher-agent-ffoyrf75aq-uc.a.run.app/search"
)
DOWNLOADER_URL = os.environ.get(
    "DOWNLOADER_URL", "https://downloader-agent-ffoyrf75aq-uc.a.run.app/download"
)

# --- BARRE LATÉRALE ---
st.sidebar.title("🥊 Sparring AI")
st.sidebar.markdown("---")

st.sidebar.header("1. Recherche de Combattant")
fighter_query = st.sidebar.text_input(
    "Nom du combattant (ex: Islam Makhachev, Jon Jones...)"
)

if "videos" not in st.session_state:
  st.session_state.videos = []

if st.sidebar.button("Rechercher sur YouTube"):
  if not fighter_query.strip():
    st.sidebar.warning("Veuillez entrer un nom.")
  else:
    with st.spinner(f"Recherche en cours pour {fighter_query}..."):
      try:
        response = requests.post(
            SEARCHER_URL, json={"fighter_name": fighter_query}, timeout=30
        )
        if response.status_code == 200:
          data = response.json()
          st.session_state.videos = data.get("videos", [])
          st.sidebar.success(
              f"{len(st.session_state.videos)} vidéos trouvées !"
          )
        else:
          st.sidebar.error(f"Erreur Searcher : {response.text}")
      except Exception as e:
        st.sidebar.error(f"Erreur de connexion : {e}")

# --- CORPS PRINCIPAL ---
st.title("Tableau de bord - Pipeline Vidéo")

if st.session_state.videos:
  st.markdown("### 2. Sélectionner et envoyer au pipeline")

  video_options = {
      f"{v.get('title')} (Durée: {v.get('duration')}s) - [{v.get('uploader')}]": v
      for v in st.session_state.videos
  }
  selected_label = st.selectbox(
      "Choisissez une vidéo à traiter :", list(video_options.keys())
  )
  selected_video = video_options[selected_label]

  st.video(selected_video.get("url"))

  if st.button("🚀 Lancer le téléchargement (Agent 2)"):
    with st.spinner("Téléchargement et transfert vers Cloud Storage..."):
      try:
        payload = {
            "video_id": selected_video.get("video_id"),
            "video_url": selected_video.get("url"),
            "video_title": selected_video.get("title"),
            "fighter_name": fighter_query,
        }
        response = requests.post(DOWNLOADER_URL, json=payload, timeout=180)

        if response.status_code == 200:
          st.success("Vidéo traitée et stockée avec succès dans GCS !")
          st.json(response.json())
        else:
          st.error(f"Erreur Downloader : {response.text}")
      except requests.exceptions.Timeout:
        st.error("Le téléchargement a pris trop de temps (timeout).")
      except Exception as e:
        st.error(f"Erreur de connexion : {e}")
else:
  st.info("👈 Tape le nom d'un combattant dans la barre latérale pour commencer.")