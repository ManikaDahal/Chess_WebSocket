import paho.mqtt.client as mqtt
import json
import logging

logger = logging.getLogger(__name__)

# MQTT Broker settings
MQTT_BROKER = "broker.hivemq.com" # Using HiveMQ public broker
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

def publish_mqtt_message(topic, message_dict):
    """
    Publishes a message to an MQTT topic.
    """
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        
        payload = json.dumps(message_dict)
        print(f"MQTT: Publishing to topic '{topic}': {payload}")
        result = client.publish(topic, payload)
        
        # Check if the message was actually published
        status = result[0]
        if status == 0:
            logger.info(f"MQTT: Successfully sent message to topic {topic}")
            print(f"MQTT: Success status 0")
        else:
            logger.error(f"MQTT: Failed to send message to topic {topic}, status: {status}")
            print(f"MQTT: Failed status {status}")
            
        client.disconnect()
    except Exception as e:
        logger.error(f"MQTT: Error publishing message: {e}")

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
    data = {
        "message": message,
        "user_id": sender_id,
        "room_id": int(room_id),
        "sender_name": sender_name,
    }
    publish_mqtt_message(topic, data)
