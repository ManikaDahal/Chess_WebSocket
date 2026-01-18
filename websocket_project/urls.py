# URL Configuration for WebSocket project
# This project ONLY handles WebSocket connections, no REST API endpoints
from django.contrib import admin 
from django.urls import path
from django.http import HttpResponse 


def home(request):
    return HttpResponse("WebSocket is running successfully ")
urlpatterns = [
    # No REST API endpoints - all handled by Vercel deployment
    path('admin/', admin.site.urls),
    path('', home),
]
