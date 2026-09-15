$PROJECT_ID = "sparring-ai-prod"
$REGION = "us-central1"

Write-Host "=== Initialisation de l'infrastructure GCP ===" -ForegroundColor Cyan

Write-Host "`n1. Création des buckets Cloud Storage..."
gcloud storage buckets create gs://sparring-ai-raw-videos --location=$REGION --project=$PROJECT_ID
gcloud storage buckets create gs://sparring-ai-clips --location=$REGION --project=$PROJECT_ID

Write-Host "`n2. Création des canaux de communication Pub/Sub..."
gcloud pubsub topics create topic-video-downloaded --project=$PROJECT_ID
gcloud pubsub topics create topic-video-analyzed --project=$PROJECT_ID

Write-Host "`n=== Infrastructure de base créée avec succès ! ===" -ForegroundColor Green
Write-Host "⚠️ Note : Les abonnements (Subscriptions) Push devront être créés APRES le déploiement des agents Cloud Run pour avoir leurs URLs." -ForegroundColor Yellow