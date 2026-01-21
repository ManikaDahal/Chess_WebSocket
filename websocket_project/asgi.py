import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# Lazy import to avoid AppRegistryNotReady
def get_application():
    from call.routing import websocket_urlpatterns
    return ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })

application = get_application()
