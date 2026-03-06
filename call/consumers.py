# WebSocket Consumer for Call Signaling
# Copied from main project - handles real-time call signaling between users

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

        # Notify others in the room - ONLY if it's a private game/user room
        if self.room_name.startswith("user_") or self.room_name.startswith("game_call_"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'signal_message',
                    'message': {
                        'type': 'peer_joined',
                        'sender': 'system', # Identified as system to avoid client-side self-filtering
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
