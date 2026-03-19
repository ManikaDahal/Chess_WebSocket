from django.db import models
from django.conf import settings

class GameInvite(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_invites")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_invites")
    room = models.ForeignKey('chat.ChatRoom', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    game_type = models.CharField(max_length=20, default='chess') # 'chess' or 'snake'
    board_id = models.IntegerField(null=True, blank=True) # For snake game specifically
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"

    class Meta:
        db_table = 'call_gameinvite'

class GameMove(models.Model):
    room_id = models.IntegerField()
    from_row = models.IntegerField()
    from_col = models.IntegerField()
    to_row = models.IntegerField()
    to_col = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        db_table = 'call_gamemove'

    def __str__(self):
        return f"Move in room {self.room_id}: ({self.from_row},{self.from_col}) -> ({self.to_row},{self.to_col})"
