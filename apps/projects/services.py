"""Serviços de domínio de projetos (RN-001, RN-011, RN-021)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.auditlog import services as audit
from apps.lifecycle.services import DomainError, instantiate_lifecycle
from apps.organizations import rbac

from .models import TERMINAL_STATUSES, Portfolio, Project, ProjectStatus, ProjectStatusHistory

AUDITED_FIELDS = [
    "code", "name", "description", "business_case", "business_objectives", "target_indicators", "platform_type",
    "deployment_approach", "technology_metadata", "sponsor_id", "manager_id", "technical_lead_id", "priority",
    "criticality", "data_classification", "start_date", "due_date", "planned_cost", "currency", "portfolio_id",
]


def _snapshot(project: Project) -> dict:
    return {f: getattr(project, f) for f in AUDITED_FIELDS}


def _check_people_in_org(organization, *users):
    """RN-021: patrocinador, gerente e responsável técnico precisam ter vínculo com a organização."""
    from apps.organizations.models import Membership, MembershipStatus

    for user in users:
        if user is None:
            continue
        if not Membership.objects.filter(
            organization=organization, user=user, status=MembershipStatus.ACTIVE
        ).exists():
            raise DomainError(f"{user} não possui vínculo ativo com a organização.")


@audit.atomic_service
def create_project(*, actor, organization, **data) -> Project:
    """RN-001: organização, patrocinador, gerente, finalidade e código único. Recebe as 7 fases (T-003)."""
    rbac.require_perm(actor, "project.create", organization)
    portfolio: Portfolio | None = data.get("portfolio")
    if portfolio is not None and portfolio.organization_id != organization.pk:
        raise DomainError("O portfólio não pertence à organização.")
    _check_people_in_org(organization, data.get("sponsor"), data.get("manager"), data.get("technical_lead"))
    for required in ("code", "name", "description", "business_case", "sponsor", "manager"):
        if not data.get(required):
            raise DomainError(f"Campo obrigatório ausente: {Project._meta.get_field(required).verbose_name}.")
    project = Project(organization=organization, created_by=actor, **data)
    project.full_clean(exclude=["lifecycle_version"])
    try:
        with transaction.atomic():
            project.save()
    except IntegrityError as exc:
        raise DomainError("Já existe projeto com este código na organização.") from exc
    ProjectStatusHistory.objects.create(project=project, to_status=project.status, changed_by=actor, reason="Criação")
    audit.record(
        "project.create", actor=actor, organization_id=organization.pk, project_id=project.pk, entity=project,
        entity_version=project.version, after=_snapshot(project),
    )
    instantiate_lifecycle(project, actor=actor)
    return project


@audit.atomic_service
def update_project(project_id, *, actor, expected_version: int | None = None, **changes) -> Project:
    project = Project.objects.select_for_update().select_related("organization").get(pk=project_id)
    rbac.require_perm(actor, "project.edit", project.organization, project, entity=project)
    if project.is_terminal:
        raise DomainError("Projeto encerrado/cancelado/arquivado não pode ser editado.")
    if expected_version is not None and expected_version != project.version:
        raise DomainError("O projeto foi alterado por outra pessoa. Recarregue a página e tente novamente.")
    if "portfolio" in changes and changes["portfolio"] and changes["portfolio"].organization_id != project.organization_id:
        raise DomainError("O portfólio não pertence à organização.")
    _check_people_in_org(project.organization, changes.get("sponsor"), changes.get("manager"), changes.get("technical_lead"))
    changes.pop("organization", None)
    changes.pop("status", None)
    before = _snapshot(project)
    for key, value in changes.items():
        setattr(project, key, value)
    project.version += 1
    try:
        project.full_clean(exclude=["lifecycle_version"])
    except ValidationError:
        raise
    project.save()
    after = _snapshot(project)
    diff_before = {k: v for k, v in before.items() if after.get(k) != v}
    diff_after = {k: after[k] for k in diff_before}
    audit.record(
        "project.update", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=project, entity_version=project.version, before=diff_before, after=diff_after,
    )
    return project


_STATUS_PERMS = {
    ProjectStatus.CLOSED: "project.close",
    ProjectStatus.CANCELLED: "project.close",
    ProjectStatus.ON_HOLD: "project.edit",
    ProjectStatus.ARCHIVED: "project.close",
    ProjectStatus.ACTIVE: "project.edit",
}


@audit.atomic_service
def change_status(project_id, *, actor, to_status: str, reason: str, decision_id=None) -> Project:
    """Encerramento, cancelamento, suspensão, arquivamento e reabertura (reabertura exige decisão formal)."""
    project = Project.objects.select_for_update().select_related("organization").get(pk=project_id)
    if to_status not in ProjectStatus.values:
        raise DomainError("Status inválido.")
    from_status = project.status
    if from_status == to_status:
        return project
    reopening = from_status in TERMINAL_STATUSES and to_status == ProjectStatus.ACTIVE
    perm = "project.reopen" if reopening else _STATUS_PERMS[to_status]
    rbac.require_perm(actor, perm, project.organization, project, entity=project)
    reason = (reason or "").strip()
    if len(reason) < 10:
        raise DomainError("Informe a justificativa/decisão formal (mínimo de 10 caracteres).")
    if from_status == ProjectStatus.ARCHIVED and not reopening:
        raise DomainError("Projeto arquivado só pode ser reaberto por decisão formal.")
    if reopening:  # reabertura exige decisão formal aprovada (tema "reabertura") do próprio projeto
        from apps.risks.services import approved_reopen_decision

        decision = approved_reopen_decision(project, decision_id) if decision_id else None
        if decision is None:
            raise DomainError("A reabertura exige uma decisão formal aprovada (tema: reabertura de projeto).")
        reason = f"{reason} [decisão {decision.code} v{decision.version}]"
    project.status = to_status
    project.version += 1
    project.save(update_fields=["status", "version", "updated_at"])
    ProjectStatusHistory.objects.create(
        project=project, from_status=from_status, to_status=to_status, changed_by=actor, reason=reason
    )
    audit.record(
        "project.status", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=project, entity_version=project.version, before={"status": from_status},
        after={"status": to_status}, reason=reason,
    )
    return project
