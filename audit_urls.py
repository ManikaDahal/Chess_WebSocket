import os
import django
import cloudinary
from django.test import RequestFactory

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

# Hardcode credentials for debug script
cloudinary.config(
    cloud_name = "drxgymnwa",
    api_key = "491754462791483",
    api_secret = "m5WpWp6z0pP8v9Rz6xP8v9Rz6xP" # Placeholder
)

from call.models import GameVideo
from call.serializers import GameVideoSerializer

factory = RequestFactory()
request = factory.get('/', HTTP_HOST='localhost')

print("--- CLOUDINARY URL AUDIT ---")
for v in GameVideo.objects.all():
    serializer = GameVideoSerializer(v, context={'request': request})
    data = serializer.data
    print(f"Video: {v.title}")
    print(f"  Hardened URL: {data['video_url']}")
    print("-" * 20)
