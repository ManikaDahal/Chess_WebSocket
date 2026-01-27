import os
import json
import firebase_admin
from firebase_admin import credentials, messaging
import logging

logger = logging.getLogger(__name__)

def initialize_fcm():
    """Initializes Firebase Admin SDK using environment variable."""
    if not firebase_admin._apps:
        try:
            service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
            if service_account_info:
                # If it's a file path, load it. If it's the JSON string, parse it.
                if service_account_info.startswith("{"):
                    cert_dict = json.loads(service_account_info)
                    cred = credentials.Certificate(cert_dict)
                else:
                    cred = credentials.Certificate(service_account_info)
                
                firebase_admin.initialize_app(cred)
                logger.info("FCM: Firebase Admin initialized successfully.")
                print("FCM: Firebase Admin initialized successfully.")
            else:
                logger.warning("FCM: FIREBASE_SERVICE_ACCOUNT_JSON environment variable not found.")
                print("FCM: FIREBASE_SERVICE_ACCOUNT_JSON environment variable not found.")
        except Exception as e:
            logger.error(f"FCM: Error initializing Firebase Admin: {e}")
            print(f"FCM: Error initializing Firebase Admin: {e}")

def send_fcm_notification(tokens, title, body, data=None):
    """Sends a notification to a list of FCM tokens."""
    if not tokens:
        return
    
    initialize_fcm()
    
    # Firebase messaging expects tokens in a list
    if isinstance(tokens, str):
        tokens = [tokens]

    messages = [
        messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        ) for token in tokens
    ]
    
    try:
        response = messaging.send_each(messages)
        logger.info(f"FCM: Successfully sent {response.success_count} messages.")
        print(f"FCM: Successfully sent {response.success_count} messages. Failures: {response.failure_count}")
        
        return response
    except Exception as e:
        logger.error(f"FCM: Error sending messages: {e}")
        print(f"FCM: Error sending messages: {e}")
        return None

def notify_user_via_fcm(user, title, body, data=None):
    """Retrieves all tokens for a user and sends a notification."""
    from chess_python.models import FCMToken
    tokens = list(FCMToken.objects.filter(user=user).values_list('token', flat=True))
    if tokens:
        print(f"FCM: Found {len(tokens)} tokens for user {user.username} (ID: {user.id})")
        return send_fcm_notification(tokens, title, body, data)
    else:
        logger.info(f"FCM: No tokens found for user {user.username} (ID: {user.id})")
        print(f"FCM: No tokens found for user {user.username} (ID: {user.id})")
        return None
