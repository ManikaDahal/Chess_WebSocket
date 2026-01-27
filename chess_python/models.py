from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username

class FCMToken(models.Model):
    user = models.ForeignKey('chess_python.CustomUser', on_delete=models.CASCADE, related_name='fcm_tokens')
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.token[:10]}..."
