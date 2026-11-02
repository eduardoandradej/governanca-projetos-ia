"""Serviços de domínio do ciclo de vida (transações atômicas; views não manipulam regras críticas)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.utils import timezone

from apps.auditlog import services as audit
from apps.organizations import rbac

from .models import (
    STAGE_TRANSITIONS,
    LifecycleTemplateVersion,
    RequirementInstance,
    RequirementStatus,
    RequirementValidation,
    StageInstance,
    StageStatus,
    StageStatusHistory,
    Task,
    TaskDependency,
    TaskStatus,
    TemplateVersionStatus,
    ValidationDecision,
)


class DomainError(ValidationError):
    """Violação de regra de negócio (mensagem exibível ao usuário)."""


def ensure_project_writable(project, *, allow_followup: bool = False) -> None:
    """RN-011: projeto encerrado/cancelado/arquivado não recebe alterações (salvo acompanhamento permitido)."""
    if project.is_terminal and not allow_followup:
        raise DomainError(f"Projeto {project.get_status_display().lower()}: alterações não são permitidas.")


def published_version_for(organization) -> LifecycleTemplateVersion:
    """Versão publicada mais recente: template próprio da organização, senão o padrão do sistema."""
    qs = LifecycleTemplateVersion.objects.filter(status=TemplateVersionStatus.PUBLISHED)
    version = qs.filter(template__organization=organization).order_by("-number").first()
    if version is None:
        version = qs.filter(template__organization__isnull=True).order_by("-number").first()
    if version is None:
        raise DomainError("Não há template de ciclo de vida publicado.")
    return version


def instantiate_lifecycle(project, *, actor) -> list[StageInstance]:
    """Copia fases e requisitos da versão publicada (snapshot) e inicia a fase 1 (RN-003)."""
    version = project.lifecycle_version or published_version_for(project.organization)
    if project.stages.exists():
        raise DomainError("O ciclo de vida deste projeto já foi instanciado.")
    stages = []
    for st in version.stages.order_by("order").prefetch_related("requirements"):
        stage = StageInstance.objects.create(
            project=project, stage_template=st, order=st.order, code=st.code, name=st.name, objective=st.objective,
            cobit_refs=st.cobit_refs, requires_segregation=st.requires_segregation,
            block_on_critical_risk=st.block_on_critical_risk, has_exit_gate=st.has_exit_gate, created_by=actor,
        )
        RequirementInstance.objects.bulk_create(
            [
                RequirementInstance(
                    stage=stage, template=rt, order=rt.order, code=rt.code, title=rt.title,
                    description=rt.description, mandatory=rt.mandatory, requires_evidence=rt.requires_evidence,
                    evidence_kind=rt.evidence_kind, requires_validation=rt.requires_validation,
                    is_legal=rt.is_legal, cobit_ref=rt.cobit_ref, created_by=actor,
                )
                for rt in st.requirements.order_by("order")
            ]
        )
        stages.append(stage)
    if len(stages) < 1:
        raise DomainError("Template sem fases.")
    project.lifecycle_version = version
    project.save(update_fields=["lifecycle_version", "updated_at"])
    _transition(stages[0], StageStatus.IN_PROGRESS, actor=actor, reason="Início automático do projeto (fase 1)")
    return stages


def _transition(stage: StageInstance, to_status: str, *, actor, reason: str = "") -> StageInstance:
    """Única porta de mudança de estado de fase; valida a máquina de estados e registra histórico/auditoria."""
    from_status = stage.status
    if to_status not in STAGE_TRANSITIONS[from_status]:
        raise DomainError(
            f"Transição inválida da fase '{stage.name}': {stage.get_status_display()} → "
            f"{StageStatus(to_status).label}."
        )
    now = timezone.now()
    stage.status = to_status
    stamp = {
        StageStatus.IN_PROGRESS: "started_at",
        StageStatus.SUBMITTED: "submitted_at",
        StageStatus.APPROVED: "approved_at",
        StageStatus.COMPLETED: "completed_at",
    }.get(to_status)
    fields = ["status", "version", "updated_at"]
    if stamp and (stamp != "started_at" or stage.started_at is None):
        setattr(stage, stamp, now)
        fields.append(stamp)
    stage.version += 1
    stage.save(update_fields=fields)
    StageStatusHistory.objects.create(
        stage=stage, from_status=from_status, to_status=to_status, changed_by=actor, reason=reason
    )
    audit.record(
        "stage.transition", actor=actor, organization_id=stage.project.organization_id, project_id=stage.project_id,
        entity=stage, entity_version=stage.version, before={"status": from_status}, after={"status": to_status},
        reason=reason,
    )
    return stage


def transition_stage(stage: StageInstance, to_status: str, *, actor, reason: str = "") -> StageInstance:
    """Transição usada por outros serviços de domínio (gates). Exige que o chamador já detenha o lock."""
    return _transition(stage, to_status, actor=actor, reason=reason)


@audit.atomic_service
def resume_stage(stage_id, *, actor, reason: str = "") -> StageInstance:
    """Retoma fase devolvida (RETURNED → IN_PROGRESS) para retrabalho."""
    stage = StageInstance.objects.select_for_update().select_related("project__organization").get(pk=stage_id)
    rbac.require_perm(actor, "stage.start", stage.project.organization, stage.project, entity=stage)
    ensure_project_writable(stage.project)
    if stage.status != StageStatus.RETURNED:
        raise DomainError("Somente fases devolvidas podem ser retomadas.")
    return _transition(stage, StageStatus.IN_PROGRESS, actor=actor, reason=reason or "Retrabalho após devolução")


def _lock_requirement(requirement_id) -> RequirementInstance:
    return (
        RequirementInstance.objects.select_for_update()
        .select_related("stage__project__organization")
        .get(pk=requirement_id)
    )


@audit.atomic_service
def fulfill_requirement(requirement_id, *, actor, note: str) -> RequirementInstance:
    """Registra o atendimento verificável do requisito (não basta marcar caixa: exige registro textual)."""
    req = _lock_requirement(requirement_id)
    stage, project = req.stage, req.stage.project
    rbac.require_perm(actor, "requirement.fulfill", project.organization, project, entity=req)
    ensure_project_writable(project)
    if stage.status not in (StageStatus.IN_PROGRESS, StageStatus.RETURNED, StageStatus.APPROVED):
        raise DomainError("Requisitos só podem ser atendidos em fase em andamento ou devolvida.")
    note = (note or "").strip()
    if len(note) < 10:
        raise DomainError("Descreva o atendimento do requisito (mínimo de 10 caracteres).")
    before = {"status": req.status, "version": req.version, "note": req.fulfillment_note}
    req.fulfillment_note = note
    req.fulfilled_by = actor
    req.fulfilled_at = timezone.now()
    req.status = RequirementStatus.FULFILLED if req.requires_validation else RequirementStatus.VALIDATED
    req.version += 1
    req.save()
    audit.record(
        "requirement.fulfill", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=req, entity_version=req.version, before=before,
        after={"status": req.status, "version": req.version, "note": note},
    )
    _flag_revalidation_if_approved(stage, actor=actor, cause=f"Requisito {req.code} alterado após aprovação")
    return req


@audit.atomic_service
def validate_requirement(requirement_id, *, actor, decision: str, comment: str) -> RequirementInstance:
    req = _lock_requirement(requirement_id)
    project = req.stage.project
    rbac.require_perm(actor, "requirement.validate", project.organization, project, entity=req)
    ensure_project_writable(project)
    if decision not in ValidationDecision.values:
        raise DomainError("Decisão de validação inválida.")
    if req.status != RequirementStatus.FULFILLED:
        raise DomainError("Somente requisitos atendidos e aguardando validação podem ser validados.")
    if req.fulfilled_by_id == actor.pk:
        raise PermissionDenied("Quem registrou o atendimento não pode validá-lo (segregação de funções).")
    comment = (comment or "").strip()
    if not comment:
        raise DomainError("O parecer da validação é obrigatório.")
    RequirementValidation.objects.create(
        requirement=req, validator=actor, decision=decision, comment=comment, requirement_version=req.version
    )
    before = {"status": req.status}
    req.status = RequirementStatus.VALIDATED if decision == ValidationDecision.APPROVED else RequirementStatus.REJECTED
    req.save(update_fields=["status", "updated_at"])
    audit.record(
        "requirement.validate", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=req, entity_version=req.version, before=before, after={"status": req.status}, reason=comment,
    )
    return req


def _flag_revalidation_if_approved(stage: StageInstance, *, actor, cause: str) -> None:
    """RN-010: mudança após aprovação força revalidação do gate da fase (implementado em governance)."""
    if stage.status in (StageStatus.APPROVED, StageStatus.COMPLETED):
        try:
            from apps.governance.services import flag_revalidation
        except ImportError:  # módulo de gates ainda não instalado
            return
        flag_revalidation(stage, actor=actor, cause=cause)


# --------------------------------------------------------------------------------------- Tarefas (F03)


def _validate_assignee(project, assignee):
    """Tarefas não podem ser atribuídas a alguém fora do escopo do projeto."""
    if assignee is None:
        return
    if not rbac.roles_for(assignee, project.organization, project):
        raise DomainError("O responsável precisa ter papel ativo nesta organização/projeto.")


@audit.atomic_service
def create_task(*, actor, project, stage, title: str, **fields) -> Task:
    rbac.require_perm(actor, "task.manage", project.organization, project, entity=project)
    ensure_project_writable(project)
    if stage.project_id != project.pk:
        raise DomainError("A fase não pertence ao projeto.")  # RN-021
    team = fields.get("team")
    if team is not None and team.organization_id != project.organization_id:
        raise DomainError("A equipe não pertence à organização do projeto.")
    _validate_assignee(project, fields.get("assignee"))
    task = Task.objects.create(project=project, stage=stage, title=title.strip(), created_by=actor, **fields)
    audit.record(
        "task.create", actor=actor, organization_id=project.organization_id, project_id=project.pk, entity=task,
        after={"title": task.title, "stage": stage.order, "assignee": str(task.assignee_id or "")},
    )
    return task


@audit.atomic_service
def update_task_status(task_id, *, actor, status: str) -> Task:
    task = Task.objects.select_for_update().select_related("project__organization").get(pk=task_id)
    project = task.project
    is_assignee = task.assignee_id == actor.pk and rbac.has_perm(actor, "project.view", project.organization, project)
    if not is_assignee:
        rbac.require_perm(actor, "task.manage", project.organization, project, entity=task)
    ensure_project_writable(project)
    if status not in TaskStatus.values:
        raise DomainError("Status de tarefa inválido.")
    if status == TaskStatus.DONE:
        pending = TaskDependency.objects.filter(task=task).filter(~Q(depends_on__status=TaskStatus.DONE))
        if pending.exists():
            raise DomainError("A tarefa possui dependências não concluídas.")
    before = {"status": task.status}
    task.status = status
    task.completed_at = timezone.now() if status == TaskStatus.DONE else None
    task.save(update_fields=["status", "completed_at", "updated_at"])
    audit.record(
        "task.status", actor=actor, organization_id=project.organization_id, project_id=project.pk, entity=task,
        before=before, after={"status": status},
    )
    return task


@audit.atomic_service
def add_task_dependency(*, actor, task, depends_on) -> TaskDependency:
    rbac.require_perm(actor, "task.manage", task.project.organization, task.project, entity=task)
    if task.project_id != depends_on.project_id:
        raise DomainError("Dependências só entre tarefas do mesmo projeto.")
    if task.pk == depends_on.pk:
        raise DomainError("Uma tarefa não pode depender de si mesma.")
    if TaskDependency.objects.filter(task=depends_on, depends_on=task).exists():
        raise DomainError("Dependência circular.")
    dep, _ = TaskDependency.objects.get_or_create(task=task, depends_on=depends_on)
    return dep


def stage_progress(stage: StageInstance) -> dict:
    """Percentual de requisitos obrigatórios validados. Sem requisitos → None ('Sem dados', não 100%)."""
    mandatory = [r for r in stage.requirements.all() if r.mandatory]
    total = len(mandatory)
    done = sum(1 for r in mandatory if r.status == RequirementStatus.VALIDATED)
    return {"total": total, "done": done, "percent": round(100 * done / total) if total else None}
