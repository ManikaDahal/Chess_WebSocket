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
            if not url.startswith('http') and not url.startswith('//'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(url)
            return url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            url = obj.thumbnail.url
            if not url.startswith('http') and not url.startswith('//'):
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
