import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameMove

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Fetch and send history
        history = await self.get_game_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'history': history,
            'room_id': self.room_id
        }))
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'room_id': self.room_id
        }))
        print(f"[GAME] User connected to room {self.room_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"[GAME] User DISCONNECTED from room {self.room_id} (code: {close_code})")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'move':
            # Save move to database
            await self.save_move(data)
            
            # Add room info to help client filtering
            data['room_id'] = self.room_id
            print(f"BROADCAST [Room {self.room_id}]: Move from {self.channel_name} -> {data}")
            
            # Broadcast move to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_move',
                    'move_data': data,
                    'sender_channel_name': self.channel_name
                }
            )
        elif message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'room_id': self.room_id
            }))
        elif message_type == 'reset':
             await self.clear_history()
             
             await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_reset',
                    'sender_channel_name': self.channel_name
                }
            )
        elif message_type == 'join':
            user_id = data.get('user_id')
            print(f"BROADCAST [Room {self.room_id}]: Player joined {user_id}")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_joined',
                    'room_id': self.room_id,
                    'user_id': user_id
                }
            )

    @database_sync_to_async
    def save_move(self, data):
        try:
            rid = int(self.room_id)
            GameMove.objects.create(
                room_id=rid,
                from_row=data['from_row'],
                from_col=data['from_col'],
                to_row=data['to_row'],
                to_col=data['to_col']
            )
        except Exception as e:
            print(f"Error saving move to DB: {e}")

    @database_sync_to_async
    def get_game_history(self):
        try:
            rid = int(self.room_id)
            moves = GameMove.objects.filter(room_id=rid).order_by('timestamp')
            return [
                {
                    'from_row': m.from_row,
                    'from_col': m.from_col,
                    'to_row': m.to_row,
                    'to_col': m.to_col
                }
                for m in moves
            ]
        except Exception as e:
            print(f"Error fetching game history: {e}")
            return []

    @database_sync_to_async
    def clear_history(self):
        try:
            rid = int(self.room_id)
            GameMove.objects.filter(room_id=rid).delete()
        except Exception as e:
            print(f"Error clearing history: {e}")

    async def game_move(self, event):
        print(f"DELIVERING [Room {self.room_id}] to {self.channel_name}")
        await self.send(text_data=json.dumps(event['move_data']))

    async def game_reset(self, event):
        await self.send(text_data=json.dumps({'type': 'reset'}))

    async def player_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_joined', 
            'room_id': event['room_id'],
            'user_id': event.get('user_id')
        }))
