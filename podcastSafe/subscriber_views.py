from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from .models import Subscription
from .auth import subscriber_required

User = get_user_model()


@subscriber_required
def dashboard_admin_for_subscribers(request):
    """Dashboard accessible aux inscrits via leur email Subscription."""
    sub = Subscription.objects.filter(email=request.user.email, is_active=True).first()
    # Prototype : redirige vers le même template dashboard_admin.html
    # On pourrait plus tard afficher liste de subscribers, gérer etc.
    return render(request, 'dashboard_admin.html', {'subscription': sub})

