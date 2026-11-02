"""Riscos, custos e decisões (T-010, T-016, T-017, T-026 nível de serviço, RN-008/016/019)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from apps.governance import services as gov
from apps.risks import services as rs
from apps.risks.models import CostEntry, DecisionStatus, Risk, RiskLevel, RiskPolicy, classify
from tests_support.factories import complete_stage_requirements

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "p,i,expected",
    [(1, 1, "low"), (1, 5, "low"), (2, 3, "medium"), (3, 3, "medium"), (3, 4, "high"), (4, 4, "high"),
     (4, 5, "critical"), (5, 5, "critical"), (2, 2, "low"), (5, 1, "low"), (2, 5, "medium"), (3, 5, "high")],
)
def test_T017_default_policy_classification(p, i, expected):
    assert classify(p * i) == expected


def test_T017_policy_configurable_per_organization(org_a, project_a):
    RiskPolicy.objects.create(organization=org_a.org, critical_min=16, high_min=10, medium_min=5)
    risk = rs.create_risk(actor=org_a.manager, project=project_a, title="Falta de GPU", category="gpu",
                          probability=4, impact=4, owner=org_a.executor)
    assert risk.score == 16 and risk.level == RiskLevel.CRITICAL
    with pytest.raises(IntegrityError), transaction.atomic():
        RiskPolicy.objects.filter(organization=org_a.org).update(high_min=30)


def test_risk_scale_enforced_and_codes_sequential(org_a, project_a):
    with pytest.raises(ValidationError):
        rs.create_risk(actor=org_a.manager, project=project_a, title="x", category="data", probability=6, impact=1,
                       owner=org_a.executor)
    r1 = rs.create_risk(actor=org_a.manager, project=project_a, title="A", category="data", probability=1, impact=1,
                        owner=org_a.executor)
    r2 = rs.create_risk(actor=org_a.manager, project=project_a, title="B", category="ethics", probability=2,
                        impact=2, owner=org_a.executor, ai_category="ethical")
    assert (r1.code, r2.code) == ("R-001", "R-002") and r2.ai_category == "ethical"
    with pytest.raises(IntegrityError), transaction.atomic():
        Risk.objects.filter(pk=r1.pk).update(probability=0)


def test_risk_owner_must_be_in_scope(org_a, org_b, project_a):
    with pytest.raises(ValidationError, match="papel ativo"):
        rs.create_risk(actor=org_a.manager, project=project_a, title="x", category="data", probability=1, impact=1,
                       owner=org_b.executor)


def test_T010_gate_blocked_by_untreated_critical_risk(org_a, project_a):
    stage = project_a.stages.get(order=1)
    complete_stage_requirements(org_a, stage)
    risk = rs.create_risk(actor=org_a.manager, project=project_a, title="Vazamento de dados sensíveis",
                          category="privacy", ai_category="policy", probability=5, impact=5, owner=org_a.security)
    with pytest.raises(ValidationError, match="Risco crítico sem tratamento"):
        gov.request_gate(stage.pk, actor=org_a.manager)
    rs.add_treatment(risk.pk, actor=org_a.manager, strategy="mitigate",
                     description="Anonimização e controle de acesso", owner=org_a.security,
                     due_date=date.today() + timedelta(days=15))
    assert not rs.untreated_critical_risks(project_a).exists()
    assert gov.request_gate(stage.pk, actor=org_a.manager).status == "requested"


def test_T010_exception_can_cover_critical_risk_with_security_ack(org_a, project_a):
    stage = project_a.stages.get(order=1)
    complete_stage_requirements(org_a, stage)
    rs.create_risk(actor=org_a.manager, project=project_a, title="Capacidade de GPU insuficiente", category="gpu",
                   probability=5, impact=4, owner=org_a.executor)
    exc = gov.grant_exception(stage.pk, actor=org_a.sponsor, covers_critical_risks=True,
                              valid_until=timezone.localdate() + timedelta(days=10),
                              justification="Fase 1 é documental; tratamento definido na fase 3",
                              residual_risk="Atraso de cronograma aceito pelo patrocínio")
    assert exc.status == "pending_security"
    gov.acknowledge_exception(exc.pk, actor=org_a.security)
    gate = gov.request_gate(stage.pk, actor=org_a.manager)
    assert gate.status == "requested"


def test_residual_acceptance_requires_sponsor(org_a, project_a):
    risk = rs.create_risk(actor=org_a.manager, project=project_a, title="Dependência de fornecedor",
                          category="vendor", probability=5, impact=4, owner=org_a.executor)
    with pytest.raises(PermissionDenied):
        rs.accept_residual(risk.pk, actor=org_a.manager, residual_probability=2, residual_impact=3,
                           justification="Contrato com cláusula de saída")
    risk = rs.accept_residual(risk.pk, actor=org_a.sponsor, residual_probability=2, residual_impact=3,
                              justification="Contrato com cláusula de saída")
    assert risk.status == "accepted" and risk.residual_score == 6
    assert not rs.untreated_critical_risks(project_a).exists()


def test_T016_costs_use_decimal_and_totals_are_exact(org_a, project_a):
    today = date.today()
    for amount in ("0.10", "0.20", "1000.05"):
        rs.add_cost(actor=org_a.manager, project=project_a, category="gpu", kind="actual", amount=Decimal(amount),
                    entry_date=today, justification="Nota fiscal sintética")
    rs.add_cost(actor=org_a.manager, project=project_a, category="storage", kind="planned", amount="5000",
                entry_date=today, justification="Estimativa do plano")
    summary = rs.cost_summary(project_a)
    assert summary["rows"]["gpu"]["actual"] == Decimal("1000.35")  # 0.1+0.2 exato (sem erro de float)
    assert summary["actual_total"] == Decimal("1000.35") and summary["planned_total"] == Decimal("5000.00")
    assert summary["execution_percent"] == Decimal("1.0")  # 1000.35 / 100000.00
    assert summary["variance"] == Decimal("1000.35") - Decimal("100000.00")
    assert isinstance(CostEntry.objects.first().amount, Decimal)
    assert CostEntry.objects.first().currency == "BRL"


def test_costs_reject_float_negative_and_unauthorized(org_a, project_a):
    with pytest.raises(ValidationError, match="Decimal"):
        rs.add_cost(actor=org_a.manager, project=project_a, category="gpu", kind="actual", amount=0.1,
                    entry_date=date.today(), justification="x" * 6)
    with pytest.raises(ValidationError, match="positivo"):
        rs.add_cost(actor=org_a.manager, project=project_a, category="gpu", kind="actual", amount="-1",
                    entry_date=date.today(), justification="estorno")
    with pytest.raises(PermissionDenied):
        rs.add_cost(actor=org_a.executor, project=project_a, category="gpu", kind="actual", amount="1",
                    entry_date=date.today(), justification="sem papel")


def test_costs_page_hidden_from_reader(client, org_a, project_a):
    client.force_login(org_a.reader)
    assert client.get(reverse("risks:costs", args=[project_a.pk])).status_code == 403
    client.force_login(org_a.sponsor)
    assert client.get(reverse("risks:costs", args=[project_a.pk])).status_code == 200


def test_decision_lifecycle_versioning_and_segregation(org_a, project_a):
    d1 = rs.propose_decision(actor=org_a.manager, project=project_a, agenda="Escolha de orquestrador",
                             alternatives="A; B", decision="Adotar A", rationale="Menor custo",
                             topic="architecture")
    with pytest.raises(PermissionDenied):
        rs.decide(d1.pk, actor=org_a.executor, approve=True, note="sem papel")  # T-026 (serviço)
    with pytest.raises(ValidationError):
        rs.revise_decision(d1.pk, actor=org_a.manager, decision="x", rationale="y")  # ainda não aprovada
    rs.decide(d1.pk, actor=org_a.sponsor, approve=True, note="Aprovado")
    d2 = rs.revise_decision(d1.pk, actor=org_a.manager, decision="Adotar B", rationale="Suporte local")
    d1.refresh_from_db()
    assert d1.status == DecisionStatus.APPROVED and d2.version == 2 and d2.supersedes == d1
    rs.decide(d2.pk, actor=org_a.portfolio, approve=True, note="Revisão aceita")
    d1.refresh_from_db()
    assert d1.status == DecisionStatus.SUPERSEDED  # histórico preservado, sem sobrescrever
    assert d1.decision == "Adotar A"


def test_proposer_cannot_approve_own_decision(org_a, project_a):
    d = rs.propose_decision(actor=org_a.sponsor, project=project_a, agenda="Pauta", alternatives="A;B",
                            decision="A", rationale="R")
    with pytest.raises(PermissionDenied, match="segregação"):
        rs.decide(d.pk, actor=org_a.sponsor, approve=True, note="auto")


def test_risk_pages_render_and_isolated(client, org_a, org_b, project_a):
    risk = rs.create_risk(actor=org_a.manager, project=project_a, title="Viés no modelo", category="ethics",
                          ai_category="ethical", probability=3, impact=4, owner=org_a.executor)
    client.force_login(org_a.reader)
    body = client.get(reverse("risks:project", args=[project_a.pk])).content.decode()
    assert "Viés no modelo" in body and "Matriz de riscos 5 por 5" in body
    assert client.get(reverse("risks:list")).status_code == 200
    client.force_login(org_b.admin)
    assert client.get(reverse("risks:detail", args=[risk.pk])).status_code == 404
    assert "Viés no modelo" not in client.get(reverse("risks:list")).content.decode()


def test_create_risk_via_web(client, org_a, project_a):
    client.force_login(org_a.executor)
    resp = client.post(reverse("risks:project", args=[project_a.pk]), {
        "title": "Ataque adversarial", "category": "security", "ai_category": "technology",
        "probability": 3, "impact": 5, "owner": org_a.security.pk,
    })
    assert resp.status_code == 302
    assert Risk.objects.get(title="Ataque adversarial").level == "high"
