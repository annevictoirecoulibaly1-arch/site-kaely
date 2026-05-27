"""
LiveStream model for SafePlace application
"""
from django.db import models


class LiveStream(models.Model):
    """Model for live streaming events"""
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram'),
        ('spotify', 'Spotify'),
    ]
    STATUS_CHOICES = [
        ('live', 'En Direct'),
        ('scheduled', 'Programmé'),
        ('ended', 'Terminé'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    stream_url = models.URLField(blank=True)
    embed_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    viewers_count = models.IntegerField(default=0)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_platform_display()})"

    class Meta:
        verbose_name = "Live Stream"
        ordering = ['-created_at']
