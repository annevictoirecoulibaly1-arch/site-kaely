from django.db import OperationalError, ProgrammingError
from .models import Subscription


def profile_info(request):
    if not request.user.is_authenticated:
        return {}
    initials = ''
    if request.user.first_name:
        initials += request.user.first_name[:1].upper()
    if request.user.last_name:
        initials += request.user.last_name[:1].upper()
    if not initials and request.user.username:
        initials = request.user.username[:1].upper()
    profile_photo_url = ''
    try:
        if getattr(request.user, 'email', None):
            sub = Subscription.objects.filter(email=request.user.email).first()
            if sub and sub.photo_url:
                profile_photo_url = sub.photo_url
    except (OperationalError, ProgrammingError):
        pass
    return {'profile_photo_url': profile_photo_url, 'profile_initials': initials}
