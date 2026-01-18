# WebSocket URL routing for call signaling
# Defines the WebSocket endpoint: /ws/call/{room_name}/

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/call/(?P<room_name>\w+)/$', consumers.CallConsumer.as_asgi()),
]
