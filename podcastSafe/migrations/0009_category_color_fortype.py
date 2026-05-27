from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcastSafe', '0008_multistreamconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='color',
            field=models.CharField(default='#00261b', help_text='Couleur principale hex', max_length=30),
        ),
        migrations.AddField(
            model_name='category',
            name='for_type',
            field=models.CharField(
                choices=[('podcast', 'Podcast'), ('video', 'Vidéo'), ('all', 'Tous')],
                default='all',
                max_length=10,
            ),
        ),
    ]
