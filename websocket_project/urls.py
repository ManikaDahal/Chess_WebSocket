# URL Configuration for WebSocket project
# This project ONLY handles WebSocket connections, no REST API endpoints
from django.contrib import admin 
from django.urls import path
from django.http import HttpResponse 
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve


from chat.views import chat_history, get_or_create_private_room
from game.views import send_invite, accept_invite, decline_invite, pending_invites
from media.views import upload_recording
from media.video_views import list_videos, get_video_detail, stream_video, upload_video, delete_video, video_comments, toggle_reaction
from media.voice_views import upload_voice_samples, chat_with_self, get_voice_status, delete_voice_profile
from notifications.views import update_notification_status, get_notification_preferences, update_notification_preference

def home(request):
    return HttpResponse("WebSocket is running successfully ")

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    # No REST API endpoints - all handled by Vercel deployment
    path('trigger-error/', trigger_error, name='trigger-error'),
    path('admin/', admin.site.urls),
    path('api/chat/history/<int:room_id>/', chat_history),
    path('api/chat/get_or_create_room/', get_or_create_private_room),
    path('api/send-invite/', send_invite),
    path('api/accept-invite/', accept_invite),
    path('api/decline-invite/', decline_invite),
    path('api/pending-invites/', pending_invites),
    path('api/call/upload/', upload_recording, name='recording-upload'),
    path('api/notifications/update-status/', update_notification_status, name='update-notification-status'),
    path('api/notifications/preferences/', get_notification_preferences, name='get-notification-preferences'),
    path('api/notifications/preferences/update/', update_notification_preference, name='update-notification-preference'),
    
    # Video API endpoints
    path('api/videos/', list_videos, name='list_videos'),
    path('api/videos/<int:video_id>/', get_video_detail, name='video_detail'),
    path('api/videos/<int:video_id>/stream/', stream_video, name='stream_video'),
    path('api/videos/upload/', upload_video, name='upload_video'),
    path('api/videos/<int:video_id>/delete/', delete_video, name='delete_video'),
    path('api/videos/<int:video_id>/comments/', video_comments, name='video_comments'),
    path('api/videos/<int:video_id>/react/', toggle_reaction, name='toggle_reaction'),
    
    # AI Voice Cloning Endpoints
    path('api/voice/upload-samples/', upload_voice_samples, name='upload_voice_samples'),
    path('api/voice/chat-self/', chat_with_self, name='chat_with_self'),
    path('api/voice/status/', get_voice_status, name='get_voice_status'),
    path('api/voice/delete-profile/', delete_voice_profile, name='delete_voice_profile'),

    
    path('', home),
]

# Standard way to serve media files in Django
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, WhiteNoise handles STATIC_URL automatically.
    # If using local media storage in production (non-Cloudinary), we still need this:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
