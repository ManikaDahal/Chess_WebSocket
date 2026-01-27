import threading
import logging
from .fcm_utils import notify_user_via_fcm

logger = logging.getLogger(__name__)

def notify_user_background(user_id, room_id, message, sender_id, sender_name):
    """
    Entry point to trigger an FCM notification in a background thread.
    This prevents the WebSocket consumer from hangng.
    """
    thread = threading.Thread(
        target=_process_notification,
        args=(user_id, room_id, message, sender_id, sender_name),
        daemon=True
    )
    thread.start()

def _process_notification(user_id, room_id, message, sender_id, sender_name):
    """
    The actual work function running in the background thread.
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        fcm_data = {
            "room_id": str(room_id),
            "user_id": str(sender_id),
            "sender_name": str(sender_name),
            "type": "chat_message"
        }
        
        print(f"FCM: Background thread starting for user {user.username}")
        
        notify_user_via_fcm(
            user=user,
            title=f"New message from {sender_name}",
            body=message,
            data=fcm_data
        )
    except Exception as e:
        logger.error(f"FCM: Background notification failed for user {user_id}: {e}")
        print(f"FCM: Background notification ERROR: {e}")
