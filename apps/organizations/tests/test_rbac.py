"""RBAC com escopo, isolamento entre organizações, papéis e trilha append-only (RN-002, RN-015, T-013/T-014/T-022)."""

import pytest
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.db.utils import DatabaseError
from django.urls import reverse

from apps.auditlog.models import AppendOnlyError, AuditEvent
from apps.organizations import rbac, services
from apps.organizations.models import Membership, Role, RoleAssignment
from tests_support.factories import make_user

pytestmark = pytest.mark.django_db


def test_permission_matrix_scoped_by_organization(org_a, org_b):
    assert rbac.has_perm(org_a.manager, "project.create", org_a.org)
    assert not rbac.has_perm(org_a.manager, "project.create", org_b.org)
    assert not rbac.has_perm(org_a.outsider, "project.view", org_a.org)  # membro sem papel
    assert not rbac.has_perm(org_a.reader, "project.edit", org_a.org)
    assert rbac.has_perm(org_a.auditor, "audit.view", org_a.org)
    assert not rbac.has_perm(org_a.manager, "gate.approve", org_a.org)


def test_unknown_permission_raises(org_a):
    with pytest.raises(ValueError):
        rbac.has_perm(org_a.manager, "nao.existe", org_a.org)


def test_suspended_membership_loses_access(org_a):
    Membership.objects.filter(user=org_a.manager).update(status="suspended")
    assert not rbac.has_perm(org_a.manager, "project.view", org_a.org)


def test_project_scoped_role_only_applies_to_that_project(org_a):
    p1 = org_a.create_project(code="IA-P1")
    p2 = org_a.create_project(code="IA-P2")
    consultant = org_a.add_user("consultant")
    services.bootstrap_role(organization=org_a.org, user=consultant, role=Role.TECH_EXECUTOR, project=p1)
    assert rbac.has_perm(consultant, "task.manage", org_a.org, p1)
    assert not rbac.has_perm(consultant, "task.manage", org_a.org, p2)
    assert not rbac.has_perm(consultant, "task.manage", org_a.org)


def test_platform_admin_has_no_implicit_business_rights(org_a, project_a):
    root = make_user("root", is_superuser=True, is_staff=True)
    assert rbac.has_perm(root, "platform.org_create", None)
    assert not rbac.has_perm(root, "gate.approve", org_a.org, project_a)
    assert not rbac.has_perm(root, "project.view", org_a.org, project_a)
    assert not rbac.has_perm(root, "decision.approve", org_a.org)


def test_T014_common_user_cannot_change_roles(client, org_a):
    client.force_login(org_a.manager)
    resp = client.post(
        reverse("organizations:detail", args=[org_a.org.pk]),
        {"user": org_a.reader.pk, "role": Role.ORG_ADMIN, "reason": "tentativa"},
    )
    assert resp.status_code == 403
    assert not RoleAssignment.objects.filter(user=org_a.reader, role=Role.ORG_ADMIN).exists()
    assert AuditEvent.objects.filter(action="authz.denied", actor=org_a.manager, result="denied").exists()


def test_no_self_elevation_even_for_org_admin(org_a):
    with pytest.raises(PermissionDenied):
        services.assign_role(actor=org_a.admin, organization=org_a.org, user=org_a.admin, role=Role.GATE_APPROVER)
    assert AuditEvent.objects.filter(action="role.assign", result="denied", actor=org_a.admin).exists()


def test_org_admin_assigns_and_revokes_role_with_history(org_a):
    a = services.assign_role(
        actor=org_a.admin, organization=org_a.org, user=org_a.reader, role=Role.TECH_EXECUTOR, reason="Alocação"
    )
    again = services.assign_role(actor=org_a.admin, organization=org_a.org, user=org_a.reader, role=Role.TECH_EXECUTOR)
    assert again.pk == a.pk  # idempotente (T-025)
    services.revoke_role(actor=org_a.admin, assignment=a, reason="Fim da alocação")
    a.refresh_from_db()
    assert a.revoked_at is not None  # revogação lógica preserva histórico
    assert not rbac.has_perm(org_a.reader, "task.manage", org_a.org)
    assert AuditEvent.objects.filter(action="role.revoke", entity_id=str(a.pk)).count() == 1


def test_cannot_assign_role_to_non_member_or_cross_org_project(org_a, org_b):
    project_b = org_b.create_project(code="IA-B1")
    with pytest.raises(Exception, match="vínculo ativo"):
        services.assign_role(actor=org_a.admin, organization=org_a.org, user=org_b.manager, role=Role.READER)
    with pytest.raises(Exception, match="não pertence"):
        services.assign_role(
            actor=org_a.admin, organization=org_a.org, user=org_a.reader, role=Role.READER, project=project_b
        )


def test_T002_org_detail_hidden_from_other_org(client, org_a, org_b):
    client.force_login(org_b.admin)
    assert client.get(reverse("organizations:detail", args=[org_a.org.pk])).status_code == 403


def test_audit_event_append_only_in_application(org_a):
    ev = AuditEvent.objects.first()
    ev.reason = "adulterado"
    with pytest.raises(AppendOnlyError):
        ev.save()
    with pytest.raises(AppendOnlyError):
        ev.delete()


def test_audit_event_append_only_in_database_trigger(org_a):
    ev = AuditEvent.objects.first()
    with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
        AuditEvent.objects.filter(pk=ev.pk).update(reason="adulterado")
    with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
        with connection.cursor() as cur:
            cur.execute("DELETE FROM auditlog_auditevent WHERE id = %s", [ev.pk])
    assert AuditEvent.objects.filter(pk=ev.pk, reason=ev.reason).exists()


def test_T013_auditor_reads_audit_but_cannot_modify_project(client, org_a, project_a):
    client.force_login(org_a.auditor)
    resp = client.get(reverse("auditlog:list"))
    assert resp.status_code == 200 and "project.create" in resp.content.decode()
    assert client.get(reverse("projects:edit", args=[project_a.pk])).status_code == 403
    assert client.post(reverse("projects:edit", args=[project_a.pk]), {"name": "x"}).status_code == 403


def test_audit_list_restricted_and_scoped(client, org_a, org_b, project_a):
    client.force_login(org_a.manager)
    assert client.get(reverse("auditlog:list")).status_code == 403
    client.force_login(org_b.auditor)
    body = client.get(reverse("auditlog:list")).content.decode()
    assert "IA-ALFA-01" not in body and str(project_a.pk) not in body
