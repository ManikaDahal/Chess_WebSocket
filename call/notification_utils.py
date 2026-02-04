import threading
import logging
from .fcm_utils import notify_user_via_fcm

logger = logging.getLogger(__name__)

def notify_user_background(user_id, room_id, message, sender_id, sender_name, msg_id=None):
    """
    Entry point to trigger an FCM notification in a background thread.
    This prevents the WebSocket consumer from hanging.
    """
    thread = threading.Thread(
        target=_process_notification,
        args=(user_id, room_id, message, sender_id, sender_name, msg_id),
        daemon=True
    )
    thread.start()


def notify_room_members_background(room_id, message, sender_id, sender_name, msg_id=None):
    """
    Sends FCM notification to all members of a room except the sender.
    """
    try:
        from call.models import ChatRoom  

        room = ChatRoom.objects.get(id=room_id)

        # Loop through all members except sender
        for member in room.members.exclude(id=sender_id):
            notify_user_background(
                user_id=member.id,
                room_id=room_id,
                message=message,
                sender_id=sender_id,
                sender_name=sender_name,
                msg_id=msg_id
            )

    except Exception as e:
        print(f"FCM Room Notify Error: {e}")


def _process_notification(user_id, room_id, message, sender_id, sender_name, msg_id=None):
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
            "message": str(message),
            "id": str(msg_id) if msg_id else "",
            "type": "chat_message"
        }
        
        print(f"FCM: Background thread starting for user {user.username}. ID presence: {bool(msg_id)}")
        
        notify_user_via_fcm(
            user=user,
            title=f"New message from {sender_name}",
            body=message,
            data=fcm_data
        )
    except Exception as e:
        logger.error(f"FCM: Background notification failed for user {user_id}: {e}")
        print(f"FCM: Background notification ERROR: {e}")
