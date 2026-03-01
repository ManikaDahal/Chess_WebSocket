from django.contrib import admin
from .models import ChatRoom, Message, Notification, GameInvite, GameMove, GameVideo, VideoComment, VideoReaction, CallRecording, NotificationLog

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
        import sys
        try:
            # Auto-calculate file size if video file exists
            if obj.video_file:
                try:
                    # Cloudinary field doesn't have .size immediately available in the same way locally
                    # But we can try to get it if available, or just skip it for now
                    if hasattr(obj.video_file, 'size'):
                         obj.file_size = obj.video_file.size
                except Exception as e:
                    sys.stderr.write(f"WARNING: Error calculating file size: {e}\n")
            
            # Print debug info before saving
            sys.stderr.write(f"DEBUG: Attempting to save video '{obj.title}'...\n")
            super().save_model(request, obj, form, change)
            sys.stderr.write(f"DEBUG: Successfully saved video '{obj.title}'\n")
            
        except Exception as e:
            # Log critical error to stderr (always visible in Render logs)
            sys.stderr.write(f"CRITICAL ERROR SAVING VIDEO: {e}\n")
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise e

# Register other models
admin.site.register(GameInvite)
admin.site.register(GameMove)
admin.site.register(VideoComment)
admin.site.register(VideoReaction)

@admin.register(CallRecording)
class CallRecordingAdmin(admin.ModelAdmin):
    list_display = ('user', 'room_id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'room_id')
    readonly_fields = ('created_at',)

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_id', 'title', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'title', 'message_id', 'body')
    readonly_fields = ('created_at', 'updated_at')

    def changelist_view(self, request, extra_context=None):
        # Aggregate statistics
        from django.db.models import Count
        from .models import NotificationLog
        
        stats = NotificationLog.objects.values('status').annotate(total=Count('status'))
        total_count = NotificationLog.objects.count()
        
        summary = {
            'total': total_count,
            'sent': 0,
            'delivered': 0,
            'opened': 0,
            'failed': 0,
        }
        
        for s in stats:
            summary[s['status']] = s['total']
            
        # Calculate rates
        if total_count > 0:
            summary['delivery_rate'] = round((summary['delivered'] + summary['opened']) / total_count * 100, 2)
            summary['open_rate'] = round(summary['opened'] / total_count * 100, 2)
        else:
            summary['delivery_rate'] = 0
            summary['open_rate'] = 0

        extra_context = extra_context or {}
        extra_context['notification_summary'] = summary
        
        return super().changelist_view(request, extra_context=extra_context)
