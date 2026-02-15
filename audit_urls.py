import os
import django
from django.test import RequestFactory

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from call.models import GameVideo
from call.serializers import GameVideoSerializer

factory = RequestFactory()
# Set HTTP_HOST to satisfy DisallowedHost
request = factory.get('/', HTTP_HOST='localhost')

print("--- URL Generation Audit ---")
for v in GameVideo.objects.all():
    serializer = GameVideoSerializer(v, context={'request': request})
    data = serializer.data
    print(f"Title: {v.title}")
    # Print the direct URL from the model and the one from the serializer
    raw_url = v.video_file.url if v.video_file else "None"
    print(f"  Raw URL: {raw_url}")
    print(f"  Srz URL: {data['video_url']}")
    print(f"  Stm URL: {data['stream_url']}")
    print("-" * 20)
