from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.auditlog import services as audit
from apps.auditlog.models import AuditResult
from apps.core import context

from . import throttle


class ThrottledAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuário ou senha inválidos.",
        "locked": "Muitas tentativas malsucedidas. Aguarde alguns minutos e tente novamente.",
    }

    def clean(self):
        username = self.cleaned_data.get("username", "")
        ip = context.get_client_ip()
        if throttle.is_locked(username, ip):
            audit.record(
                "auth.login_blocked",
                result=AuditResult.DENIED,
                actor_repr=username,
                reason="Bloqueio temporário por excesso de tentativas",
            )
            raise forms.ValidationError(self.error_messages["locked"], code="locked")
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            throttle.register(username, ip, successful=False)
            raise
        throttle.register(username, ip, successful=True)
        return cleaned
