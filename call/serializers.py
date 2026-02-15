from rest_framework import serializers
from .models import GameVideo, VideoComment, VideoReaction


class VideoCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = VideoComment
        fields = ['id', 'user_id', 'user_name', 'text', 'created_at']

class GameVideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    stream_url = serializers.SerializerMethodField()
    reaction_counts = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    
    class Meta:
        model = GameVideo
        fields = [
            'id', 'title', 'description', 'video_file', 'thumbnail',
            'duration', 'file_size', 'views', 'created_at', 'updated_at',
            'video_url', 'thumbnail_url', 'stream_url',
            'reaction_counts', 'user_reaction'
        ]
        read_only_fields = ['views', 'created_at', 'updated_at']
    
    def get_video_url(self, obj):
        if obj.video_file:
            url = obj.video_file.url
            # CRITICAL FIX: If the URL already has a scheme (http/https) or is protocol-relative (//),
            # DO NOT use build_absolute_uri. This prevents the "Double URL" bug.
            if url.startswith(('http:', 'https:', '//')):
                # CLOUDINARY HARDENING: Force H.264 Baseline Profile for sensitive consumers (Xiaomi)
                if 'res.cloudinary.com' in url and '/video/upload/' in url and 'vc_h264' not in url:
                    url = url.replace('/video/upload/', '/video/upload/q_auto,vc_h264:baseline:3.0/')
                return url
            
            request = self.context.get('request')
            if request:
                absolute_url = request.build_absolute_uri(url)
                print(f"DEBUG: Serializing Relative Video URL: {url} -> {absolute_url}")
                return absolute_url
            return url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            url = obj.thumbnail.url
            if url.startswith(('http:', 'https:', '//')):
                return url
            
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(url)
            return url
        return None
    
    def get_stream_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/videos/{obj.id}/stream/')
        return None

    def get_reaction_counts(self, obj):
        from django.db.models import Count
        return dict(
            obj.reactions.values('reaction_type').annotate(count=Count('id')).values_list('reaction_type', 'count')
        )

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            if reaction:
                return reaction.reaction_type
        return None
