from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from apps.auditlog import services as audit
from apps.auditlog.models import AuditResult


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    audit.record("auth.login", actor=user, entity=user)


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if user is not None:
        audit.record("auth.logout", actor=user, entity=user)


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    # `credentials` já vem com a senha mascarada pelo Django; registramos apenas o usuário informado.
    audit.record(
        "auth.login_failed",
        result=AuditResult.FAILURE,
        actor_repr=str(credentials.get("username", ""))[:150],
    )
