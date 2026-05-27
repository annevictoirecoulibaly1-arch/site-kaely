from django.db import models
from django.utils import timezone


class MultiStreamConfig(models.Model):
    """Configuration des clés RTMP pour le multistreaming simultané."""

    title = models.CharField(max_length=200, default='Mon Stream')
    status = models.CharField(
        max_length=20,
        choices=[('idle', 'Arrêté'), ('live', 'En Direct'), ('error', 'Erreur')],
        default='idle',
    )

    # Clés RTMP par plateforme
    youtube_rtmp  = models.CharField(max_length=600, blank=True, help_text='rtmp://a.rtmp.youtube.com/live2/VOTRE_CLÉ')
    tiktok_rtmp   = models.CharField(max_length=600, blank=True, help_text='rtmp://live.tiktok.com/live/VOTRE_CLÉ')
    instagram_rtmp = models.CharField(max_length=600, blank=True, help_text='rtmp://live-api-s.facebook.com:80/rtmp/VOTRE_CLÉ')
    custom_rtmp   = models.CharField(max_length=600, blank=True, help_text='Autre plateforme RTMP')

    # Qualité du stream
    VIDEO_QUALITY_CHOICES = [
        ('360p', '360p — 800 kbps (connexion lente)'),
        ('480p', '480p — 1500 kbps'),
        ('720p', '720p — 2500 kbps (recommandé)'),
        ('1080p', '1080p — 4500 kbps (fibre)'),
    ]
    video_quality = models.CharField(max_length=10, choices=VIDEO_QUALITY_CHOICES, default='720p')

    # Suivi
    ffmpeg_pid   = models.IntegerField(null=True, blank=True)
    started_at   = models.DateTimeField(null=True, blank=True)
    stopped_at   = models.DateTimeField(null=True, blank=True)
    viewers_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuration Multistream'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.get_status_display()}"

    def get_active_platforms(self):
        platforms = []
        if self.youtube_rtmp:
            platforms.append('YouTube')
        if self.tiktok_rtmp:
            platforms.append('TikTok')
        if self.instagram_rtmp:
            platforms.append('Instagram')
        if self.custom_rtmp:
            platforms.append('Autre')
        return platforms

    QUALITY_SETTINGS = {
        '360p':  {'vbr': '800k',  'res': '640x360',  'fps': 25},
        '480p':  {'vbr': '1500k', 'res': '854x480',  'fps': 30},
        '720p':  {'vbr': '2500k', 'res': '1280x720', 'fps': 30},
        '1080p': {'vbr': '4500k', 'res': '1920x1080','fps': 30},
    }

    def build_ffmpeg_cmd(self, ffmpeg_bin='ffmpeg'):
        outputs = []
        for url in [self.youtube_rtmp, self.tiktok_rtmp, self.instagram_rtmp, self.custom_rtmp]:
            if url and url.strip():
                outputs.append(f'[f=flv]{url.strip()}')

        if not outputs:
            raise ValueError('Aucune destination RTMP configurée.')

        q = self.QUALITY_SETTINGS.get(self.video_quality, self.QUALITY_SETTINGS['720p'])
        tee = '|'.join(outputs)

        return [
            ffmpeg_bin, '-y',
            '-f', 'webm', '-i', 'pipe:0',
            '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency',
            '-b:v', q['vbr'], '-maxrate', q['vbr'], '-bufsize', str(int(q['vbr'].replace('k', '')) * 2) + 'k',
            '-vf', f"scale={q['res']}",
            '-r', str(q['fps']), '-g', str(q['fps'] * 2),
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
            '-f', 'tee', tee,
        ]
