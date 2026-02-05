import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"[GAME] User connected to room {self.room_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"[GAME] User disconnected from room {self.room_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'move':
            # Broadcast move to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_move',
                    'move_data': data,
                    'sender_channel_name': self.channel_name
                }
            )
        elif message_type == 'reset':
             await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_reset',
                    'sender_channel_name': self.channel_name
                }
            )

    async def game_move(self, event):
        # Send move to WebSocket except the sender
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps(event['move_data']))

    async def game_reset(self, event):
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps({'type': 'reset'}))
