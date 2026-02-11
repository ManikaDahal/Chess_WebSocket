from django.contrib import admin
from .models import ChatRoom, Message, Notification, GameInvite, GameMove, GameVideo

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

@admin.register(GameVideo)
class GameVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration', 'file_size', 'views', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['views', 'created_at', 'updated_at', 'file_size']
    
    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'description')
        }),
        ('Files', {
            'fields': ('video_file', 'thumbnail')
        }),
        ('Metadata', {
            'fields': ('duration', 'file_size', 'views', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Auto-calculate file size if video file exists
        if obj.video_file:
            try:
                obj.file_size = obj.video_file.size
            except Exception as e:
                # If file size cannot be retrieved (e.g. storage issue), 
                # log it and continue without crashing
                print(f"Error calculating file size: {e}")
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            # Catch Cloudinary or other storage errors
            print(f"ERROR: Failed to save video (likely Cloudinary upload failed): {e}")
            from django.contrib import messages
            messages.set_level(request, messages.ERROR)
            messages.error(request, f"Failed to upload video: {str(e)}. Check Cloudinary credentials.")

# Register other models
admin.site.register(GameInvite)
admin.site.register(GameMove)
