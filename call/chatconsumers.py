import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, Notification
from .mqtt_utils import notify_room_via_mqtt

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])  
        self.room_group_name = f"chat_{self.room_id}"
        print(f"[DEBUG] Trying to connect to room {self.room_id}")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print("[DEBUG] Connection accepted")

        # Send history on connect
        messages = await self.get_history()
        await self.send(text_data=json.dumps({
            "type": "history",
            "messages": messages,
            "room_id": self.room_id
        }))
        print(f"[DEBUG] Sent {len(messages)} history messages to user")


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"[DEBUG] Disconnected with code {close_code}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Check if it's a history request
        if data.get("type") == "get_history":
            messages = await self.get_history()
            await self.send(text_data=json.dumps({
                "type": "history",
                "messages": messages,
                "room_id": self.room_id
            }))
            print(f"[DEBUG] Sent {len(messages)} history messages on request")
            return

        message = data.get("message")
        user_id = data.get("user_id")
        sender_name = data.get("sender_name") or "Unknown"

        if message and user_id:
            # If sender_name wasn't provided, try to look it up in local DB (though it might be empty on WebSocket server)
            if sender_name == "Unknown":
                sender_name = await self.get_sender_name(user_id)
            
            await self.save_message(user_id, message)
            await self.create_notification(user_id, message, sender_name)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user_id": user_id,
                    "sender_name": sender_name,
                }
            )
            print(f"[DEBUG] Received and broadcast: {message} from {sender_name}")

    async def chat_message(self, event):
        print("[DEBUG] Sending to frontend:",event)
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "user_id": event["user_id"],
            "sender_name": event.get("sender_name", "Unknown"),
            "room_id": self.room_id
        }))

    @database_sync_to_async
    def get_sender_name(self, user_id):
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        try:
            user = User.objects.get(id=user_id)
            return user.username
        except:
            return "Unknown"

    @database_sync_to_async
    def save_message(self, user_id, message):
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        try:
             room = ChatRoom.objects.get(id=int(self.room_id))
             user = User.objects.get(id=user_id)
             Message.objects.create(room=room, sender=user, text=message)
        except Exception as e:
            print(f"[ERROR] save_message: {e}")
       

    @database_sync_to_async
    def create_notification(self, sender_id, message, sender_name):
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        try:
            room = ChatRoom.objects.get(id=int(self.room_id))
            sender = User.objects.get(id=sender_id)
            for user in room.users.exclude(id=sender_id):
                Notification.objects.create(user=user, sender=sender, message=message, room=room)
            
            # Notify the whole room via MQTT (testing phase: room-wide)
            notify_room_via_mqtt(room.id, message, sender_id, sender_name)
        except Exception as e:
             print(f"[ERROR] create_notification: {e}")

    @database_sync_to_async
    def get_history(self):
        try:
            messages = Message.objects.filter(room_id=self.room_id).order_by('created_at')[:50]
            return [
                {
                    "message": m.text,
                    "user_id": m.sender.id,
                    "sender_name": m.sender.username,
                    "room_id": self.room_id
                }
                for m in messages
            ]
        except Exception as e:
            print(f"[ERROR] get_history: {e}")
            return []