"""Requisitos, máquina de estados das fases e tarefas (F02/F03)."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from apps.lifecycle import services
from apps.lifecycle.models import RequirementStatus, StageStatus, TaskStatus

pytestmark = pytest.mark.django_db


def _stage1(project):
    return project.stages.get(order=1)


def test_fulfill_requires_verifiable_note_and_permission(org_a, project_a):
    req = _stage1(project_a).requirements.get(code="F1-R2")
    with pytest.raises(ValidationError, match="mínimo"):
        services.fulfill_requirement(req.pk, actor=org_a.manager, note="ok")
    with pytest.raises(PermissionDenied):
        services.fulfill_requirement(req.pk, actor=org_a.reader, note="Patrocinador nomeado em ata.")
    req = services.fulfill_requirement(req.pk, actor=org_a.manager, note="Patrocinador nomeado em ata 01.")
    assert req.status == RequirementStatus.FULFILLED and req.version == 2


def test_validation_requires_segregation_and_comment(org_a, project_a):
    req = _stage1(project_a).requirements.get(code="F1-R2")
    services.fulfill_requirement(req.pk, actor=org_a.manager, note="Patrocinador nomeado em ata 01.")
    with pytest.raises(PermissionDenied, match="segregação"):
        services.validate_requirement(req.pk, actor=org_a.manager, decision="approved", comment="ok")
    with pytest.raises(ValidationError, match="parecer"):
        services.validate_requirement(req.pk, actor=org_a.security, decision="approved", comment=" ")
    req = services.validate_requirement(req.pk, actor=org_a.security, decision="approved", comment="Conferido.")
    assert req.status == RequirementStatus.VALIDATED
    assert req.validations.get().requirement_version == 2


def test_stage_state_machine_rejects_invalid_transition(org_a, project_a):
    stage2 = project_a.stages.get(order=2)
    with pytest.raises(ValidationError, match="Transição inválida"):
        services.transition_stage(stage2, StageStatus.APPROVED, actor=org_a.manager)


def test_cannot_fulfill_requirement_of_not_started_stage(org_a, project_a):
    req = project_a.stages.get(order=2).requirements.first()
    with pytest.raises(ValidationError, match="andamento"):
        services.fulfill_requirement(req.pk, actor=org_a.manager, note="Tentativa fora da fase.")


def test_stage_progress_without_requirements_reports_no_data(org_a, project_a):
    stage = _stage1(project_a)
    assert services.stage_progress(stage) == {"total": 6, "done": 0, "percent": 0}
    stage.requirements.update(mandatory=False)
    assert services.stage_progress(stage)["percent"] is None  # "Sem dados", nunca 100% (T-028)


def test_task_assignment_restricted_to_project_scope(org_a, org_b, project_a):
    stage = _stage1(project_a)
    with pytest.raises(ValidationError, match="papel ativo"):
        services.create_task(actor=org_a.manager, project=project_a, stage=stage, title="X", assignee=org_b.executor)
    with pytest.raises(ValidationError, match="papel ativo"):
        services.create_task(actor=org_a.manager, project=project_a, stage=stage, title="X", assignee=org_a.outsider)
    task = services.create_task(
        actor=org_a.manager, project=project_a, stage=stage, title="Levantar casos de uso", assignee=org_a.executor
    )
    assert task.status == TaskStatus.TODO


def test_task_dependencies_block_completion_and_cycles(org_a, project_a):
    stage = _stage1(project_a)
    t1 = services.create_task(actor=org_a.manager, project=project_a, stage=stage, title="Base")
    t2 = services.create_task(actor=org_a.manager, project=project_a, stage=stage, title="Depende")
    services.add_task_dependency(actor=org_a.manager, task=t2, depends_on=t1)
    with pytest.raises(ValidationError, match="circular"):
        services.add_task_dependency(actor=org_a.manager, task=t1, depends_on=t2)
    with pytest.raises(ValidationError, match="dependências"):
        services.update_task_status(t2.pk, actor=org_a.manager, status=TaskStatus.DONE)
    services.update_task_status(t1.pk, actor=org_a.manager, status=TaskStatus.DONE)
    assert services.update_task_status(t2.pk, actor=org_a.manager, status=TaskStatus.DONE).completed_at


def test_assignee_can_update_own_task_but_reader_cannot(org_a, project_a):
    stage = _stage1(project_a)
    task = services.create_task(actor=org_a.manager, project=project_a, stage=stage, title="T", assignee=org_a.security)
    services.update_task_status(task.pk, actor=org_a.security, status=TaskStatus.DOING)
    with pytest.raises(PermissionDenied):
        services.update_task_status(task.pk, actor=org_a.reader, status=TaskStatus.DONE)


def test_task_status_via_htmx_and_requirement_via_web(client, org_a, project_a):
    stage = _stage1(project_a)
    task = services.create_task(actor=org_a.manager, project=project_a, stage=stage, title="Kanban")
    client.force_login(org_a.manager)
    resp = client.post(
        reverse("lifecycle:task_status", args=[project_a.pk, task.pk]), {"status": "doing"}, HTTP_HX_REQUEST="true"
    )
    assert resp.status_code == 200 and "Kanban" in resp.content.decode()
    req = stage.requirements.get(code="F1-R3")
    client.post(
        reverse("lifecycle:requirement_fulfill", args=[project_a.pk, stage.pk, req.pk]),
        {"note": "Metas definidas no termo de abertura."},
    )
    req.refresh_from_db()
    assert req.status == RequirementStatus.FULFILLED
    page = client.get(reverse("lifecycle:stage", args=[project_a.pk, stage.pk]))
    assert page.status_code == 200 and "Metas definidas" in page.content.decode()


def test_closed_project_blocks_requirement_and_task_changes(org_a, project_a):
    from apps.projects.services import change_status

    change_status(project_a.pk, actor=org_a.sponsor, to_status="cancelled", reason="Cancelado pelo comitê")
    req = _stage1(project_a).requirements.first()
    with pytest.raises(ValidationError, match="não são permitidas"):
        services.fulfill_requirement(req.pk, actor=org_a.manager, note="Depois do cancelamento.")
