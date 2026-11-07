"""Projetos e instanciação do ciclo de vida (RN-001, RN-003, RN-011, RN-021; T-001, T-002, T-003, T-022, T-027)."""

from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.urls import reverse

from apps.auditlog.models import AuditEvent
from apps.lifecycle import default_template
from apps.lifecycle.models import LifecycleTemplateVersion, StageStatus
from apps.projects import services
from apps.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_T001_project_persists_after_connection_reset(org_a):
    project = org_a.create_project(code="IA-PERSIST")
    connection.close()  # simula reinício da aplicação: nova conexão ao PostgreSQL
    reloaded = Project.objects.get(pk=project.pk)
    assert reloaded.code == "IA-PERSIST" and reloaded.organization == org_a.org
    assert reloaded.planned_cost == Decimal("100000.00")


def test_T003_project_receives_seven_stages_starting_at_phase_1(project_a):
    stages = list(project_a.stages.order_by("order"))
    assert [s.order for s in stages] == [1, 2, 3, 4, 5, 6, 7]
    assert stages[0].status == StageStatus.IN_PROGRESS
    assert all(s.status == StageStatus.NOT_STARTED for s in stages[1:])
    assert stages[0].requirements.count() == 6  # template v4 (F1-R5 ISACA 2025; F1-R6 PMBOK 8)
    assert stages[6].has_exit_gate is False
    assert project_a.current_stage == stages[0]
    assert project_a.lifecycle_version.number == 4


def test_code_unique_per_organization_only(org_a, org_b):
    org_a.create_project(code="IA-DUP")
    with pytest.raises(ValidationError):
        org_a.create_project(code="IA-DUP")
    assert org_b.create_project(code="IA-DUP").code == "IA-DUP"


def test_required_fields_and_people_from_same_org(org_a, org_b):
    with pytest.raises(ValidationError, match="vínculo ativo"):
        org_a.create_project(code="IA-X", sponsor=org_b.sponsor)
    with pytest.raises(ValidationError):
        org_a.create_project(code="IA-Y", business_case="")


def test_reader_cannot_create_project(org_a):
    with pytest.raises(PermissionDenied):
        services.create_project(
            actor=org_a.reader, organization=org_a.org, code="IA-R", name="x", description="x", business_case="x",
            platform_type="genai", deployment_approach="hybrid", sponsor=org_a.sponsor, manager=org_a.manager,
        )


def test_T002_other_org_user_gets_404_even_with_known_id(client, org_b, project_a):
    client.force_login(org_b.admin)
    for url in (
        reverse("projects:detail", args=[project_a.pk]),
        reverse("projects:edit", args=[project_a.pk]),
        reverse("lifecycle:tasks", args=[project_a.pk]),
        reverse("lifecycle:stage", args=[project_a.pk, project_a.stages.first().pk]),
    ):
        assert client.get(url).status_code == 404, url
    assert AuditEvent.objects.filter(action="authz.denied", actor=org_b.admin, project_id=project_a.pk).exists()
    assert "IA-ALFA-01" not in client.get(reverse("projects:list")).content.decode()


def test_project_views_render_for_member(client, org_a, project_a):
    client.force_login(org_a.reader)
    resp = client.get(reverse("projects:detail", args=[project_a.pk]))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Oportunidade e justificativa" in body and "Operação e melhoria contínua" in body
    assert "Restrito ao seu perfil" in body  # leitor não vê custos (campo sensível)
    assert client.get(reverse("projects:list")).status_code == 200
    assert client.get(reverse("lifecycle:tasks", args=[project_a.pk])).status_code == 200


def test_create_project_via_web_form(client, org_a):
    client.force_login(org_a.manager)
    resp = client.post(
        reverse("projects:create", args=[org_a.org.pk]),
        {
            "code": "ia-web-01", "name": "Plataforma LLM interna", "description": "Implantação sintética.",
            "business_case": "Reduzir tempo de PoC a produção.", "platform_type": "genai",
            "deployment_approach": "hybrid", "sponsor": org_a.sponsor.pk, "manager": org_a.manager.pk,
            "priority": "high", "criticality": "medium", "data_classification": "internal",
            "planned_cost": "250000.50", "currency": "BRL", "technology_metadata": "Orquestração: Kubernetes",
        },
    )
    project = Project.objects.get(organization=org_a.org, code="IA-WEB-01")
    assert resp.status_code == 302
    assert project.technology_metadata == {"Orquestração": "Kubernetes"}
    assert project.stages.count() == 7


