import json
from google.cloud import pubsub_v1

PROJECT_ID = "sparring-ai-prod"
TOPIC_ID = "topic-video-downloaded"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# Un JSON parfaitement formaté et encodé
message_data = json.dumps({"video_id": "BCESF0pDe6Q"}).encode("utf-8")

print(f"Publication sur {topic_path}...")
future = publisher.publish(topic_path, message_data)

print(f"SUCCESS ! Message publié avec l'ID : {future.result()}")