import threading
import logging
from .fcm_utils import notify_user_via_fcm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Add new notification_type → category mappings here when you create a new
# notification type. This is the single source of truth.
# ---------------------------------------------------------------------------
NOTIFICATION_TYPE_TO_CATEGORY = {
    "chat_message":    "message",
    "reaction":        "message",
    "chess_invite":    "invitation",
    "snake_invite":    "invitation",
    "invite_accepted": "invitation",
    "invite_declined": "invitation",
}

# Title template per notification_type. Use {sender_name} as placeholder.
NOTIFICATION_TITLE_TEMPLATES = {
    "chat_message":    "New message from {sender_name}",
    "reaction":        "{sender_name} reacted to your message",
    "chess_invite":    "Chess Invite from {sender_name}",
    "snake_invite":    "Snake Game Invite from {sender_name}",
    "invite_accepted": "{sender_name} accepted your invite!",
    "invite_declined": "{sender_name} declined your invite.",
}


def notify_user_background(user_id, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None, extra_data=None):
    """
    Entry point to trigger an FCM notification in a background thread.
    extra_data: optional dict of additional key/value pairs merged into the FCM payload.
    """
    thread = threading.Thread(
        target=_process_notification,
        args=(user_id, room_id, message, sender_id, sender_name, msg_id, notification_type, category, extra_data),
        daemon=True
    )
    thread.start()


def notify_multiple_users_background(user_ids, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None, extra_data=None):
    """
    Triggers batch FCM notifications for multiple users in a single background thread.
    extra_data: optional dict of additional key/value pairs merged into the FCM payload.
    """
    thread = threading.Thread(
        target=_process_multi_notification,
        args=(user_ids, room_id, message, sender_id, sender_name, msg_id, notification_type, category, extra_data),
        daemon=True
    )
    thread.start()


def notify_room_members_background(room_id, message, sender_id, sender_name, msg_id=None):
    """
    Sends FCM notification to all members of a room except the sender.
    """
    try:
        from chat.models import ChatRoom

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


def _process_notification(user_id, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None, extra_data=None):
    """Wrapper for single user notification in background."""
    _process_multi_notification([user_id], room_id, message, sender_id, sender_name, msg_id, notification_type, category, extra_data)


def _process_multi_notification(user_ids, room_id, message, sender_id, sender_name, msg_id=None, notification_type="chat_message", category=None, extra_data=None):
    """
    The actual work function running in the background thread for one or more users.
    """
    try:
        from django.contrib.auth import get_user_model
        from .fcm_utils import notify_multiple_users_via_fcm
        from .models import NotificationPreference, NotificationLog
        User = get_user_model()

        users = list(User.objects.filter(id__in=user_ids))
        if not users:
            return

        # Resolve category from mapping if not explicitly provided
        if not category:
            category = NOTIFICATION_TYPE_TO_CATEGORY.get(notification_type, "system")

        blocked_user_ids = set(
            NotificationPreference.objects.filter(
                user__in=users,
                category=category,
                is_blocked=True,
            ).values_list('user_id', flat=True)
        )

        allowed_users = [u for u in users if u.id not in blocked_user_ids]
        blocked_users  = [u for u in users if u.id in blocked_user_ids]

        # Log blocked for audit trail
        if blocked_users:
            title = NOTIFICATION_TITLE_TEMPLATES.get(
                notification_type, "Notification"
            ).format(sender_name=sender_name)
            NotificationLog.objects.bulk_create([
                NotificationLog(
                    user=u,
                    title=title,
                    body=message,
                    data={
                        "room_id": str(room_id),
                        "user_id": str(sender_id),
                        "sender_name": str(sender_name),
                        "id": str(msg_id) if msg_id else "",
                        "type": notification_type,
                        "category": category,
                    },
                    category=category,
                    status='blocked',
                    error_message="User has blocked this notification category",
                )
                for u in blocked_users
            ])
            print(f"FCM [BATCH]: {len(blocked_users)} user(s) blocked category '{category}'. Skipped.")

        if not allowed_users:
            print(f"FCM [BATCH]: All recipients blocked '{category}'. Nothing to send.")
            return

        fcm_data = {
            "room_id": str(room_id),
            "user_id": str(sender_id),
            "sender_name": str(sender_name),
            "message": str(message),
            "id": str(msg_id) if msg_id else "",
            "type": notification_type,
            "category": category,
        }
        # Merge caller-supplied extra fields (all values must be strings for FCM)
        if extra_data:
            for k, v in extra_data.items():
                fcm_data[str(k)] = str(v) if v is not None else ""

        title = NOTIFICATION_TITLE_TEMPLATES.get(
            notification_type, "Notification"
        ).format(sender_name=sender_name)

        print(f"FCM [BATCH_TRACE]: Sending to {len(allowed_users)} user(s). Type: {notification_type}, Category: {category}")

        notify_multiple_users_via_fcm(
            users=allowed_users,
            title=title,
            body=message,
            data=fcm_data,
            category=category,
        )
    except Exception as e:
        logger.error(f"FCM: Background batch notification failed: {e}")
        print(f"FCM: Background batch notification ERROR: {e}")
