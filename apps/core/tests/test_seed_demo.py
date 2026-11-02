"""seed_demo: opt-in explícito, idempotente, marca dados como demonstrativos (RN-022)."""

import pytest
from django.core.management import CommandError, call_command

from apps.analytics.models import Insight
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.risks.models import Risk

pytestmark = pytest.mark.django_db


def test_seed_requires_confirmation():
    with pytest.raises(CommandError, match="--confirm-demo"):
        call_command("seed_demo")


def test_seed_refuses_without_debug_flag():
    with pytest.raises(CommandError, match="DEBUG=False"):
        call_command("seed_demo", "--confirm-demo")


def test_seed_creates_demo_data_idempotently(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "senha-demo-teste-123")
    call_command("seed_demo", "--confirm-demo", "--allow-non-debug")
    call_command("seed_demo", "--confirm-demo", "--allow-non-debug")
    assert Organization.objects.filter(is_demo=True).count() == 2
    assert Project.objects.count() == 3
    assert Risk.objects.filter(level="critical").exists()
    assert Insight.objects.exists() and all(i.is_demo for i in Insight.objects.all())
