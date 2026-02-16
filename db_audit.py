import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from django.db import connection

print("--- RAW DB VIDEO AUDIT ---")
with connection.cursor() as cursor:
    cursor.execute("SELECT title, video_file FROM call_gamevideo")
    for row in cursor.fetchall():
        print(f"Title: {row[0]}")
        print(f"  Field Value: {row[1]}")
        print("-" * 20)
