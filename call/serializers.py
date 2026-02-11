from rest_framework import serializers
from .models import GameVideo


class GameVideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    stream_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GameVideo
        fields = [
            'id', 'title', 'description', 'video_file', 'thumbnail',
            'duration', 'file_size', 'views', 'created_at', 'updated_at',
            'video_url', 'thumbnail_url', 'stream_url'
        ]
        read_only_fields = ['views', 'created_at', 'updated_at']
    
    def get_video_url(self, obj):
        request = self.context.get('request')
        if obj.video_file and request:
            return request.build_absolute_uri(obj.video_file.url)
        return None
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_stream_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/videos/{obj.id}/stream/')
        return None
