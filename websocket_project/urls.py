# URL Configuration for WebSocket project
# This project ONLY handles WebSocket connections, no REST API endpoints
from django.contrib import admin 
from django.urls import path
from django.http import HttpResponse 


from call.views import chat_history, get_or_create_private_room, send_invite, accept_invite, decline_invite, pending_invites

def home(request):
    return HttpResponse("WebSocket is running successfully ")
urlpatterns = [
    # No REST API endpoints - all handled by Vercel deployment
    path('admin/', admin.site.urls),
    path('api/chat/history/<int:room_id>/', chat_history),
    path('api/chat/get_or_create_room/', get_or_create_private_room),
    path('api/send-invite/', send_invite),
    path('api/accept-invite/', accept_invite),
    path('api/decline-invite/', decline_invite),
    path('api/pending-invites/', pending_invites),
    path('', home),
]
