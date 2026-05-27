"""
Episode model for SafePlace application
"""
import re

from django.db import models
from .category import Category


class Episode(models.Model):
    """Model for podcast and video episodes"""
    TYPE_CHOICES = [('podcast', 'Podcast'), ('video', 'Vidéo')]
    MAX_TYPE_LENGTH = 10
    MAX_DURATION_LENGTH = 10

    title = models.CharField(max_length=200)
    description = models.TextField()
    episode_type = models.CharField(max_length=MAX_TYPE_LENGTH, choices=TYPE_CHOICES, default='podcast')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    audio_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='videos/%Y/%m/', blank=True, null=True, verbose_name='Fichier vidéo local')
    duration = models.CharField(max_length=MAX_DURATION_LENGTH, blank=True)
    host = models.CharField(max_length=100, blank=True, default='The SafePlace by K')
    cover_color = models.CharField(max_length=7, default='#00261b')
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_youtube_embed_url(self):
        """Return a youtube.com/embed/... URL for iframe, or empty string."""
        if not self.video_url:
            return ''
        url = (self.video_url or '').strip()
        m = re.search(
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            url,
        )
        if m:
            return f'https://www.youtube.com/embed/{m.group(1)}'
        return ''

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Épisode"
        verbose_name_plural = "Épisodes"
