# WebSocket URL routing for call signaling
# Defines the WebSocket endpoint: /ws/call/{room_name}/

from call.chatconsumers import ChatConsumer
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/call/(?P<room_name>[^/]+)/?$', consumers.CallConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_id>[^/]+)/?$', ChatConsumer.as_asgi()),
]
