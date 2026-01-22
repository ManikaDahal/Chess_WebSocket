import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, Notification
from .mqtt_utils import notify_user_via_mqtt

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.contrib.auth.models import User
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])  
        self.room_group_name = f"chat_{self.room_id}"
        print(f"[DEBUG] Trying to connect to room {self.room_id}")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print("[DEBUG] Connection accepted")


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"[DEBUG] Disconnected with code {close_code}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")
        user_id = data.get("user_id")

        if message and user_id:
            await self.save_message(user_id, message)
            await self.create_notification(user_id, message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user_id": user_id,
                }
            )
            print(f"[DEBUG] Received: {text_data}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "user_id": event["user_id"],
            "room_id":self.room_id
        }))

    @database_sync_to_async
    def save_message(self, user_id, message):
        from django.contrib.auth.models import User
        try:
             room = ChatRoom.objects.get(id=int(self.room_id))
             user = User.objects.get(id=user_id)
             Message.objects.create(room=room, sender=user, text=message)
        except Exception as e:
            print(f"[ERROR] save_message: {e}")
       

    @database_sync_to_async
    def create_notification(self, sender_id, message):
        from django.contrib.auth.models import User
        try:
            room = ChatRoom.objects.get(id=int(self.room_id))
            sender = User.objects.get(id=sender_id)
            for user in room.users.exclude(id=sender_id):
                Notification.objects.create(user=user, sender=sender, message=message, room=room)
                # Also notify via MQTT for push notifications
                notify_user_via_mqtt(user.id, message, sender_id, room.id)
        except Exception as e:
             print(f"[ERROR] create_notification: {e}")