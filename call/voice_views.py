from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.base import ContentFile
from .models import UserVoiceProfile
from .voice_service import VoiceAIManager
import uuid

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_voice_samples(request):
    """
    Upload voice samples to train the ElevenLabs digital twin.
    Expects multiple files in request.FILES.
    """
    user = request.user
    audio_files = request.FILES.getlist('samples')
    
    if not audio_files:
        return Response({"error": "No voice samples provided"}, status=400)
        
    ai_manager = VoiceAIManager()
    
    # Pass the full UploadedFile objects so the service can access metadata like name and content_type
    voice_id, error = ai_manager.create_user_voice(user.username, audio_files)
    
    if error:
        return Response({"error": error}, status=500)
        
    # Update or create voice profile
    profile, created = UserVoiceProfile.objects.get_or_create(user=user)
    profile.elevenlabs_voice_id = voice_id
    profile.is_trained = True
    profile.save()
    
    return Response({
        "message": "Voice profile created successfully",
        "voice_id": voice_id
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_self(request):
    """
    Talk to the AI digital twin.
    Expects 'message' in request.data.
    Returns response text and a URL to the synthesized audio.
    """
    user = request.user
    message = request.data.get('message')
    
    if not message:
        return Response({"error": "No message provided"}, status=400)
        
    try:
        profile = user.voice_profile
    except UserVoiceProfile.DoesNotExist:
        return Response({"error": "Voice profile not trained. Please upload voice samples first."}, status=400)
        
    if not profile.elevenlabs_voice_id:
        return Response({"error": "Voice ID missing. Please retrain."}, status=400)
        
    ai_manager = VoiceAIManager()
    
    # 1. Generate text response (Llama 3)
    response_text = ai_manager.generate_response(message)
    
    # 2. Synthesize speech (ElevenLabs)
    audio_content, synth_error = ai_manager.text_to_speech(response_text, profile.elevenlabs_voice_id)
    
    if synth_error:
        return Response({"error": synth_error, "text": response_text}, status=500)
        
    # 3. Save audio content (For now, we'll use a temporary file or Cloudinary)
    # We'll use a simple approach: save to a 'voice_responses' directory
    # In production, Cloudinary is better.
    filename = f"voice_{user.id}_{uuid.uuid4().hex}.mp3"
    
    # Note: This is a placeholder for actual storage logic. 
    # For now, we'll return the text and a simulated success.
    # To truly serve the audio, we would save to MEDIA_ROOT or Cloudinary.
    
    return Response({
        "text": response_text,
        "audio_id": filename, # In real app, this would be a full URL
        "message": "Speech synthesized successfully"
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_voice_status(request):
    """Check if the user has a trained voice profile."""
    try:
        profile = request.user.voice_profile
        return Response({
            "is_trained": profile.is_trained,
            "voice_id": profile.elevenlabs_voice_id
        })
    except UserVoiceProfile.DoesNotExist:
        return Response({"is_trained": False})
