import threading
import logging
from .fcm_utils import notify_user_via_fcm

logger = logging.getLogger(__name__)

def notify_user_background(user_id, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None):
    """
    Entry point to trigger an FCM notification in a background thread.
    This prevents the WebSocket consumer from hanging.
    """
    thread = threading.Thread(
        target=_process_notification,
        args=(user_id, room_id, message, sender_id, sender_name, msg_id, notification_type, category),
        daemon=True
    )
    thread.start()


def notify_multiple_users_background(user_ids, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None):
    """
    Triggers batch FCM notifications for multiple users in a single background thread.
    """
    thread = threading.Thread(
        target=_process_multi_notification,
        args=(user_ids, room_id, message, sender_id, sender_name, msg_id, notification_type, category),
        daemon=True
    )
    thread.start()


def notify_room_members_background(room_id, message, sender_id, sender_name, msg_id=None):
    """
    Sends FCM notification to all members of a room except the sender.
    Optimized to use batch processing.
    """
    try:
        from call.models import ChatRoom  

        room = ChatRoom.objects.get(id=room_id)
        participants = room.users.exclude(id=sender_id)
        user_ids = list(participants.values_list('id', flat=True))
        
        if user_ids:
            print(f"FCM: Room {room_id} triggering batch notification for {len(user_ids)} users.")
            notify_multiple_users_background(
                user_ids=user_ids,
                room_id=room_id,
                message=message,
                sender_id=sender_id,
                sender_name=sender_name,
                msg_id=msg_id
            )
    except Exception as e:
        print(f"FCM Room Notify Error: {e}")


def _process_notification(user_id, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None):
    """Wrapper for single user notification in background."""
    _process_multi_notification([user_id], room_id, message, sender_id, sender_name, msg_id, notification_type, category)


def _process_multi_notification(user_ids, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None):
    """
    The actual work function running in the background thread for one or more users.
    """
    try:
        from django.contrib.auth import get_user_model
        from .fcm_utils import notify_multiple_users_via_fcm
        User = get_user_model()
        
        users = list(User.objects.filter(id__in=user_ids))
        if not users:
            return

        fcm_data = {
            "room_id": str(room_id),
            "user_id": str(sender_id),
            "sender_name": str(sender_name),
            "message": str(message),
            "id": str(msg_id) if msg_id else "",
            "type": notification_type
        }
        
        print(f"FCM [BATCH_TRACE]: Starting background thread for {len(users)} users. Type: {notification_type}")
        
        # Map notification_type to category if not explicitly provided
        if not category:
            if notification_type == "chat_message":
                category = "message"
            elif notification_type in ["chess_invite", "invite_accepted", "invite_declined"]:
                category = "invitation"
            else:
                category = "system"

        title = f"New message from {sender_name}" if notification_type == "chat_message" else f"Chess Invite from {sender_name}"
        
        notify_multiple_users_via_fcm(
            users=users,
            title=title,
            body=message,
            data=fcm_data,
            category=category
        )
    except Exception as e:
        logger.error(f"FCM: Background batch notification failed: {e}")
        print(f"FCM: Background batch notification ERROR: {e}")
