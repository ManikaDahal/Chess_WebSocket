import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from call.models import GameVideo

print("--- Video Listing ---")
for v in GameVideo.objects.all():
    url = v.video_file.url if v.video_file else "None"
    print(f"Title: {v.title}")
    print(f"  ID: {v.id}")
    print(f"  URL: {url}")
    print("-" * 20)
