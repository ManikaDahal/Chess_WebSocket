# WebSocket Consumer for Call Signaling
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'call_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send a connection confirmation to the client
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to room: {self.room_name}'
        }))

        # Notify others in the room - essential for initiating WebRTC handshakes
        if (self.room_name.startswith("user_") or 
            self.room_name.startswith("game_call_") or 
            self.room_name == "chess_room_1"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'signal_message',
                    'message': {
                        'type': 'peer_joined',
                        'sender': 'system',
                        'sender_channel': self.channel_name,
                        'message': f'Peer joined room: {self.room_name}'
                    },
                    'sender': self.channel_name
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Handle ping/pong for keepalive
        if data.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            return

        # NEW: Trigger FCM push notification for incoming calls if targeting a user room
        if data.get('type') == 'call_offer' and self.room_name.startswith('user_'):
            try:
                target_user_id = self.room_name.replace('user_', '')
                sender = self.scope.get('user')
                sender_name = sender.username if (sender and not sender.is_anonymous) else data.get('sender_name', 'Someone')
                sender_id = sender.id if (sender and not sender.is_anonymous) else 0
                
                from notifications.utils import notify_user_background
                
                # Determine media type for the notification message
                media_type = data.get('mediaType', 'voice')
                msg_text = f"Incoming {media_type} call from {sender_name}"
                
                print(f"FCM: Triggering call notification for user {target_user_id} from {sender_name}")
                
                notify_user_background(
                    user_id=target_user_id,
                    room_id=self.room_name,
                    message=msg_text,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    notification_type="call_offer",
                    extra_data={
                        "media_type": media_type,
                        "room_id": self.room_name,
                        "is_video": "true" if media_type == 'video' else "false"
                    }
                )
            except Exception as e:
                print(f"FCM ERROR in CallConsumer: {e}")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal_message',
                'message': data,
                'sender': self.channel_name
            }
        )

    async def signal_message(self, event):
        message = event['message']
        
        # Don't send peer_joined notification to the person who just joined
        if message.get('type') == 'peer_joined' and message.get('sender_channel') == self.channel_name:
            return

        # Don't send back to sender for other messages
        if self.channel_name != event['sender']:
            await self.send(text_data=json.dumps(message))
