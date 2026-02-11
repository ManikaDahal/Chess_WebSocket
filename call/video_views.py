from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse, Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from .models import GameVideo
from .serializers import GameVideoSerializer
import os
import mimetypes


@api_view(['GET'])
@permission_classes([AllowAny])
def list_videos(request):
    """List all available videos"""
    videos = GameVideo.objects.all()
    serializer = GameVideoSerializer(videos, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_video_detail(request, video_id):
    """Get details of a specific video"""
    video = get_object_or_404(GameVideo, id=video_id)
    
    # Increment view count
    video.views += 1
    video.save(update_fields=['views'])
    
    serializer = GameVideoSerializer(video, context={'request': request})
    return Response(serializer.data)


class RangeFileWrapper:
    """Wrapper to support range requests for video streaming"""
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration
        else:
            if self.remaining <= 0:
                raise StopIteration
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration
            self.remaining -= len(data)
            return data


@api_view(['GET'])
@permission_classes([AllowAny])
def stream_video(request, video_id):
    """
    Redirect to the Cloudinary URL for streaming.
    Cloudinary handles range requests and streaming efficiently.
    """
    video = get_object_or_404(GameVideo, id=video_id)
    
    if not video.video_file:
        raise Http404("Video file not found")
        
    # Redirect to the external Cloudinary URL
    from django.shortcuts import redirect
    return redirect(video.video_file.url)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_video(request):
    """Upload a new video (admin only)"""
    if not request.user.is_staff:
        return Response(
            {"error": "Only administrators can upload videos"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = GameVideoSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_video(request, video_id):
    """Delete a video (admin only)"""
    if not request.user.is_staff:
        return Response(
            {"error": "Only administrators can delete videos"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    video = get_object_or_404(GameVideo, id=video_id)
    
    # Delete from Cloudinary
    if video.video_file:
        import cloudinary.uploader
        # CloudinaryField stores the public_id
        try:
            cloudinary.uploader.destroy(video.video_file.public_id, resource_type='video')
        except Exception as e:
            print(f"Error deleting video from Cloudinary: {e}")

    if video.thumbnail:
        try:
            cloudinary.uploader.destroy(video.thumbnail.public_id)
        except Exception as e:
            print(f"Error deleting thumbnail from Cloudinary: {e}")
    
    video.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
