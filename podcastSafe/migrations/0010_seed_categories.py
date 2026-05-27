from django.db import migrations


PODCAST_CATEGORIES = [
    {'name': 'Rencontre Homme de Dieu',       'icon': 'person',            'color': '#1E3A5F'},
    {'name': 'Rencontre Chantre',              'icon': 'mic',               'color': '#5B21B6'},
    {'name': 'Rencontre Influenceur Chrétien', 'icon': 'social_leaderboard','color': '#9D174D'},
    {'name': 'Rencontre Artiste Gospel',       'icon': 'piano',             'color': '#92400E'},
]

VIDEO_CATEGORIES = [
    {'name': 'Worship',         'icon': 'music_note',          'color': '#4C1D95'},
    {'name': 'Témoignage',      'icon': 'record_voice_over',   'color': '#7C2D12'},
    {'name': 'Exhortation',     'icon': 'campaign',            'color': '#064E3B'},
    {'name': 'Enseignement',    'icon': 'auto_stories',        'color': '#1E3A8A'},
    {'name': 'Évangélisation',  'icon': 'volunteer_activism',  'color': '#78350F'},
    {'name': 'Prière',          'icon': 'self_improvement',    'color': '#14532D'},
]


def seed(apps, schema_editor):
    Category = apps.get_model('podcastSafe', 'Category')
    for c in PODCAST_CATEGORIES:
        Category.objects.get_or_create(
            name=c['name'],
            defaults={'icon': c['icon'], 'color': c['color'], 'for_type': 'podcast'},
        )
    for c in VIDEO_CATEGORIES:
        Category.objects.get_or_create(
            name=c['name'],
            defaults={'icon': c['icon'], 'color': c['color'], 'for_type': 'video'},
        )


def unseed(apps, schema_editor):
    Category = apps.get_model('podcastSafe', 'Category')
    names = [c['name'] for c in PODCAST_CATEGORIES + VIDEO_CATEGORIES]
    Category.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('podcastSafe', '0009_category_color_fortype'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
