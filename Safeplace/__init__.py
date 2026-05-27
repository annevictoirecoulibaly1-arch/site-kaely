import os

# Celery optional - only load in production or when explicitly needed
if os.environ.get('CELERY_ENABLED', 'False').lower() == 'true':
    from .celery import app as celery_app
    __all__ = ('celery_app',)
else:
    # Celery disabled for development without Redis
    try:
        from .celery import app as celery_app
        __all__ = ('celery_app',)
    except ImportError:
        __all__ = ()
