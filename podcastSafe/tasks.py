from celery import shared_task
from django.core.mail import send_mass_mail
from django.utils import timezone
from datetime import timedelta
from .models import Episode, LiveStream

@shared_task
def update_live_stream_status():
    """
    Mettre à jour le statut des live streams
    """
    now = timezone.now()

    scheduled_streams = LiveStream.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    )
    updated_count = scheduled_streams.update(status='live')
    return f"Updated {updated_count} streams"


@shared_task
def send_new_episode_notifications():
    """
    Envoyer une notification pour les nouveaux épisodes
    """
    today = timezone.now().date()
    today_episodes = Episode.objects.filter(
        is_published=True,
        created_at__date=today
    )

    if not today_episodes.exists():
        return "No new episodes today"

    # TODO: implémenter l'envoi d'emails aux abonnés si nécessaire.
    return f"Notifications planned for {today_episodes.count()} episodes"


@shared_task
def send_daily_report():
    """
    Envoyer un rapport quotidien au propriétaire
    """
    from django.conf import settings

    today = timezone.now().date()
    new_episodes = Episode.objects.filter(created_at__date=today).count()

    message = f"""
    Rapport journalier - {today}

    Nouveaux épisodes: {new_episodes}
    """

    if settings.ADMINS:
        send_mass_mail(((
            'Rapport journalier SafePlace',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMINS[0][1]],
        ),))

    return message
