from django.contrib import admin
from .models import ChatRoom, Message, Notification

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    filter_horizontal = ('users',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'text', 'timestamp', 'is_read')
    list_filter = ('room', 'sender', 'is_read')
    search_fields = ('text', 'sender__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'sender', 'room', 'message', 'created_at')
    list_filter = ('user', 'sender', 'room')
