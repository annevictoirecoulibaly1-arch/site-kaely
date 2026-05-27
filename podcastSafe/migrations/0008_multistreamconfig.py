from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcastSafe', '0007_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='MultiStreamConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Mon Stream', max_length=200)),
                ('status', models.CharField(
                    choices=[('idle', 'Arrêté'), ('live', 'En Direct'), ('error', 'Erreur')],
                    default='idle', max_length=20,
                )),
                ('youtube_rtmp',   models.CharField(blank=True, max_length=600)),
                ('tiktok_rtmp',    models.CharField(blank=True, max_length=600)),
                ('instagram_rtmp', models.CharField(blank=True, max_length=600)),
                ('custom_rtmp',    models.CharField(blank=True, max_length=600)),
                ('video_quality',  models.CharField(
                    choices=[('360p','360p'),('480p','480p'),('720p','720p'),('1080p','1080p')],
                    default='720p', max_length=10,
                )),
                ('ffmpeg_pid',    models.IntegerField(blank=True, null=True)),
                ('started_at',    models.DateTimeField(blank=True, null=True)),
                ('stopped_at',    models.DateTimeField(blank=True, null=True)),
                ('viewers_count', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
                ('updated_at',    models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Configuration Multistream', 'ordering': ['-created_at']},
        ),
    ]
