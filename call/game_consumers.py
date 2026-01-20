from call.models import ChessRoom
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chess_{self.room_name}"  # fixed typo

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()

        # Send system message
        await self.send(text_data=json.dumps({
            "type": "system",
            "message": "Connected to game room"
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        move = data.get('move')  # fix: string key
        user_id = data.get('user_id')

        # Save move in DB
        room = ChessRoom.objects.get(id=self.room_name)
        room.moves.append(move)
        room.current_turn = room.player2 if room.current_turn == room.player1 else room.player1
        room.save()

        # Broadcast move to both players
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_move',
                'move': move,
                'user_id': user_id,
            }
        )

    async def send_move(self, event):
        await self.send(text_data=json.dumps({
            'move': event['move'],
            'user_id': event['user_id']
        }))

    async def game_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
