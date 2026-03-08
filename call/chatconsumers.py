from call.notification_utils import notify_room_members_background
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, Notification
from .notification_utils import notify_user_background

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])  
        self.user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        self.room_group_name = f"chat_{self.room_id}"
        
        print(f"[DEBUG] User {self.user_id} connecting to room {self.room_id}")
        
        # Add user to room in DB to ensure background notifications work
        await self.add_user_to_room_db()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"[DEBUG] Connection accepted for User {self.user_id}")

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

        # Handle ping/pong for keepalive
        if data.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            print(f"[DEBUG] Sent pong response to room {self.room_id}")
            return

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

        # Handle Message Status Updates (Delivered/Read)
        if data.get("type") in ["message_delivered", "message_read"]:
            msg_id = data.get("message_id")
            if msg_id:
                status_type = data.get("type").replace("message_", "") # 'delivered' or 'read'
                await self.update_message_status(msg_id, status_type)
                
                # Broadcast status update to the room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_status_update",
                        "message_id": msg_id,
                        "status": status_type,
                        "room_id": self.room_id
                    }
                )
            return

        # Handle Reactions
        if data.get("type") == "add_reaction":
            msg_id = data.get("message_id")
            emoji = data.get("emoji")
            if msg_id and emoji:
                await self.handle_reaction(self.user_id, msg_id, emoji)
                # Broadcast reaction to room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_reaction_update",
                        "message_id": msg_id,
                        "user_id": self.user_id,
                        "emoji": emoji,
                        "room_id": self.room_id
                    }
                )
            return

        message = data.get("message")
        user_id = data.get("user_id")
        sender_name = data.get("sender_name") or "Unknown"

        if (message and user_id):
            # If sender_name wasn't provided, try to look it up in local DB
            if sender_name == "Unknown":
                sender_name = await self.get_sender_name(user_id)
            
            msg_info = await self.save_message(user_id, message)
            
            # Pass msg_id if available to help with deduplication
            msg_id = msg_info.get('id') if msg_info else None
            await self.create_notification(user_id, message, sender_name, msg_id=msg_id)
            
            payload = {
                "type": "chat_message",
                "message": message,
                "user_id": user_id,
                "sender_name": sender_name,
                "trackingId": data.get("trackingId") # Return trackingId for replacement
            }
            if msg_info:
                payload.update(msg_info)

            await self.channel_layer.group_send(
                self.room_group_name,
                payload
            )
            print(f"[DEBUG] Received and broadcast: {message} from {sender_name} (ID: {msg_id}, trackingId: {data.get('trackingId')})")

    async def chat_message(self, event):
        msg_data = {
            "type": "chat_message",
            "message": event["message"],
            "user_id": event["user_id"],
            "sender_name": event.get("sender_name", "Unknown"),
            "room_id": self.room_id,
            "is_delivered": event.get("is_delivered", False),
            "is_read": event.get("is_read", False),
            "reactions": event.get("reactions", []),
            "trackingId": event.get("trackingId")
        }
        # Include ID and timestamp if present
        if "id" in event:
            msg_data["id"] = event["id"]
        if "timestamp" in event:
            msg_data["timestamp"] = event["timestamp"]

        await self.send(text_data=json.dumps(msg_data))

    async def message_status_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def message_reaction_update(self, event):
        await self.send(text_data=json.dumps(event))

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
    def add_user_to_room_db(self):
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        try:
            room, _ = ChatRoom.objects.get_or_create(id=self.room_id)
            user = User.objects.get(id=self.user_id)
            if not room.users.filter(id=user.id).exists():
                room.users.add(user)
                print(f"[DEBUG] Added user {user.username} to Room {self.room_id} in DB")
        except Exception as e:
            print(f"[ERROR] add_user_to_room_db: {e}")

    @database_sync_to_async
    def save_message(self, user_id, message):
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        try:
             room = ChatRoom.objects.get(id=int(self.room_id))
             user = User.objects.get(id=user_id)
             msg = Message.objects.create(room=room, sender=user, text=message)
             return {
                 "id": msg.id,
                 "timestamp": msg.timestamp.isoformat(),
                 "is_delivered": msg.is_delivered,
                 "is_read": msg.is_read
             }
        except Exception as e:
            print(f"[ERROR] save_message: {e}")
            return None

    @database_sync_to_async
    def update_message_status(self, msg_id, status_type):
        try:
            msg = Message.objects.get(id=msg_id)
            if status_type == 'delivered':
                msg.is_delivered = True
            elif status_type == 'read':
                msg.is_read = True
                msg.is_delivered = True # Cannot be read if not delivered
            msg.save()
        except Exception as e:
            print(f"[ERROR] update_message_status: {e}")

    @database_sync_to_async
    def handle_reaction(self, user_id, msg_id, emoji):
        from .models import MessageReaction
        from django.apps import apps
        User = apps.get_model('chess_python', 'CustomUser')
        try:
            user = User.objects.get(id=user_id)
            msg = Message.objects.get(id=msg_id)
            
            # Toggle reaction: if exists with same emoji, delete it. If different emoji, update it.
            existing = MessageReaction.objects.filter(user=user, message=msg).first()
            if existing:
                if existing.emoji == emoji:
                    existing.delete()
                else:
                    existing.emoji = emoji
                    existing.save()
            else:
                MessageReaction.objects.create(user=user, message=msg, emoji=emoji)
        except Exception as e:
            print(f"[ERROR] handle_reaction: {e}")
       

    # @database_sync_to_async
    # def create_notification(self, sender_id, message, sender_name, msg_id=None):
    #     from django.apps import apps
    #     from .notification_utils import notify_user_background
    #     User = apps.get_model('chess_python', 'CustomUser')
    #     try:
    #         room = ChatRoom.objects.get(id=int(self.room_id))
    #         sender = User.objects.get(id=int(sender_id))
    #         participants = room.users.exclude(id=sender.id).distinct()
    #         print(f"[DEBUG] create_notification: Sender {sender_id}. Total users in room: {room.users.count()}")
    #         print(f"[DEBUG] Participants to notify: {[p.username for p in participants]}")
            
    #         for user in participants:
    #             Notification.objects.create(user=user, sender=sender, message=message, room=room)
    #             # Global notification: Notify the user via non-blocking FCM
    #             print(f"FCM [DEBUG]: Triggering backend FCM for user {user.id} ({user.username}) in Room {self.room_id}")
    #             if participants.count() == 1:
    #                 receiver = participants.first()
    #                 notify_user_background(receiver.id, self.room_id, message, sender.id, sender_name, msg_id=msg_id)
                
    #             elif participants.count() > 1:
    #                 notify_room_members_background(
    #                 room_id=self.room_id,
    #                  message=message,
    #                  sender_id=sender.id,
    #                   sender_name=sender_name,
    #                   msg_id=msg_id
    #                   )
    #     except Exception as e:
    #          print(f"[ERROR] create_notification: {e}")

    @database_sync_to_async
    def create_notification(self, sender_id, message, sender_name, msg_id=None):
        from django.apps import apps
        from .notification_utils import notify_user_background
        User = apps.get_model('chess_python', 'CustomUser')
        from chess_python.models import FCMToken
        
        try:
            room = ChatRoom.objects.get(id=int(self.room_id))
            try:
                sender = User.objects.get(id=int(sender_id))
            except User.DoesNotExist:
                print(f"[ERROR] create_notification: Sender with ID {sender_id} not found in DB. Notification aborted.")
                return

            # Special Logic for Room 1 (General Room): 
            # Notify ALL users who have FCM tokens, not just those currently in room.users
            if int(self.room_id) == 1:
                print(f"[DEBUG] FCM_TRIGGER: Room 1 (General) detected. Querying all users with tokens...")
                # Fetch users who have at least one token
                users_with_tokens = User.objects.filter(fcm_tokens__isnull=False).exclude(id=sender.id).distinct()
                participants = users_with_tokens
            else:
                participants = room.users.exclude(id=sender.id).distinct()

            participant_list = list(participants.values_list('username', flat=True))
            print(f"[DEBUG] FCM_TRIGGER: Room {self.room_id}. Sender {sender.username} (ID: {sender.id})")
            print(f"[DEBUG] FCM_TRIGGER: Targets identified: {len(participant_list)} users -> {participant_list}")

            if not participant_list:
                print(f"[WARNING] FCM_TRIGGER: No matching users/tokens found for Room {self.room_id}")

            # Create DB notifications in bulk to avoid multiple queries
            notifs_to_create = [
                Notification(user=user, sender=sender, message=message, room=room)
                for user in participants
            ]
            if notifs_to_create:
                Notification.objects.bulk_create(notifs_to_create)
                print(f"FCM [LOG_TRACE]: Created {len(notifs_to_create)} Notification objects in DB.")

            # Trigger batch background FCM notification
            user_ids = list(participants.values_list('id', flat=True))
            if user_ids:
                from .notification_utils import notify_multiple_users_background
                print(f"FCM [LOG_TRACE]: Triggering batch notification for {len(user_ids)} users.")
                notify_multiple_users_background(user_ids, self.room_id, message, sender.id, sender_name, msg_id=msg_id)
        except Exception as e:
            print(f"[ERROR] create_notification main: {e}")


    @database_sync_to_async
    def get_history(self):
        from .models import MessageReaction
        try:
            # Get the most recent 50 messages, then reverse them
            messages = Message.objects.filter(room_id=self.room_id).select_related('sender').order_by('-timestamp')[:50]
            history = []
            for m in messages:
                # Aggregate reactions
                reactions_list = []
                reactions = MessageReaction.objects.filter(message=m)
                for r in reactions:
                    reactions_list.append({
                        "user_id": r.user.id,
                        "emoji": r.emoji
                    })

                history.append({
                    "id": m.id,
                    "message": m.text,
                    "user_id": m.sender.id,
                    "sender_name": m.sender.username,
                    "room_id": self.room_id,
                    "timestamp": m.timestamp.isoformat(),
                    "is_delivered": m.is_delivered,
                    "is_read": m.is_read,
                    "reactions": reactions_list
                })
            return list(reversed(history))
        except Exception as e:
            print(f"[ERROR] get_history: {e}")
            return []