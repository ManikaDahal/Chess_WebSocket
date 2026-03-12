from django.contrib import admin
from .models import Notification, NotificationLog, NotificationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'sender', 'room', 'message', 'created_at')
    list_filter = ('user', 'sender', 'room')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'short_body', 'category', 'status', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('user__username', 'title', 'message_id', 'body')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Body')
    def short_body(self, obj):
        return (obj.body[:80] + '…') if len(obj.body) > 80 else obj.body

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'is_blocked', 'updated_at')
    list_filter = ('category', 'is_blocked')
    search_fields = ('user__username',)
    readonly_fields = ('updated_at',)
