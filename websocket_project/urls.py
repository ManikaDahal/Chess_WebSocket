# URL Configuration for WebSocket project
# This project ONLY handles WebSocket connections, no REST API endpoints

from django.urls import path


def home(request):
    return HttpResponse("WebSocket is running successfully ")
urlpatterns = [
    # No REST API endpoints - all handled by Vercel deployment
    path('', home),
]
