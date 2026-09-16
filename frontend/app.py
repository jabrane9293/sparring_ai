import streamlit as st
import requests

# L'URL est maintenant fixée dans le code (ou idéalement dans un fichier .env plus tard)
SEARCHER_URL = "https://searcher-agent-ffoyrf75aq-uc.a.run.app"
DOWNLOADER_URL = "https://downloader-agent-ffoyrf75aq-uc.a.run.app/download"

# ==========================================
# CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="Sparring AI - Dashboard", 
    page_icon="🥊", 
    layout="wide"
)

st.title("🥊 Sparring AI - Extracteur de moments forts")
st.markdown("Recherchez un combattant et laissez les agents IA isoler ses meilleures sessions d'entraînement.")

# ==========================================
# BARRE LATÉRALE
# ==========================================
with st.sidebar:
    st.header("⚙️ Infrastructure")
    st.write("Statut : 🟢 En ligne (GCP)")
    st.caption(f"Agent Chercheur : {SEARCHER_URL[:30]}...")
    st.caption(f"Agent Téléchargeur : {DOWNLOADER_URL[:30]}...")

# ==========================================
# ZONE PRINCIPALE : RECHERCHE
# ==========================================
fighter_name = st.text_input("Nom du combattant :", placeholder="ex: Jon Jones, Ciryl Gane, Cédric Doumbé")

if st.button("Lancer l'Agent Chercheur", type="primary"):
    if not fighter_name:
        st.warning("Veuillez entrer un nom de combattant.")
    elif SEARCHER_URL == "URL_SEARCHER_ICI" or DOWNLOADER_URL == "URL_DOWNLOADER_ICI":
        st.error("Veuillez configurer les URLs Cloud Run dans le fichier app.py.")
    else:
        with st.spinner(f"L'Agent scrute le web pour {fighter_name}..."):
            try:
                # 1. Appel HTTP vers l'Agent Cloud Run (Searcher)
                response = requests.post(
                    f"{SEARCHER_URL.rstrip('/')}/search",
                    json={"fighter_name": fighter_name}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("results", [])
                    
                    st.success(f"✅ {len(videos)} vidéos potentielles trouvées pour {fighter_name} !")
                    
                    # 2. Affichage des résultats
                    for idx, vid in enumerate(videos, 1):
                        with st.expander(f"🎬 {vid['title']}"):
                            cols = st.columns([2, 1])
                            
                            # Colonne de gauche : Infos vidéo
                            with cols[0]:
                                st.write(f"**Chaîne :** {vid['uploader']}")
                                st.write(f"**Lien :** {vid['url']}")
                                
                            # Colonne de droite : Action (Déclenchement du pipeline)
                            with cols[1]:
                                if st.button("Envoyer au Pipeline 🚀", key=f"btn_{idx}"):
                                    with st.spinner("Transmission à l'Agent de Téléchargement..."):
                                        payload = {
                                            "video_url": vid['url'],
                                            "video_title": vid['title'],
                                            "fighter_name": fighter_name
                                        }
                                        try:
                                            # Appel HTTP vers l'Agent Cloud Run (Downloader)
                                            resp = requests.post(
                                                f"{DOWNLOADER_URL.rstrip('/')}/download", 
                                                json=payload
                                            )
                                            if resp.status_code == 200:
                                                st.success("✅ Vidéo injectée ! Le pipeline (Téléchargement ➔ IA ➔ Découpage) tourne en arrière-plan sur GCP.")
                                            else:
                                                st.error(f"Erreur d'injection ({resp.status_code}) : {resp.text}")
                                        except Exception as e:
                                            st.error(f"Erreur de communication avec l'Agent Téléchargeur : {e}")
                else:
                    st.error(f"Erreur de l'Agent Chercheur : {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Impossible de joindre l'Agent Chercheur. Vérifiez l'URL. Détails : {e}")