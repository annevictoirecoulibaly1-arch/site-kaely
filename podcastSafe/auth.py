from django.shortcuts import redirect
from functools import wraps


def owner_required(view_func):
    """Accès uniquement au superuser du site."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        if not request.user.is_superuser:
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def subscriber_required(view_func):
    """Accès aux personnes avec une Subscription active (email vérifié)."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')

        email = (getattr(request.user, 'email', None) or '').strip()
        if not email:
            return redirect('access_denied')

        from .models import Subscription
        sub = Subscription.objects.filter(email__iexact=email, is_active=True).first()
        if not sub:
            return redirect('access_denied')

        request.subscription = sub
        return view_func(request, *args, **kwargs)
    return wrapped_view


def owner_and_staff_required(view_func):
    """Accès staff ou propriétaire."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapped_view
