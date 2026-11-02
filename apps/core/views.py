import logging

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.organizations import rbac

logger = logging.getLogger(__name__)


@require_GET
@never_cache
def healthz(request):
    """Verificação simples de saúde: aplicação + banco. Não expõe detalhes internos."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception:  # noqa: BLE001
        logger.exception("healthz: falha ao consultar o banco")
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "error"}, status=status)


@login_required
def dashboard(request):
    from apps.projects.models import Project

    organizations = rbac.organizations_for(request.user)
    projects = (
        Project.objects.filter(rbac.visible_project_filter(request.user))
        .select_related("organization", "manager")
        .order_by("-updated_at")
    )
    context = {"organizations": organizations, "projects": projects[:10], "project_count": projects.count()}
    return render(request, "core/dashboard.html", context)
