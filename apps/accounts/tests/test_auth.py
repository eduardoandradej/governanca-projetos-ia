"""Autenticação, força bruta, recuperação de senha e healthz (F08)."""

import pytest
from django.core import mail
from django.urls import reverse

from apps.auditlog.models import AuditEvent
from tests_support.factories import TEST_PASSWORD, make_user

pytestmark = pytest.mark.django_db


def _login(client, username, password):
    return client.post(reverse("accounts:login"), {"username": username, "password": password})


def test_login_success_is_audited(client):
    user = make_user("ana")
    resp = _login(client, "ana", TEST_PASSWORD)
    assert resp.status_code == 302
    ev = AuditEvent.objects.get(action="auth.login")
    assert ev.actor == user and ev.result == "success" and ev.correlation_id


def test_login_failure_is_audited_without_password(client):
    make_user("bia")
    resp = _login(client, "bia", "senha-errada-xyz")
    assert resp.status_code == 200
    ev = AuditEvent.objects.get(action="auth.login_failed")
    assert ev.actor_repr == "bia"
    dumped = str(ev.before) + str(ev.after) + ev.reason
    assert "senha-errada-xyz" not in dumped


def test_brute_force_lock_blocks_even_correct_password(client, settings):
    settings.LOGIN_THROTTLE_MAX_FAILURES = 3
    make_user("caio")
    for _ in range(3):
        _login(client, "caio", "errada-123456")
    resp = _login(client, "caio", TEST_PASSWORD)
    assert resp.status_code == 200
    assert "Muitas tentativas" in resp.content.decode()
    assert AuditEvent.objects.filter(action="auth.login_blocked", result="denied").exists()
    assert "_auth_user_id" not in client.session


def test_password_reset_sends_token_and_does_not_enumerate(client):
    make_user("davi", email="davi@exemplo.invalid")
    r1 = client.post(reverse("accounts:password_reset"), {"email": "davi@exemplo.invalid"})
    r2 = client.post(reverse("accounts:password_reset"), {"email": "naoexiste@exemplo.invalid"})
    assert r1.status_code == r2.status_code == 302
    assert r1.url == r2.url  # mesma resposta: não revela existência da conta
    assert len(mail.outbox) == 1
    assert "/contas/senha/redefinir/" in mail.outbox[0].body
    assert "NexFase" in mail.outbox[0].subject


def test_password_policy_rejects_short_password(client):
    user = make_user("eva")
    client.force_login(user)
    resp = client.post(
        reverse("accounts:password_change"),
        {"old_password": TEST_PASSWORD, "new_password1": "curta1", "new_password2": "curta1"},
    )
    assert resp.status_code == 200  # formulário reapresentado com erro
    user.refresh_from_db()
    assert user.check_password(TEST_PASSWORD)


def test_brand_identity_is_configurable(client, settings):
    body = client.get(reverse("accounts:login")).content.decode()
    assert "NexFase" in body and "Governança e gestão de projetos de IA" in body
    assert "da prova de conceito à produção" in body
    assert "GovIA" not in body and "TrilhaIA" not in body
    settings.APP_SHORT_NAME = "OutroNome"
    assert "OutroNome" in client.get(reverse("accounts:login")).content.decode()


def test_protected_pages_require_login(client):
    resp = client.get(reverse("projects:list"))
    assert resp.status_code == 302 and reverse("accounts:login") in resp.url


def test_healthz_checks_database(client):
    resp = client.get(reverse("core:healthz"))
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}
    assert resp["X-Request-ID"]


def test_logout_requires_post_and_is_audited(client):
    user = make_user("fabi")
    client.force_login(user)
    assert client.get(reverse("accounts:logout")).status_code == 405
    client.post(reverse("accounts:logout"))
    assert AuditEvent.objects.filter(action="auth.logout", actor=user).exists()
