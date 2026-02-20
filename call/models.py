from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class ChatRoom(models.Model):
    """Chat room for two or more users"""
    users=models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_at=models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    """Stores chat messages"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text= models.TextField()
    timestamp=models.DateTimeField(auto_now_add=True)
    is_read=models.BooleanField(default=False)

class Notification(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message=models.TextField()
    sender=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender")
    room=models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

class GameInvite(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_invites")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_invites")
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"

class GameMove(models.Model):
    room_id = models.IntegerField()
    from_row = models.IntegerField()
    from_col = models.IntegerField()
    to_row = models.IntegerField()
    to_col = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Move in room {self.room_id}: ({self.from_row},{self.from_col}) -> ({self.to_row},{self.to_col})"

class GameVideo(models.Model):
    """Stores chess tutorial/gameplay videos"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_file = CloudinaryField('video', resource_type='video')
    thumbnail = models.ImageField(upload_to='video_thumbnails/', null=True, blank=True)
    duration = models.IntegerField(help_text="Duration in seconds", default=0)
    file_size = models.BigIntegerField(help_text="File size in bytes", default=0)
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class VideoComment(models.Model):
    video = models.ForeignKey(GameVideo, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.video}"

class VideoReaction(models.Model):
    REACTION_TYPES = [
        ('like', 'Like'),
        ('heart', 'Heart'),
        ('laugh', 'Laugh'),
        ('surprised', 'Surprised'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
    ]
    video = models.ForeignKey(GameVideo, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('video', 'user')

    def __str__(self):
        return f"{self.user} reacted {self.reaction_type} to {self.video}"

class UserVoiceProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voice_profile')
    elevenlabs_voice_id = models.CharField(max_length=100, blank=True, null=True)
    siliconflow_voice_uri = models.CharField(max_length=255, blank=True, null=True) # Used for SiliconFlow Zero-Shot
    reference_audio = CloudinaryField('audio', resource_type='video', null=True, blank=True) # Used for fallback/storage
    is_trained = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Voice Profile for {self.user.username}"

class VoiceResponseCache(models.Model):
    """Caches synthesized audio to prevent redundant API calls"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text_hash = models.CharField(max_length=64, db_index=True) # SHA-256 of text
    audio_file = CloudinaryField('audio', resource_type='video')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'text_hash')
        ordering = ['-created_at']

    def __str__(self):
        return f"Cache for {self.user.username} - {self.text_hash[:8]}"

class CallRecording(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='call_recordings')
    room_id = models.CharField(max_length=255)
    file = CloudinaryField('video', resource_type='video')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recording by {self.user.username} in {self.room_id} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']