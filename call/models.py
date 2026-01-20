from django.contrib.auth.models import User
from django.db import models

#Chess Invite
class Invite(models.Model):
    from_user=models.IntegerField()
    to_user=models.IntegerField()
    status=models.CharField(max_length=10, default='pending')
    created_at=models.DateTimeField(auto_now_add=True)

#Game Room
class ChessRoom(models.Model):
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player1_games')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player2_games')
    moves=models.JSONField(default=list)
    current_turn = models.ForeignKey(User, on_delete=models.CASCADE, related_name='current_turn_games')
    status=models.CharField(max_length=20,default='ongoing')
    created_at=models.DateTimeField(auto_now_add=True)


    

