from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.organizations import rbac
from apps.organizations.models import RoleAssignment

from .models import AuditEvent, AuditResult


def auditable_org_ids(user):
    """Organizações em que o usuário possui `audit.view` (papel org-wide)."""
    allowed_roles = rbac.PERMISSIONS["audit.view"]
    return list(
        RoleAssignment.objects.filter(
            user=user, role__in=allowed_roles, revoked_at__isnull=True, project__isnull=True,
            organization__memberships__user=user, organization__memberships__status="active",
        ).values_list("organization_id", flat=True).distinct()
    )


@login_required
def event_list(request):
    org_ids = auditable_org_ids(request.user)
    if not org_ids:
        from apps.auditlog import services as audit

        audit.record("authz.denied", actor=request.user, result=AuditResult.DENIED, reason="Permissão ausente: audit.view")
        raise PermissionDenied("Consulta de auditoria restrita a perfis autorizados.")
    qs = AuditEvent.objects.filter(organization_id__in=org_ids).select_related("actor")
    filters = {
        "acao": request.GET.get("acao", "").strip(),
        "resultado": request.GET.get("resultado", "").strip(),
        "projeto": request.GET.get("projeto", "").strip(),
        "usuario": request.GET.get("usuario", "").strip(),
    }
    if filters["acao"]:
        qs = qs.filter(action__icontains=filters["acao"])
    if filters["resultado"] in AuditResult.values:
        qs = qs.filter(result=filters["resultado"])
    if filters["projeto"]:
        qs = qs.filter(project_id=filters["projeto"]) if len(filters["projeto"]) == 36 else qs.none()
    if filters["usuario"]:
        qs = qs.filter(actor_repr__icontains=filters["usuario"])
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    return render(
        request, "auditlog/list.html", {"page": page, "filters": filters, "results": AuditResult.choices}
    )


@login_required
def export_events(request):
    """Exportação autorizada da trilha (auditor/segurança/admin org), limitada ao escopo e auditada."""
    from apps.core.exports import csv_response

    org_ids = auditable_org_ids(request.user)
    if not org_ids:
        from apps.auditlog import services as audit

        audit.record("authz.denied", actor=request.user, result=AuditResult.DENIED, reason="Permissão ausente: audit.view")
        raise PermissionDenied("Exportação de auditoria restrita a perfis autorizados.")
    qs = AuditEvent.objects.filter(organization_id__in=org_ids).order_by("-occurred_at")[:5000]
    rows = ([e.occurred_at.isoformat(), e.actor_repr, e.action, e.entity_type, e.entity_id, e.result, e.reason,
             e.correlation_id] for e in qs)
    return csv_response(user=request.user, report="auditoria", filters={"orgs": [str(o) for o in org_ids]},
                        header=["Instante (UTC)", "Ator", "Ação", "Entidade", "ID", "Resultado", "Motivo", "Correlação"],
                        rows=rows, filename="auditoria.csv")
