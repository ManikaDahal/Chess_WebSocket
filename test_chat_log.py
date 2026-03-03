import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()

from call.models import NotificationLog, ChatRoom
from call.notification_utils import notify_user_background
from django.contrib.auth import get_user_model
import time

User = get_user_model()

def test_chat_notification_log():
    user = User.objects.first()
    if not user:
        print("No users found.")
        return

    # Create/get a room
    room, _ = ChatRoom.objects.get_or_create(id=1)
    
    print(f"Testing chat notification log for user: {user.username}")
    
    # Initial log count
    initial_count = NotificationLog.objects.filter(user=user).count()
    
    # Trigger background notification
    notify_user_background(
        user_id=user.id,
        room_id=room.id,
        message="Verification Test Message",
        sender_id=user.id, # Self-notify for test
        sender_name="System",
        msg_id="test_msg_123",
        notification_type="chat_message"
    )
    
    # Wait for background thread
    print("Waiting for background thread to process...")
    time.sleep(3)
    
    # Check if a new log entry exists
    final_count = NotificationLog.objects.filter(user=user).count()
    
    if final_count > initial_count:
        latest_log = NotificationLog.objects.filter(user=user).order_by('-created_at').first()
        print(f"SUCCESS: New log entry created! ID: {latest_log.id}, Type: {latest_log.data.get('type')}")
    else:
        print("FAILURE: No new log entry created.")

if __name__ == "__main__":
    test_chat_notification_log()
