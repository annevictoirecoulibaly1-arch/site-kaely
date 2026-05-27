import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Safeplace.settings')

app = Celery('Safeplace')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configuration Celery
app.conf.update(
    # Broker settings
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Beat schedule (tâches planifiées)
    beat_schedule={
        'check-live-streams': {
            'task': 'podcastSafe.tasks.update_live_stream_status',
            'schedule': crontab(minute='*/5'),  # Tous les 5 minutes
        },
        'send-email-notifications': {
            'task': 'podcastSafe.tasks.send_new_episode_notifications',
            'schedule': crontab(hour=12, minute=0),  # Chaque jour à midi
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
