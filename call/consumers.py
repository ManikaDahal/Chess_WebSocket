import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CallSignalingConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"call_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        print(f"✅ Connected to {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"❌ Disconnected from {self.room_group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Ignore ping
        if data.get("type") == "ping":
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "signal.message",
                "message": data,
                "sender": self.channel_name,
            }
        )

    async def signal_message(self, event):
        if event["sender"] != self.channel_name:
            await self.send(text_data=json.dumps(event["message"]))
