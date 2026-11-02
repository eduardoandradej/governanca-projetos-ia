"""Limitação de tentativas de login por usuário e por IP (janela deslizante)."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import LoginAttempt


def _window_start():
    return timezone.now() - timedelta(minutes=settings.LOGIN_THROTTLE_WINDOW_MINUTES)


def _recent_failures(**filters) -> int:
    qs = LoginAttempt.objects.filter(created_at__gte=_window_start(), **filters)
    last_success = qs.filter(successful=True).order_by("-created_at").first()
    failures = qs.filter(successful=False)
    if last_success:
        failures = failures.filter(created_at__gt=last_success.created_at)
    return failures.count()


def is_locked(username: str, ip_address: str | None) -> bool:
    limit = settings.LOGIN_THROTTLE_MAX_FAILURES
    username = (username or "").strip().lower()
    if username and _recent_failures(username=username) >= limit:
        return True
    # Limite por IP é mais tolerante (vários usuários atrás do mesmo NAT).
    if ip_address and _recent_failures(ip_address=ip_address) >= limit * 4:
        return True
    return False


def register(username: str, ip_address: str | None, successful: bool) -> None:
    LoginAttempt.objects.create(
        username=(username or "").strip().lower()[:150], ip_address=ip_address, successful=successful
    )
