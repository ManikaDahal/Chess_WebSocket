from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.base import ContentFile
from .models import UserVoiceProfile, VoiceResponseCache
from .voice_service import VoiceAIManager, SiliconFlowManager
import uuid
import hashlib
from django.db import transaction
import os

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_voice_samples(request):
    """
    Upload voice samples. One is saved to Cloudinary as a reference for SiliconFlow.
    """
    user = request.user
    audio_files = request.FILES.getlist('samples')
    
    if not audio_files:
        return Response({"error": "No voice samples provided"}, status=400)
    
    # 1. Update or create voice profile
    profile, created = UserVoiceProfile.objects.get_or_create(user=user)
    
    # 2. Save the first sample to Cloudinary as our persistent reference
    # CloudinaryField handles the upload automatically when assigned a file object
    profile.reference_audio = audio_files[0]
    profile.is_trained = True
    profile.save()
    
    # 3. (Optional) Still try ElevenLabs if key exists, but don't block on it
    ai_manager = VoiceAIManager()
    if os.environ.get('ELEVENLABS_API_KEY'):
        voice_id, error = ai_manager.create_user_voice(user.username, audio_files)
        if not error:
            profile.elevenlabs_voice_id = voice_id
            profile.save()

    return Response({
        "message": "Voice profile created successfully",
        "reference_url": profile.reference_audio.url if profile.reference_audio else None
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_voice_profile(request):
    """Securely delete user samples and profile"""
    user = request.user
    try:
        profile = user.voice_profile
        # Note: CloudinaryField deletion typically happens on model delete 
        # but we can also manually clear the field if we want to keep the profile record
        profile.delete()
        VoiceResponseCache.objects.filter(user=user).delete()
        return Response({"message": "Voice profile and samples deleted successfully"})
    except UserVoiceProfile.DoesNotExist:
        return Response({"error": "No voice profile found"}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_self(request):
    user = request.user
    message = request.data.get('message', '').strip()
    
    if not message:
        return Response({"error": "No message provided"}, status=400)
    
    try:
        profile = user.voice_profile
    except UserVoiceProfile.DoesNotExist:
        return Response({"error": "Voice profile not trained."}, status=400)
    
    # 1. Caching Check: Has this user said this before?
    text_hash = hashlib.sha256(message.lower().encode()).hexdigest()
    cache_entry = VoiceResponseCache.objects.filter(user=user, text_hash=text_hash).first()
    
    ai_manager = VoiceAIManager()
    sf_manager = SiliconFlowManager()

    # 2. Generate text response
    response_text = ai_manager.generate_response(message)
    
    # 3. Audio Generation (from Cache, ElevenLabs, or SiliconFlow)
    audio_url = None
    if cache_entry:
        print(f"DEBUG: Cache hit for message hash {text_hash}")
        audio_url = cache_entry.audio_file.url
    else:
        audio_content = None
        # Try ElevenLabs first if previously successful
        if profile.elevenlabs_voice_id:
            audio_content, error = ai_manager.text_to_speech(response_text, profile.elevenlabs_voice_id)
        
        # Fallback to SiliconFlow (Free/Low Cost)
        if not audio_content and profile.reference_audio:
            audio_content, error = sf_manager.zero_shot_tts(response_text, profile.reference_audio.url)
            
        if audio_content:
            # Save to Cloudinary for caching
            filename = f"voice_{user.id}_{uuid.uuid4().hex}.mp3"
            new_cache = VoiceResponseCache.objects.create(
                user=user,
                text_hash=text_hash,
                audio_file=ContentFile(audio_content, name=filename)
            )
            audio_url = new_cache.audio_file.url

    return Response({
        "text": response_text,
        "audio_url": audio_url,
        "is_cached": cache_entry is not None
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
