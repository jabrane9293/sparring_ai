import os
from google import genai

PROJECT_ID = "sparring-ai-prod"
regions = ["europe-west1", "us-east4", "us-central1"]
models = ["gemini-2.5-flash"]

for region in regions:
  print(f"\n================ Région : {region} ================")
  try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=region)
    for model_id in models:
      try:
        response = client.models.generate_content(
            model=model_id, contents="Dis 'OK' si tu fonctionnes."
        )
        print(f"SUCCESS sur {region} avec {model_id} :", response.text.strip())
        os._exit(0)  # Arrête le script dès qu'une combinaison fonctionne
      except Exception as e:
        print(f"  - Échec {model_id} : {e}")
  except Exception as e:
    print(f"Erreur d'initialisation sur {region} : {e}")