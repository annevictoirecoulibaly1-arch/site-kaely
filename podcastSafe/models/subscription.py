"""
Subscription model for SafePlace application
"""
from django.db import models


class Subscription(models.Model):
    """Model for free notification subscriptions"""
    
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Nom")
    email = models.EmailField(unique=True, verbose_name="Adresse e-mail")
    photo_url = models.URLField(blank=True, null=True, verbose_name="URL photo de profil")
    
    # Notification preferences
    notify_podcasts = models.BooleanField(default=True, verbose_name="Notifier pour les podcasts")
    notify_live = models.BooleanField(default=True, verbose_name="Notifier pour les lives")
    notify_videos = models.BooleanField(default=False, verbose_name="Notifier pour les vidéos")
    
    is_active = models.BooleanField(default=True, verbose_name="Abonnement actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-created_at']