def test_T022_audit_records_project_creation_without_secrets(org_a, project_a):
    ev = AuditEvent.objects.get(action="project.create", project_id=project_a.pk)
    assert ev.actor == org_a.manager and ev.organization_id == org_a.org.pk and ev.occurred_at
    assert ev.after["code"] == "IA-ALFA-01"
    assert "password" not in str(ev.after).lower()


def test_update_tracks_diff_and_optimistic_version(org_a, project_a):
    updated = services.update_project(project_a.pk, actor=org_a.manager, expected_version=1, name="Novo nome")
    assert updated.version == 2
    ev = AuditEvent.objects.get(action="project.update", project_id=project_a.pk)
    assert ev.before == {"name": "Projeto sintético IA-ALFA-01"} and ev.after == {"name": "Novo nome"}
    with pytest.raises(ValidationError, match="alterado por outra pessoa"):
        services.update_project(project_a.pk, actor=org_a.manager, expected_version=1, name="Conflito")


def test_RN011_closed_project_is_read_only_and_reopen_requires_authority(org_a, project_a):
    with pytest.raises(PermissionDenied):
        services.change_status(project_a.pk, actor=org_a.manager, to_status="closed", reason="Encerramento formal")
    services.change_status(project_a.pk, actor=org_a.sponsor, to_status="closed", reason="Encerramento formal")
    with pytest.raises(ValidationError):
        services.update_project(project_a.pk, actor=org_a.manager, name="x")
    with pytest.raises(PermissionDenied):
        services.change_status(project_a.pk, actor=org_a.portfolio, to_status="active", reason="Reabrir sem papel")
    with pytest.raises(ValidationError, match="justificativa"):
        services.change_status(project_a.pk, actor=org_a.sponsor, to_status="active", reason="curta")
    with pytest.raises(ValidationError, match="decisão formal aprovada"):
        services.change_status(project_a.pk, actor=org_a.sponsor, to_status="active", reason="Decisão do comitê nº 12")
    from apps.risks import services as rs

    d = rs.propose_decision(actor=org_a.manager, project=project_a, topic="reopen", agenda="Reabrir projeto",
                            alternatives="Manter encerrado; reabrir", decision="Reabrir", rationale="Nova demanda")
    rs.decide(d.pk, actor=org_a.sponsor, approve=True, note="Aprovado em comitê")
    services.change_status(project_a.pk, actor=org_a.sponsor, to_status="active", reason="Decisão do comitê nº 12",
                           decision_id=d.pk)
    statuses = list(project_a.status_history.order_by("created_at").values_list("to_status", flat=True))
    assert statuses == ["active", "closed", "active"]


def test_T027_new_template_version_does_not_change_started_projects(org_a, project_a):
    from django.apps import apps as django_apps

    original = list(project_a.stages.values_list("name", flat=True))
    v2 = default_template.install(django_apps, number=5)
    stage1 = v2.stages.get(order=1)
    stage1.name = "Fase 1 renomeada na versão 5"
    stage1.save()
    stage1.requirements.all().delete()
    project_a.refresh_from_db()
    assert list(project_a.stages.values_list("name", flat=True)) == original
    assert project_a.stages.get(order=1).requirements.count() == 6
    assert project_a.lifecycle_version.number == 4
    new_project = org_a.create_project(code="IA-V2")
    assert new_project.lifecycle_version == LifecycleTemplateVersion.objects.get(number=5)
    assert new_project.stages.get(order=1).name == "Fase 1 renomeada na versão 5"


def test_template_v4_incorporates_research_round1_adjustments(project_a):
    """v4: ajustes A02, A06 e A09 derivados da pesquisa com profissionais."""
    assert project_a.lifecycle_version.number == 4
    f1 = project_a.stages.get(order=1).requirements.get(code="F1-R1")
    assert "soluções sem IA" in f1.description
    f2 = project_a.stages.get(order=2)
    assert "financiamento" in f2.requirements.get(code="F2-R1").description
    prelim = f2.requirements.get(code="F2-R6")
    assert prelim.mandatory and prelim.requires_validation
    old = LifecycleTemplateVersion.objects.get(number=3)
    assert old.status == "retired"
    assert not old.stages.get(order=2).requirements.filter(code="F2-R6").exists()
