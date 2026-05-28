"""
Event model for SafePlace community events (donations, ceremonies, conferences, etc.)
"""
from django.db import models
from django.utils import timezone


class Event(models.Model):
    TYPE_CHOICES = [
        ('don',        'Don'),
        ('ceremonie',  'Cérémonie'),
        ('conference', 'Conférence'),
        ('priere',     'Prière'),
        ('culte',      'Culte'),
        ('autre',      'Autre'),
    ]

    _GRADIENTS = {
        'don':        'linear-gradient(135deg,#416900,#9ff700)',
        'ceremonie':  'linear-gradient(135deg,#7B5E00,#F0B429)',
        'conference': 'linear-gradient(135deg,#0A3D6B,#1A7FC1)',
        'priere':     'linear-gradient(135deg,#4A0072,#9C27B0)',
        'culte':      'linear-gradient(135deg,#7F0000,#D32F2F)',
        'autre':      'linear-gradient(135deg,#00261b,#396756)',
    }
    _COLORS = {
        'don': '#416900', 'ceremonie': '#7B5E00',
        'conference': '#0A3D6B', 'priere': '#4A0072',
        'culte': '#7F0000', 'autre': '#00261b',
    }
    _ICONS = {
        'don': 'volunteer_activism', 'ceremonie': 'celebration',
        'conference': 'record_voice_over', 'priere': 'self_improvement',
        'culte': 'church', 'autre': 'event',
    }

    title            = models.CharField(max_length=200, verbose_name='Titre')
    description      = models.TextField(verbose_name='Description')
    event_type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default='autre', verbose_name='Type')
    event_date       = models.DateTimeField(verbose_name="Date de l'événement")
    end_date         = models.DateTimeField(null=True, blank=True, verbose_name='Date de fin')
    location         = models.CharField(max_length=200, blank=True, verbose_name='Lieu')
    is_online        = models.BooleanField(default=False, verbose_name='En ligne')
    online_url       = models.URLField(blank=True, verbose_name='Lien en ligne')
    image            = models.ImageField(upload_to='events/%Y/%m/', null=True, blank=True, verbose_name='Image')
    registration_url = models.URLField(blank=True, verbose_name="Lien d'inscription")
    is_published     = models.BooleanField(default=True, verbose_name='Publié')
    is_featured      = models.BooleanField(default=False, verbose_name='À la une')
    created_at       = models.DateTimeField(auto_now_add=True)

    # ── computed properties ────────────────────────────────────────────────────

    @property
    def gradient(self):
        return self._GRADIENTS.get(self.event_type, self._GRADIENTS['autre'])

    @property
    def type_color(self):
        return self._COLORS.get(self.event_type, '#00261b')

    @property
    def type_icon(self):
        return self._ICONS.get(self.event_type, 'event')

    @property
    def status(self):
        now = timezone.now()
        end = self.end_date or self.event_date
        if end < now:
            return 'past'
        if self.event_date <= now:
            return 'today'
        return 'upcoming'

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['event_date']
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'
