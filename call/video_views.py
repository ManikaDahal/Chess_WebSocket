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
    """Stream video with range request support for seeking"""
    video = get_object_or_404(GameVideo, id=video_id)
    
    if not video.video_file:
        raise Http404("Video file not found")
    
    video_path = video.video_file.path
    
    if not os.path.exists(video_path):
        raise Http404("Video file does not exist")
    
    # Get file size
    file_size = os.path.getsize(video_path)
    
    # Get content type
    content_type, _ = mimetypes.guess_type(video_path)
    if not content_type:
        content_type = 'video/mp4'
    
    # Handle range requests
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = None
    
    if range_header:
        import re
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
    
    if range_match:
        # Partial content request
        start = int(range_match.group(1))
        end = range_match.group(2)
        end = int(end) if end else file_size - 1
        length = end - start + 1
        
        resp = StreamingHttpResponse(
            RangeFileWrapper(open(video_path, 'rb'), offset=start, length=length),
            status=206,
            content_type=content_type
        )
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    else:
        # Full file request
        resp = FileResponse(
            open(video_path, 'rb'),
            content_type=content_type
        )
        resp['Content-Length'] = str(file_size)
    
    resp['Accept-Ranges'] = 'bytes'
    resp['Cache-Control'] = 'no-cache'
    
    return resp


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
    
    # Delete the actual file
    if video.video_file:
        if os.path.exists(video.video_file.path):
            os.remove(video.video_file.path)
    
    if video.thumbnail:
        if os.path.exists(video.thumbnail.path):
            os.remove(video.thumbnail.path)
    
    video.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
