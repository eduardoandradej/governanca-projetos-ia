"""Utilitários de carregamento de objetos com verificação de escopo (anti-IDOR)."""

from django.core.exceptions import ValidationError
from django.http import Http404

from apps.auditlog import services as audit
from apps.auditlog.models import AuditResult
from apps.organizations import rbac


def get_project_or_404(user, project_id, perm: str = "project.view"):
    """Carrega o projeto e exige permissão. Usuário sem vínculo recebe 404 (não revela existência)."""
    from apps.projects.models import Project

    try:
        project = Project.objects.select_related("organization").get(pk=project_id)
    except (Project.DoesNotExist, ValueError, ValidationError):  # UUID inválido também vira 404
        raise Http404("Projeto não encontrado.") from None
    if not rbac.has_perm(user, "project.view", project.organization, project):
        audit.record(
            "authz.denied",
            actor=user,
            result=AuditResult.DENIED,
            organization_id=project.organization_id,
            project_id=project.pk,
            entity=project,
            reason=f"Acesso fora do escopo ({perm})",
        )
        raise Http404("Projeto não encontrado.")
    if perm != "project.view":
        rbac.require_perm(user, perm, project.organization, project, entity=project)
    return project
