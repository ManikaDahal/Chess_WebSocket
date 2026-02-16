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
            if not url or '/video/upload/' not in url:
                return url
            
            # SAFE NASA PROFILE: Baseline 3.0 + 1Mbps Bitrate + Auto Quality
            safe_profile = 'q_auto,vc_h264:baseline:3.0,br_1m'
            
            # ABSOLUTE INTERCEPTOR: Force everything to res.cloudinary.com to guarantee transformation works
            # This bypasses local/proxied paths that might be unhardened.
            from django.conf import settings
            cloud_name = getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME') or "drxgymnwa"
            base_cloud = f"https://res.cloudinary.com/{cloud_name}"
            
            try:
                # Extract the path from /video/upload/ onwards
                path_part = url.split('/video/upload/')[-1]
                parts = [p for p in path_part.split('/') if p]
                
                new_parts = [safe_profile]
                
                # Check for version number (v1234...)
                version = None
                for p in parts[:-1]:
                    if p.startswith('v') and p[1:].isdigit():
                        version = p
                        break
                
                if version:
                    new_parts.append(version)
                
                # Always keep the actual filename (last part)
                new_parts.append(parts[-1])
                
                return f"{base_cloud}/video/upload/{'/'.join(new_parts)}"
            except Exception as e:
                print(f"DEBUG: Hardening failed for {url}: {e}")
                return url

        if obj.video_file:
            # Field property .url might return relative or absolute depending on env
            return _harden_url(obj.video_file.url)
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
