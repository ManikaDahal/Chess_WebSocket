import os
import django
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from call.models import NotificationLog, Notification, ChatRoom
from call.notification_utils import notify_multiple_users_background
from django.contrib.auth import get_user_model

User = get_user_model()

def test_batch_notification():
    # Setup test users
    user_names = ["TestUser1", "TestUser2", "TestUser3"]
    users = []
    for name in user_names:
        u, _ = User.objects.get_or_create(username=name)
        users.append(u)
    
    room, _ = ChatRoom.objects.get_or_create(id=1)
    user_ids = [u.id for u in users]
    
    print(f"Testing batch notification for {len(user_ids)} users: {user_names}")
    
    # Run batch background notification
    notify_multiple_users_background(
        user_ids=user_ids,
        room_id=room.id,
        message="Batch Optimization Test",
        sender_id=999,
        sender_name="Optimizer",
        msg_id="batch_test_001"
    )
    
    print("Waiting for batch processing...")
    time.sleep(3)
    
    # Verify logs
    for u in users:
        log = NotificationLog.objects.filter(user=u, body="Batch Optimization Test").first()
        if log:
            print(f"SUCCESS: Log entry found for {u.username} (ID: {log.id})")
        else:
            print(f"FAILURE: No log entry found for {u.username}")

    # Verify status (should be failed if no FCM secret, but entry exists)
    for u in users:
        log = NotificationLog.objects.filter(user=u, body="Batch Optimization Test").first()
        if log and log.status in ['sent', 'failed']:
            print(f"Log status for {u.username}: {log.status}")

if __name__ == "__main__":
    test_batch_notification()
