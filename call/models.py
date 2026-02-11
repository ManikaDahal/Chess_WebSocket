from django.db import models
from django.conf import settings

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
    video_file = models.FileField(upload_to='game_videos/')
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