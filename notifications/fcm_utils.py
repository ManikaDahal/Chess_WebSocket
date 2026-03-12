import os
import json
import firebase_admin
from firebase_admin import credentials, messaging
import logging
from .models import NotificationLog

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
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='chat_channel',
                    priority='max',
                ),
            ),
            apns=messaging.APNSConfig(
                headers={'apns-priority': '10'},
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(content_available=True),
                ),
            ),
            data=data or {},
            token=token,
        ) for token in tokens
    ]
    
    try:
        response = messaging.send_each(messages)
        logger.info(f"FCM: Successfully sent {response.success_count} messages.")
        print(f"FCM: Successfully sent {response.success_count} messages. Failures: {response.failure_count}")
        
        # Log specific token failures if any
        if response.failure_count > 0:
            for idx, res in enumerate(response.responses):
                if not res.success:
                    print(f"FCM: Failure for token index {idx}: {res.exception}")

        return response
    except Exception as e:
        logger.error(f"FCM: Error sending messages: {e}")
        print(f"FCM: Error sending messages: {e}")
        return None

def notify_user_via_fcm(user, title, body, data=None, category='system'):
    """Retrieves all tokens for a user and sends a notification."""
    return notify_multiple_users_via_fcm([user], title, body, data, category)

def notify_multiple_users_via_fcm(users, title, body, data=None, category='system'):
    """
    Sends a notification to multiple users and logs each attempt.
    Optimized for bulk delivery.
    """
    from chess_python.models import FCMToken
    
    # 1. Fetch all tokens for all selected users in one query
    token_objs = FCMToken.objects.filter(user__in=users).select_related('user')
    user_tokens = {}
    for t in token_objs:
        if t.user.id not in user_tokens:
            user_tokens[t.user.id] = []
        user_tokens[t.user.id].append(t.token)
    
    # 2. Bulk create NotificationLog entries
    logs_to_create = [
        NotificationLog(
            user=user,
            title=title,
            body=body,
            data=data or {},
            category=category,
            status='sent'
        )
        for user in users
    ]
    created_logs = NotificationLog.objects.bulk_create(logs_to_create)
    log_map = {log.user.id: log for log in created_logs}
    
    print(f"FCM [BATCH]: Prepared {len(created_logs)} logs for {len(users)} users.")

    # 3. Prepare FCM messages for all tokens
    all_tokens = []
    token_to_user_id = {}
    for user_id, tokens in user_tokens.items():
        for t in tokens:
            all_tokens.append(t)
            token_to_user_id[t] = user_id
            
    if not all_tokens:
        print("FCM [BATCH]: No tokens found for any recipient.")
        # Mark all logs as failed
        NotificationLog.objects.filter(id__in=[l.id for l in created_logs]).update(
            status='failed', 
            error_message="No FCM tokens found"
        )
        return None

    # 4. Send using batch messaging
    response = send_fcm_notification(all_tokens, title, body, data)
    
    if response:
        # 5. Update logs with FCM message IDs where possible
        success_user_ids = set()
        for idx, res in enumerate(response.responses):
            if res.success:
                u_id = token_to_user_id[all_tokens[idx]]
                success_user_ids.add(u_id)
                log = log_map.get(u_id)
                if log and not log.message_id:
                    log.message_id = res.message_id
        
        # Save updated message_ids 
        NotificationLog.objects.bulk_update(
            [log for log in created_logs if log.message_id], 
            ['message_id']
        )
        
        # Batch update status for those that had NO success
        failed_count = 0
        for log in created_logs:
            if log.user.id not in success_user_ids:
                log.status = 'failed'
                log.error_message = "All tokens failed or no tokens found"
                failed_count += 1
        
        if failed_count > 0:
            NotificationLog.objects.bulk_update(
                [log for log in created_logs if log.status == 'failed'], 
                ['status', 'error_message']
            )
            
    return response
