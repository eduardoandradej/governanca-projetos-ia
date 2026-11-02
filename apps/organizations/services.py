"""Serviços de domínio de organizações, vínculos e papéis (RN-015, RN-021)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.text import slugify

from apps.auditlog import services as audit
from apps.auditlog.models import AuditResult

from . import rbac
from .models import Membership, MembershipStatus, Organization, Role, RoleAssignment


@audit.atomic_service
def create_organization(*, actor, name: str, description: str = "", is_demo: bool = False) -> Organization:
    if not rbac.has_perm(actor, "platform.org_create", None):
        audit.record("org.create", actor=actor, result=AuditResult.DENIED, reason="Somente administrador da plataforma")
        raise PermissionDenied("Somente o administrador da plataforma pode criar organizações.")
    org = Organization.objects.create(
        name=name.strip(), slug=slugify(name)[:60], description=description, is_demo=is_demo, created_by=actor
    )
    audit.record("org.create", actor=actor, organization_id=org.pk, entity=org, after={"name": org.name})
    return org


@audit.atomic_service
def add_member(*, actor, organization: Organization, user, job_title: str = "") -> Membership:
    if not (rbac.has_perm(actor, "org.manage", organization) or rbac.has_perm(actor, "platform.membership_manage", None)):
        rbac.require_perm(actor, "org.manage", organization)
    membership, created = Membership.objects.get_or_create(
        organization=organization, user=user, defaults={"job_title": job_title, "created_by": actor}
    )
    if not created and membership.status != MembershipStatus.ACTIVE:
        membership.status = MembershipStatus.ACTIVE
        membership.save(update_fields=["status", "updated_at"])
    audit.record(
        "membership.add",
        actor=actor,
        organization_id=organization.pk,
        entity=membership,
        after={"user": user.username, "status": membership.status, "created": created},
    )
    return membership


@audit.atomic_service
def assign_role(*, actor, organization: Organization, user, role: str, project=None, reason: str = "") -> RoleAssignment:
    """Concede papel. Impede autoelevação: ninguém concede papel a si mesmo (exceto bootstrap por sistema)."""
    if role not in Role.values:
        raise ValidationError("Papel inválido.")
    rbac.require_perm(actor, "roles.manage", organization)
    if actor is not None and actor.pk == user.pk:
        audit.record(
            "role.assign",
            actor=actor,
            result=AuditResult.DENIED,
            organization_id=organization.pk,
            reason="Tentativa de autoelevação de privilégio",
            after={"role": role},
        )
        raise PermissionDenied("Não é permitido conceder papéis a si mesmo.")
    if not Membership.objects.filter(organization=organization, user=user, status=MembershipStatus.ACTIVE).exists():
        raise ValidationError("O usuário precisa ter vínculo ativo com a organização.")
    if project is not None and project.organization_id != organization.pk:
        raise ValidationError("O projeto não pertence a esta organização.")  # RN-021
    existing = RoleAssignment.objects.filter(
        organization=organization, user=user, role=role, project=project, revoked_at__isnull=True
    ).first()
    if existing:
        return existing  # idempotente
    assignment = RoleAssignment.objects.create(
        organization=organization, user=user, role=role, project=project,
        granted_by=actor, created_by=actor, reason=reason,
    )
    audit.record(
        "role.assign",
        actor=actor,
        organization_id=organization.pk,
        project_id=project.pk if project else None,
        entity=assignment,
        after={"user": user.username, "role": role, "project": project.code if project else None},
        reason=reason,
    )
    return assignment


@audit.atomic_service
def revoke_role(*, actor, assignment: RoleAssignment, reason: str = "") -> RoleAssignment:
    assignment = RoleAssignment.objects.select_for_update().get(pk=assignment.pk)
    rbac.require_perm(actor, "roles.manage", assignment.organization)
    if actor.pk == assignment.user_id:
        raise PermissionDenied("Não é permitido revogar os próprios papéis por esta via.")
    if assignment.revoked_at:
        return assignment
    assignment.revoked_at = timezone.now()
    assignment.revoked_by = actor
    assignment.save(update_fields=["revoked_at", "revoked_by", "updated_at"])
    audit.record(
        "role.revoke",
        actor=actor,
        organization_id=assignment.organization_id,
        project_id=assignment.project_id,
        entity=assignment,
        before={"role": assignment.role, "active": True},
        after={"role": assignment.role, "active": False},
        reason=reason,
    )
    return assignment


def bootstrap_role(*, organization: Organization, user, role: str, project=None, reason: str = "") -> RoleAssignment:
    """Concessão por ator de SISTEMA (comandos de instalação/seed). Sempre auditada como 'system'."""
    Membership.objects.get_or_create(organization=organization, user=user)
    assignment, _ = RoleAssignment.objects.get_or_create(
        organization=organization, user=user, role=role, project=project, revoked_at=None,
        defaults={"reason": reason or "bootstrap"},
    )
    audit.record(
        "role.assign", system=True, actor_repr="system", organization_id=organization.pk,
        project_id=project.pk if project else None, entity=assignment,
        after={"user": user.username, "role": role}, reason=reason or "bootstrap",
    )
    return assignment
