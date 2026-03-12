from django.urls import re_path
from media.consumers import CallConsumer
from chat.consumers import ChatConsumer
from game.consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r'ws/call/(?P<room_name>[^/]+)/?$', CallConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_id>[^/]+)/(?P<user_id>[^/]+)/?$', ChatConsumer.as_asgi()),
    re_path(r'ws/game/(?P<room_id>[^/]+)/?$', GameConsumer.as_asgi()),
]
