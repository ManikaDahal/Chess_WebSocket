# URL Configuration for WebSocket project
# This project ONLY handles WebSocket connections, no REST API endpoints
from django.contrib import admin 
from django.urls import path
from django.http import HttpResponse 
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve


from call.views import chat_history, get_or_create_private_room, send_invite, accept_invite, decline_invite, pending_invites
from call.video_views import list_videos, get_video_detail, stream_video, upload_video, delete_video

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
    
    # Video API endpoints
    path('api/videos/', list_videos, name='list_videos'),
    path('api/videos/<int:video_id>/', get_video_detail, name='video_detail'),
    path('api/videos/<int:video_id>/stream/', stream_video, name='stream_video'),
    path('api/videos/upload/', upload_video, name='upload_video'),
    path('api/videos/<int:video_id>/delete/', delete_video, name='delete_video'),
    
    path('', home),
    # Serve media files (videos, thumbnails) in PRODUCTION (since we don't have S3 yet)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
