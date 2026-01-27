import paho.mqtt.client as mqtt
import json
import logging
import ssl
from .fcm_utils import notify_user_via_fcm

logger = logging.getLogger(__name__)

# HiveMQ Cloud Broker settings - MUST MATCH Flutter app credentials
MQTT_BROKER = "feb84b33473b4be6a63034536797ca8c.s1.eu.hivemq.cloud"
MQTT_PORT = 8883  # TLS port
MQTT_USERNAME = "hivemq.webclient.1769426436046"
MQTT_PASSWORD = r"uYVG6&c>Smx1Ao0%!7Hh"
MQTT_KEEPALIVE = 60


def publish_mqtt_message(topic, message_dict):
    """
    Publishes a message to an MQTT topic using HiveMQ Cloud with TLS.
    """
    try:
        client = mqtt.Client()
        
        # Set username and password for authentication
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Enable TLS/SSL
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
        
        # Connect to HiveMQ Cloud broker
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        
        payload = json.dumps(message_dict)
        print(f"MQTT: Publishing to topic '{topic}': {payload}")
        result = client.publish(topic, payload, qos=1)
        
        # Wait for publish to complete
        result.wait_for_publish()
        
        # Check if the message was actually published
        if result.is_published():
            logger.info(f"MQTT: Successfully sent message to topic {topic}")
            print(f"MQTT: Success - message published")
        else:
            logger.error(f"MQTT: Failed to send message to topic {topic}")
            print(f"MQTT: Failed to publish")
            
        client.disconnect()
    except Exception as e:
        logger.error(f"MQTT: Error publishing message: {e}")
        print(f"MQTT: Exception - {e}")


def notify_room_via_mqtt(room_id, message, sender_id, sender_name):
    """
    Notifies everyone in a specific room about a new message via MQTT.
    """
    topic = f"chess/room/{room_id}/messages"
    data = {
        "message": message,
        "user_id": sender_id,
        "room_id": room_id,
        "sender_name": sender_name,
    }
    publish_mqtt_message(topic, data)

def notify_user_via_mqtt(user_id, room_id, message, sender_id, sender_name):
    """
    Notifies a specific user about a new message in any room.
    """
    topic = f"chess/user/{user_id}/notifications"
    import time
    
    publish_mqtt_message(topic, data)

    # ALSO send via FCM
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
        
        notify_user_via_fcm(
            user=user,
            title=f"New message from {sender_name}",
            body=message,
            data=fcm_data
        )
    except Exception as e:
        logger.error(f"FCM: Failed to trigger notification for user {user_id}: {e}")
        print(f"FCM: Failed to trigger notification: {e}")
