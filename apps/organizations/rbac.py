"""Matriz explícita de permissões (RBAC com escopo de organização e projeto) — RN-002, F08.

Regras:
- Toda verificação ocorre no servidor (views, serviços de domínio, APIs, downloads e consultas analíticas).
- O usuário precisa de vínculo ATIVO com a organização e de um papel ATIVO cujo escopo seja a
  organização inteira (project=None) ou o projeto alvo.
- O administrador da plataforma (superusuário) só possui as permissões em PLATFORM_PERMISSIONS;
  não aprova gates, decisões nem lê dados de projetos sem papel atribuído.
- Segregação de funções (ex.: solicitante ≠ aprovador) é aplicada nos serviços de domínio,
  além desta matriz.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied

from apps.auditlog import services as audit
from apps.auditlog.models import AuditResult

from .models import Membership, MembershipStatus, Role, RoleAssignment

R = Role

ALL_ROLES = frozenset(Role.values)
MANAGEMENT = frozenset({R.ORG_ADMIN, R.PORTFOLIO_MANAGER, R.PROJECT_MANAGER})

PERMISSIONS: dict[str, frozenset[str]] = {
    # Organização
    "org.view": ALL_ROLES,
    "org.manage": frozenset({R.ORG_ADMIN}),
    "roles.manage": frozenset({R.ORG_ADMIN}),
    # Portfólios e projetos
    "portfolio.manage": frozenset({R.ORG_ADMIN, R.PORTFOLIO_MANAGER}),
    "project.view": ALL_ROLES,
    "project.create": frozenset({R.ORG_ADMIN, R.PORTFOLIO_MANAGER, R.PROJECT_MANAGER}),
    "project.edit": MANAGEMENT,
    "project.view_sensitive": frozenset(
        {R.ORG_ADMIN, R.PORTFOLIO_MANAGER, R.SPONSOR, R.PROJECT_MANAGER, R.SECURITY_COMPLIANCE, R.AUDITOR}
    ),
    "project.close": frozenset({R.ORG_ADMIN, R.PORTFOLIO_MANAGER, R.SPONSOR}),
    "project.reopen": frozenset({R.ORG_ADMIN, R.SPONSOR}),
    # Ciclo de vida, requisitos e tarefas
    "lifecycle.template_manage": frozenset({R.ORG_ADMIN}),
    "stage.start": frozenset({R.PROJECT_MANAGER}),
    "requirement.fulfill": frozenset({R.PROJECT_MANAGER, R.TECH_EXECUTOR, R.SECURITY_COMPLIANCE}),
    "requirement.validate": frozenset({R.PROJECT_MANAGER, R.SECURITY_COMPLIANCE, R.GATE_APPROVER}),
    "task.manage": frozenset({R.PROJECT_MANAGER, R.TECH_EXECUTOR}),
    "team.manage": frozenset({R.ORG_ADMIN, R.PROJECT_MANAGER}),
    # Gates
    "gate.request": frozenset({R.PROJECT_MANAGER}),
    "gate.approve": frozenset({R.GATE_APPROVER, R.SPONSOR}),
    "gate.exception.grant": frozenset({R.SPONSOR, R.ORG_ADMIN}),
    "gate.exception.security_ack": frozenset({R.SECURITY_COMPLIANCE}),
    # Evidências
    "evidence.upload": frozenset({R.PROJECT_MANAGER, R.TECH_EXECUTOR, R.SECURITY_COMPLIANCE}),
    "evidence.review": frozenset({R.SECURITY_COMPLIANCE, R.GATE_APPROVER, R.PROJECT_MANAGER}),
    "evidence.download": ALL_ROLES - {R.READER},
    "evidence.inspect": frozenset({R.SECURITY_COMPLIANCE}),
    # Riscos, custos e decisões
    "risk.manage": frozenset({R.PROJECT_MANAGER, R.TECH_EXECUTOR, R.SECURITY_COMPLIANCE}),
    "risk.accept_residual": frozenset({R.SPONSOR}),
    "cost.manage": frozenset({R.PROJECT_MANAGER, R.PORTFOLIO_MANAGER}),
    "decision.record": frozenset({R.PROJECT_MANAGER, R.SPONSOR, R.PORTFOLIO_MANAGER}),
    "decision.approve": frozenset({R.SPONSOR, R.PORTFOLIO_MANAGER}),
    # Dados, informação e conhecimento
    "data.manage": frozenset({R.PROJECT_MANAGER, R.TECH_EXECUTOR}),
    "analytics.view": ALL_ROLES,
    "insight.review": frozenset({R.PROJECT_MANAGER, R.PORTFOLIO_MANAGER, R.SPONSOR}),
    "lesson.manage": frozenset({R.PROJECT_MANAGER, R.PORTFOLIO_MANAGER}),
    "lesson.approve": frozenset({R.PORTFOLIO_MANAGER, R.SPONSOR}),
    "export.data": frozenset({R.ORG_ADMIN, R.PORTFOLIO_MANAGER, R.PROJECT_MANAGER, R.SPONSOR, R.AUDITOR}),
    # Governança e auditoria
    "governance.manage": frozenset({R.ORG_ADMIN}),
    "audit.view": frozenset({R.AUDITOR, R.ORG_ADMIN, R.SECURITY_COMPLIANCE}),
}

PLATFORM_PERMISSIONS = frozenset({"platform.org_create", "platform.membership_manage", "roles.manage", "org.view"})


def _active_membership(user, organization) -> bool:
    return Membership.objects.filter(
        user=user, organization=organization, status=MembershipStatus.ACTIVE, organization__is_active=True
    ).exists()


def roles_for(user, organization, project=None) -> set[str]:
    """Papéis ativos do usuário na organização, considerando escopo do projeto (se informado)."""
    if not user or not user.is_authenticated or not user.is_active:
        return set()
    if not _active_membership(user, organization):
        return set()
    qs = RoleAssignment.objects.filter(user=user, organization=organization, revoked_at__isnull=True)
    if project is None:
        qs = qs.filter(project__isnull=True)
    else:
        if project.organization_id != organization.pk:
            return set()
        qs = qs.filter(project__isnull=True) | qs.filter(project=project)
    return set(qs.values_list("role", flat=True))


def has_perm(user, perm: str, organization, project=None) -> bool:
    if perm not in PERMISSIONS and perm not in PLATFORM_PERMISSIONS:
        raise ValueError(f"Permissão desconhecida: {perm}")
    if user and user.is_authenticated and user.is_active and user.is_superuser and perm in PLATFORM_PERMISSIONS:
        return True
    if organization is None:
        return False
    allowed = PERMISSIONS.get(perm, frozenset())
    return bool(roles_for(user, organization, project) & allowed)


def require_perm(user, perm: str, organization, project=None, *, entity=None) -> None:
    """Lança PermissionDenied e registra a negação na trilha de auditoria."""
    if not has_perm(user, perm, organization, project):
        audit.record(
            "authz.denied",
            actor=user,
            result=AuditResult.DENIED,
            organization_id=organization.pk if organization else None,
            project_id=project.pk if project else None,
            entity=entity,
            reason=f"Permissão ausente: {perm}",
        )
        raise PermissionDenied(f"Você não possui a permissão necessária ({perm}).")


def organizations_for(user):
    """Organizações em que o usuário possui vínculo ativo (base para filtrar listagens)."""
    from .models import Organization

    if not user.is_authenticated:
        return Organization.objects.none()
    return Organization.objects.filter(
        is_active=True, memberships__user=user, memberships__status=MembershipStatus.ACTIVE
    ).distinct()


def visible_project_filter(user):
    """Q para filtrar projetos visíveis: papel org-wide na organização ou papel no próprio projeto."""
    from django.db.models import Q

    org_ids = RoleAssignment.objects.filter(
        user=user,
        revoked_at__isnull=True,
        project__isnull=True,
        organization__memberships__user=user,
        organization__memberships__status=MembershipStatus.ACTIVE,
    ).values("organization_id")
    project_ids = RoleAssignment.objects.filter(
        user=user,
        revoked_at__isnull=True,
        project__isnull=False,
        organization__memberships__user=user,
        organization__memberships__status=MembershipStatus.ACTIVE,
    ).values("project_id")
    return Q(organization_id__in=org_ids) | Q(id__in=project_ids)
