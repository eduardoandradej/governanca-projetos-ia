"""Camadas D→I→K (T-018, T-019, T-028, RN-012/013/018/022) e incremento PMBOK 8 (uso responsável de IA)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.analytics import metrics, services
from apps.analytics.models import Insight, InsightStatus, LessonLearned
from apps.auditlog.models import AuditEvent
from apps.governance import services as gov
from apps.governance.models import FrameworkReference, ResponsibleAIFactor
from apps.lifecycle import services as lc
from apps.lifecycle.models import StageInstance
from apps.projects.models import Project
from apps.risks import services as rs
from tests_support.factories import complete_responsible_ai, pass_gate

pytestmark = pytest.mark.django_db


def _scope(user, org=None):
    return services.scoped_projects(user, organization_id=org.pk if org else None)


def test_T028_metrics_report_no_data_instead_of_100(org_a):
    results = metrics.compute_all(_scope(org_a.manager))
    assert results["K01"].value == 0
    for code in ("K02", "K06", "K07", "K08", "K09", "K12"):
        assert results[code].value is None, code  # sem denominador → "Sem dados"


def test_T018_dashboard_reflects_db_changes_and_filters(client, org_a, org_b, project_a):
    org_b.create_project(code="IA-B1")
    r = metrics.compute_all(_scope(org_a.manager))
    assert r["K01"].value == 1 and r["K02"].denominator == 6 and r["K02"].value == Decimal("0.0")
    req = project_a.stages.get(order=1).requirements.get(code="F1-R2")
    lc.fulfill_requirement(req.pk, actor=org_a.manager, note="Patrocínio formalizado em ata.")
    lc.validate_requirement(req.pk, actor=org_a.security, decision="approved", comment="ok")
    rs.create_risk(actor=org_a.manager, project=project_a, title="GPU", category="gpu", probability=4, impact=4,
                   owner=org_a.executor)
    r = metrics.compute_all(_scope(org_a.manager))
    assert r["K02"].numerator == 1 and r["K02"].value == Decimal("16.7")  # 1/6
    assert r["K04"].value == 1
    client.force_login(org_a.manager)
    body = client.get(reverse("core:dashboard")).content.decode()
    assert "IA-ALFA-01" in body and "IA-B1" not in body  # isolamento entre organizações
    page = client.get(reverse("analytics:metric", args=["K02"])).content.decode()
    assert "Numerador 1 / denominador 6" in page and "Ficha técnica" in page


def test_cost_and_overdue_metrics_exact(org_a, project_a):
    rs.add_cost(actor=org_a.manager, project=project_a, category="gpu", kind="actual", amount="25000.00",
                entry_date=date.today(), justification="NF sintética")
    lc.create_task(actor=org_a.manager, project=project_a, stage=project_a.stages.get(order=1), title="Atrasada",
                   due_date=date.today() - timedelta(days=2))
    r = metrics.compute_all(_scope(org_a.manager))
    assert r["K08"].value == Decimal("25.0") and r["K08"].numerator == Decimal("25000.00")
    assert r["K05"].value == 1


def _seed_signals(org, project):
    """Dados SINTÉTICOS que disparam regras: riscos altos sem tratamento, tarefas vencidas, orçamento."""
    for i in range(2):
        rs.create_risk(actor=org.manager, project=project, title=f"Risco alto {i}", category="data", probability=4,
                       impact=3, owner=org.executor)
    for i in range(3):
        lc.create_task(actor=org.manager, project=project, stage=project.stages.get(order=1), title=f"T{i}",
                       due_date=date.today() - timedelta(days=5))
    rs.add_cost(actor=org.manager, project=project, category="gpu", kind="actual", amount="95000.00",
                entry_date=date.today(), justification="NF sintética")


def test_T019_data_to_information_to_knowledge_cycle(org_a, project_a):
    # D: registros sintéticos + catálogo e linhagem
    _seed_signals(org_a, project_a)
    raw = services.create_asset(actor=org_a.manager, project=project_a, name="Base de chamados (sintética)",
                                kind="dataset", purpose="Treino do assistente", owner=org_a.executor,
                                contains_personal_data=True, classification="confidential")
    model = services.create_asset(actor=org_a.manager, project=project_a, name="Modelo de triagem", kind="model",
                                  purpose="Classificar chamados", owner=org_a.executor)
    services.add_lineage(actor=org_a.manager, source=raw, target=model, transformation="Anonimização e fine-tuning")
    with pytest.raises(ValidationError, match="ciclo"):
        services.add_lineage(actor=org_a.manager, source=model, target=raw, transformation="inválido")
    # I: KPI calculado do banco
    r = metrics.compute_all(_scope(org_a.manager, org_a.org))
    assert r["K04"].value == 2 and r["K05"].value == 3 and r["K08"].value == Decimal("95.0")
    assert services.capture_snapshots(actor=org_a.manager, organization=org_a.org) == 12
    # K: insights determinísticos rastreáveis
    created = services.generate_insights(actor=org_a.manager, organization=org_a.org)
    rules_fired = {i.rule_code for i in created}
    assert {"I02", "I04", "I05"} <= rules_fired
    ins = next(i for i in created if i.rule_code == "I02")
    assert ins.parameters == {"min_count": 2} and len(ins.supporting_data["risks"]) == 2
    assert "2 riscos" in ins.message and ins.status == InsightStatus.PROPOSED
    assert services.generate_insights(actor=org_a.manager, organization=org_a.org) == []  # sem duplicar
    # revisão humana e segregação revisor ≠ aprovador
    services.review_insight(ins.pk, actor=org_a.manager, note="Confirmado: riscos sem plano de resposta.")
    with pytest.raises(PermissionDenied):
        services.approve_insight(ins.pk, actor=org_a.manager, note="autoaprovação indevida")
    services.approve_insight(ins.pk, actor=org_a.sponsor, note="Recomendação: tratar riscos em 15 dias",
                             action_title="Definir tratamentos dos riscos altos", action_owner=org_a.manager,
                             action_due=date.today() + timedelta(days=15))
    ins.refresh_from_db()
    assert ins.status == InsightStatus.APPROVED and ins.action.title.startswith("Definir")
    lesson = services.create_lesson(actor=org_a.manager, project=project_a, source_insight=ins,
                                    title="Tratar riscos altos antes do gate", context=ins.message,
                                    lesson="Riscos sem resposta acumulam na fase 1.",
                                    recommendation="Exigir plano de resposta ao registrar risco alto.")
    services.approve_lesson(lesson.pk, actor=org_a.portfolio, visibility="organization")
    lesson.refresh_from_db()
    assert lesson.status == "approved" and lesson.source_insight == ins
    actions = set(AuditEvent.objects.filter(project_id=project_a.pk).values_list("action", flat=True))
    assert {"data.asset_create", "data.lineage", "insight.review", "lesson.approve"} <= actions


def test_RN018_classified_lesson_needs_disclosure_and_never_crosses_orgs(org_a, org_b):
    project = org_a.create_project(code="IA-SEC", data_classification="restricted")
    lesson = services.create_lesson(actor=org_a.manager, project=project, title="Lição restrita",
                                    context="Contexto sintético", lesson="Lição", recommendation="Recomendação")
    with pytest.raises(ValidationError, match="justificativa de divulgação"):
        services.approve_lesson(lesson.pk, actor=org_a.portfolio, visibility="organization")
    services.approve_lesson(lesson.pk, actor=org_a.portfolio, visibility="organization",
                            disclosure_justification="Anonimizada e autorizada pelo patrocinador para reuso.")
    # Usuário com papel apenas em OUTRO projeto da mesma organização vê a lição divulgada
    other = org_a.create_project(code="IA-OUT")
    from apps.organizations.models import Role
    from apps.organizations.services import bootstrap_role

    scoped = org_a.add_user("consultor")
    bootstrap_role(organization=org_a.org, user=scoped, role=Role.READER, project=other)
    assert services.visible_lessons(scoped).filter(pk=lesson.pk).exists()
    assert not services.visible_lessons(org_b.admin).filter(pk=lesson.pk).exists()


def test_RN022_demo_flag_propagates(org_a, project_a):
    org_a.org.is_demo = True
    org_a.org.save()
    _seed_signals(org_a, project_a)
    created = services.generate_insights(actor=org_a.manager, organization=org_a.org)
    assert created and all(i.is_demo for i in created)


def test_insights_and_lessons_pages(client, org_a, org_b, project_a):
    _seed_signals(org_a, project_a)
    client.force_login(org_a.manager)
    client.post(reverse("analytics:run_insights"), {"organizacao": org_a.org.pk})
    ins = Insight.objects.filter(project=project_a).first()
    assert ins is not None
    assert "Dados de sustentação" in client.get(reverse("analytics:insight", args=[ins.pk])).content.decode()
    assert client.get(reverse("analytics:home")).status_code == 200
    assert client.get(reverse("analytics:lessons")).status_code == 200
    client.force_login(org_b.admin)
    assert client.get(reverse("analytics:insight", args=[ins.pk])).status_code == 404
    assert client.post(reverse("analytics:run_insights"), {"organizacao": org_a.org.pk}).status_code == 404


def test_catalog_requires_permission_and_same_org(org_a, org_b, project_a):
    with pytest.raises(PermissionDenied):
        services.create_asset(actor=org_a.reader, project=project_a, name="x", kind="dataset", purpose="x",
                              owner=org_a.executor)
    pb = org_b.create_project(code="IA-B2")
    a = services.create_asset(actor=org_a.manager, project=project_a, name="A", kind="dataset", purpose="p",
                              owner=org_a.executor)
    b = services.create_asset(actor=org_b.manager, project=pb, name="B", kind="dataset", purpose="p",
                              owner=org_b.executor)
    with pytest.raises(ValidationError, match="mesma organização"):
        services.add_lineage(actor=org_a.manager, source=b, target=a, transformation="x")


# ------------------------------------------------------------------- Incremento PMBOK 8 (Apêndice X3 / 4.2)


def test_pmbok_project_fields_and_catalog(org_a):
    project = org_a.create_project(code="IA-PMB", development_approach="hybrid", ai_adoption_strategy="assistance")
    assert project.get_ai_adoption_strategy_display().startswith("Assistência")
    assert FrameworkReference.objects.filter(code="PMB-X3-ETHICS", pages__contains="238").exists()
    assert project.stages.get(order=1).requirements.filter(code="F1-R6").exists()


def test_gate_6_requires_responsible_ai_assessment(org_a, project_a):
    for order in range(1, 6):
        pass_gate(org_a, project_a.stages.get(order=order))
    stage6 = project_a.stages.get(order=6)
    assert stage6.requires_responsible_ai
    from tests_support.factories import complete_stage_requirements

    complete_stage_requirements(org_a, stage6)
    with pytest.raises(ValidationError, match="Uso responsável de IA"):
        gov.request_gate(stage6.pk, actor=org_a.manager)
    with pytest.raises(ValidationError, match="humano responsável"):
        gov.assess_responsible_ai(project_a, actor=org_a.security, factor="bias", status="addressed",
                                  measures="Testes periódicos de viés com bases diversificadas.")
    with pytest.raises(PermissionDenied):
        gov.assess_responsible_ai(project_a, actor=org_a.reader, factor="bias", status="addressed",
                                  measures="Testes periódicos de viés com bases diversificadas.",
                                  accountable=org_a.sponsor)
    complete_responsible_ai(org_a, project_a)
    gate = gov.request_gate(stage6.pk, actor=org_a.manager)
    gov.approve_gate(stage6.pk, actor=org_a.approver, justification="Aceite operacional", request_number=gate.request_number)
    # alteração posterior exige revalidação (RN-010)
    gov.assess_responsible_ai(project_a, actor=org_a.security, factor="privacy", status="pending", measures="")
    stage6.gate.refresh_from_db()
    assert stage6.gate.revalidation_required
    assert len(ResponsibleAIFactor.values) == 8


def test_responsible_ai_page(client, org_a, project_a):
    client.force_login(org_a.security)
    resp = client.post(reverse("governance:responsible_ai", args=[project_a.pk]), {
        "factor": "transparency", "status": "addressed", "accountable": org_a.sponsor.pk,
        "measures": "Usuários informados sobre o uso de IA e os limites das respostas.",
    })
    assert resp.status_code == 302
    body = client.get(reverse("governance:responsible_ai", args=[project_a.pk])).content.decode()
    assert "Usuários informados" in body and "7 fator(es) pendente(s)" in body


def test_existing_projects_keep_their_template_version(org_a):
    """Projeto criado no v3; outro forçado no v1 (legado) não ganha a exigência nova (T-027)."""
    from apps.lifecycle.models import LifecycleTemplateVersion

    v1 = LifecycleTemplateVersion.objects.get(number=1)
    legacy = Project(organization=org_a.org, code="IA-LEG", name="Legado", description="d", business_case="b",
                     platform_type="genai", deployment_approach="on_prem", sponsor=org_a.sponsor,
                     manager=org_a.manager, lifecycle_version=v1)
    legacy.save()
    lc.instantiate_lifecycle(legacy, actor=org_a.manager)
    assert not StageInstance.objects.filter(project=legacy, requires_responsible_ai=True).exists()
    assert LessonLearned.objects.count() == 0
    assert timezone.now()
