import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Sparring AI Pipeline", page_icon="🥊", layout="wide"
)

# --- PARAMÈTRES ET URLS DES AGENTS ---
SEARCHER_URL = os.environ.get(
    "SEARCHER_URL", "https://searcher-agent-ffoyrf75aq-uc.a.run.app/search"
)
DOWNLOADER_URL = os.environ.get(
    "DOWNLOADER_URL", "http://localhost:8081/download"
)
ANALYZER_URL = os.environ.get(
    "ANALYZER_URL", "https://analyzer-agent-ffoyrf75aq-uc.a.run.app/analyze"
)
CLIPPER_URL = os.environ.get(
    "CLIPPER_URL", "https://clipper-agent-ffoyrf75aq-uc.a.run.app/clip"
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

    if st.button("🚀 Lancer le traitement complet (Download ➔ IA ➔ Découpage)"):
        
        # ==========================================
        # ÉTAPE 1 : Téléchargement (Agent 2 - Local)
        # ==========================================
        with st.spinner(f"📥 1/3 Téléchargement et envoi sur Cloud Storage..."):
            download_payload = {
                "video_id": selected_video.get("video_id"),
                "video_url": selected_video.get("url"),
                "fighter_name": fighter_query,
            }
            try:
                dl_response = requests.post(DOWNLOADER_URL, json=download_payload, timeout=300)
                dl_response.raise_for_status()
                gcs_uri = dl_response.json().get("gcs_uri")
                st.success(f"✅ Vidéo préparée sur GCS : {gcs_uri}")
            except Exception as e:
                st.error(f"Erreur lors du téléchargement (Agent 2) : {e}")
                st.stop() # Arrête l'exécution si ça plante

        # ==========================================
        # ÉTAPE 2 : Analyse Vision IA (Agent 3 - Cloud Run)
        # ==========================================
        analyze_success = False
        timestamps = []
        
        with st.spinner(f"🧠 2/3 Gemini analyse l'activité de {fighter_query} (peut prendre 1-2 min)..."):
            analyze_payload = {
                "gcs_uri": gcs_uri,
                "fighter_name": fighter_query
            }
            try:
                analyze_response = requests.post(ANALYZER_URL, json=analyze_payload, timeout=300)
                analyze_response.raise_for_status()
                timestamps = analyze_response.json().get("timestamps", [])
                analyze_success = True
            except Exception as e:
                st.error(f"Erreur lors de l'analyse IA (Agent 3) : {e}")
                
        # On gère l'arrêt en DEHORS du spinner pour que l'UI se mette à jour
        if not analyze_success:
            st.stop()
            
        if not timestamps:
            st.warning("L'IA n'a détecté aucune séquence d'action claire dans cette vidéo.")
            st.stop()
            
        st.success(f"✅ {len(timestamps)} séquences d'action détectées !")

        # ==========================================
        # ÉTAPE 3 : Découpage FFmpeg (Agent 4 - Cloud Run)
        # ==========================================
        with st.spinner("✂️ 3/3 Découpage automatique des séquences en cours..."):
            clip_payload = {
                "video_id": selected_video.get("video_id"),
                "gcs_uri": gcs_uri,
                "timestamps": timestamps,
                "fighter_name": fighter_query
            }
            try:
                clip_response = requests.post(CLIPPER_URL, json=clip_payload, timeout=300)
                clip_response.raise_for_status()
                clips_uris = clip_response.json().get("clips", [])
                
                st.success("🎉 Pipeline terminé avec succès !")
                
                st.write("### 🎬 Séquences isolées sauvegardées sur GCS :")
                for clip in clips_uris:
                    st.code(clip) # Affiche le chemin GCS pour chaque clip découpé
                    
            except Exception as e:
                st.error(f"Erreur lors du découpage (Agent 4) : {e}")

else:
    st.info("👈 Tape le nom d'un athlète dans la barre latérale pour commencer.")