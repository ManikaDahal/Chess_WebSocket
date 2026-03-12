from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    """Chat room for two or more users"""
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'call_chatroom'

class Message(models.Model):
    """Stores chat messages"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} in {self.room.id}: {self.text[:20]}"

    class Meta:
        db_table = 'call_message'

class MessageReaction(models.Model):
    """Stores user reactions (emojis) to chat messages"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10) # Emoji or reaction key
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user') # One reaction per user per message
        db_table = 'call_messagereaction'

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to {self.message.id}"
