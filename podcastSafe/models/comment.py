from django.db import models
from .episode import Episode


class Comment(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=100, verbose_name="Nom")
    author_email = models.EmailField(blank=True, verbose_name="Email (optionnel)")
    content = models.TextField(verbose_name="Commentaire")
    is_approved = models.BooleanField(default=True, verbose_name="Approuvé")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author_name} — {self.episode.title[:40]}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
