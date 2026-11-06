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
    assert Organization.objects.filter(is_demo=True).count() == 3
    assert Project.objects.count() == 7
    assert Risk.objects.filter(level="critical").exists()
    assert Insight.objects.exists() and all(i.is_demo for i in Insight.objects.all())


def test_seed_scenarios_stop_at_the_planned_situations(monkeypatch):
    """Cenários da dinâmica (docs/demo/dinamica-cenarios.md): cada projeto para num bloqueio coerente com o fato."""
    from apps.analytics.models import LessonLearned
    from apps.governance import services as gov

    monkeypatch.setenv("DEMO_PASSWORD", "senha-demo-teste-123")
    call_command("seed_demo", "--confirm-demo", "--allow-non-debug")

    def stage(code):
        p = Project.objects.get(code=code)
        return p, p.current_stage

    p, st = stage("GOV-2026-01")
    assert st.order == 2 and p.organization.name.startswith("Secretaria")
    assert any("F2-R1" in b for b in gov.evaluate(st).blockers)
    p, st = stage("GOV-2026-02")
    assert st.order == 5 and any("crítico" in b.lower() or "critico" in b.lower() for b in gov.evaluate(st).blockers)
    p, st = stage("IA-2026-03")
    assert st.order == 6 and gov.responsible_ai_blockers(p)
    p, st = stage("IA-2026-04")
    assert st.order == 7 and LessonLearned.objects.filter(project=p, status="approved").exists()
