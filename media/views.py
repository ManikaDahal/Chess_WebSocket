from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CallRecording

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_recording(request):
    """Upload a call recording to Cloudinary."""
    room_id = request.data.get('room_id')
    recording_file = request.FILES.get('file')

    if not room_id or not recording_file:
        return Response(
            {"error": "room_id and file are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        recording = CallRecording.objects.create(
            user=request.user,
            room_id=room_id,
            file=recording_file
        )
        return Response(
            {"message": "Recording uploaded successfully.", "id": recording.id, "url": recording.file.url},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {"error": f"Upload failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
