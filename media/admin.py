from django.contrib import admin
from .models import GameVideo, VideoComment, VideoReaction, CallRecording, UserVoiceProfile, VoiceResponseCache

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

admin.site.register(VideoComment)
admin.site.register(VideoReaction)

@admin.register(CallRecording)
class CallRecordingAdmin(admin.ModelAdmin):
    list_display = ('user', 'room_id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'room_id')
    readonly_fields = ('created_at',)

@admin.register(UserVoiceProfile)
class UserVoiceProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_trained', 'created_at', 'updated_at')
    list_filter = ('is_trained', 'created_at')
    search_fields = ('user__username', 'elevenlabs_voice_id', 'siliconflow_voice_uri')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VoiceResponseCache)
class VoiceResponseCacheAdmin(admin.ModelAdmin):
    list_display = ('user', 'text_hash', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text_hash')
    readonly_fields = ('created_at',)
