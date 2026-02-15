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
        def _harden_url(url):
            if 'res.cloudinary.com' in url and '/video/upload/' in url:
                import re
                # SAFE NASA PROFILE: Baseline 3.0 + 1Mbps Bitrate + Auto Quality
                safe_profile = 'q_auto,vc_h264:baseline:3.0,br_1m/'
                if '/v' in url and re.search(r'/v\d+/', url):
                    # Replace existing transformations if any
                    return re.sub(r'/video/upload/.*?(/v\d+/)', f'/video/upload/{safe_profile}\\1', url)
                elif 'vc_h264' not in url:
                    return url.replace('/video/upload/', f'/video/upload/{safe_profile}')
            return url

        if obj.video_file:
            url = obj.video_file.url
            if url.startswith(('http:', 'https:', '//')):
                return _harden_url(url)
            
            request = self.context.get('request')
            if request:
                return _harden_url(request.build_absolute_uri(url))
            return _harden_url(url)
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
        # BYPASS PROXY: Serve the hardened Cloudinary URL directly for better hardware performance
        return self.get_video_url(obj)

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
