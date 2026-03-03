import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from call.models import NotificationLog
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

def test_robust_lookup():
    user = User.objects.first()
    if not user:
        print("No users found.")
        return

    # Mocked full FCM ID
    full_fcm_id = "projects/abc/messages/0:12345%6789"
    short_fcm_id = "0:12345%6789"
    
    log = NotificationLog.objects.create(
        user=user,
        message_id=full_fcm_id,
        title="Test",
        body="Test",
        status="sent"
    )
    print(f"Created log with message_id: {full_fcm_id}")

    # Test endswith lookup
    found = NotificationLog.objects.filter(
        Q(message_id=short_fcm_id) | 
        Q(message_id__endswith=short_fcm_id)
    ).first()

    if found and found.id == log.id:
        print(f"SUCCESS: Found log using short ID '{short_fcm_id}' via endswith.")
    else:
        print(f"FAILURE: Could not find log using short ID.")

    log.delete()

if __name__ == "__main__":
    test_robust_lookup()
