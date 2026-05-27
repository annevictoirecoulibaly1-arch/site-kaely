"""
Category model for SafePlace application
"""
from django.db import models


class Category(models.Model):
    TYPE_CHOICES = [
        ('podcast', 'Podcast'),
        ('video',   'Vidéo'),
        ('all',     'Tous'),
    ]

    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='church')
    color = models.CharField(max_length=30, default='#00261b', help_text='Couleur principale hex')
    for_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='all')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Catégories"
        ordering = ['for_type', 'name']
