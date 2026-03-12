from django.db import models
from django.conf import settings

# ---------------------------------------------------------------------------
# Notification categories — add a new tuple here to create a new category.
# Format: ('db_value', 'Human-Readable Label')
# ---------------------------------------------------------------------------
NOTIFICATION_CATEGORIES = [
    ('message',    'Chat Message'),
    ('invitation', 'Game Invitation'),
    ('system',     'System'),
]

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_sender")
    room = models.ForeignKey('chat.ChatRoom', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'call_notification'

class NotificationLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('closed', 'Closed'),
        ('blocked', 'Blocked'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_logs')
    message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    category = models.CharField(max_length=30, choices=NOTIFICATION_CATEGORIES, default='system')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        db_table = 'call_notificationlog'

class NotificationPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    category = models.CharField(max_length=30, choices=NOTIFICATION_CATEGORIES)
    is_blocked = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'category')
        ordering = ['category']
        db_table = 'call_notificationpreference'

    def __str__(self):
        state = 'BLOCKED' if self.is_blocked else 'allowed'
        return f"{self.user.username} - {self.category} ({state})"
