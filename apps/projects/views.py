from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect, render

from apps.core.http import get_project_or_404
from apps.lifecycle.models import StageStatus, TaskStatus
from apps.lifecycle.services import stage_progress
from apps.organizations import rbac
from apps.organizations.models import Organization

from . import services
from .forms import PROJECT_FIELDS, ProjectForm, StatusChangeForm
from .models import DeploymentApproach, PlatformType, Project, ProjectStatus


def _errors(exc) -> str:
    return " ".join(getattr(exc, "messages", [str(exc)]))


@login_required
def project_list(request):
    qs = (
        Project.objects.filter(rbac.visible_project_filter(request.user))
        .select_related("organization", "manager", "portfolio")
        .annotate(open_tasks=Count("tasks", filter=~Q(tasks__status=TaskStatus.DONE)))
    )
    f = {k: request.GET.get(k, "").strip() for k in ("q", "status", "organizacao", "plataforma", "implantacao")}
    if f["q"]:
        qs = qs.filter(Q(name__icontains=f["q"]) | Q(code__icontains=f["q"]))
    if f["status"] in ProjectStatus.values:
        qs = qs.filter(status=f["status"])
    if f["organizacao"]:
        qs = qs.filter(organization__slug=f["organizacao"])
    if f["plataforma"] in PlatformType.values:
        qs = qs.filter(platform_type=f["plataforma"])
    if f["implantacao"] in DeploymentApproach.values:
        qs = qs.filter(deployment_approach=f["implantacao"])
    page = Paginator(qs.order_by("organization__name", "code"), 25).get_page(request.GET.get("page"))
    creatable = [o for o in rbac.organizations_for(request.user) if rbac.has_perm(request.user, "project.create", o)]
    return render(
        request,
        "projects/list.html",
        {
            "page": page, "filters": f, "statuses": ProjectStatus.choices, "platforms": PlatformType.choices,
            "approaches": DeploymentApproach.choices, "organizations": rbac.organizations_for(request.user),
            "creatable_orgs": creatable,
        },
    )


@login_required
def project_create(request, org_id):
    try:
        org = Organization.objects.get(pk=org_id, is_active=True)
    except Organization.DoesNotExist:
        raise Http404 from None
    rbac.require_perm(request.user, "project.create", org)
    form = ProjectForm(request.POST or None, organization=org)
    if request.method == "POST" and form.is_valid():
        data = {k: form.cleaned_data.get(k) for k in PROJECT_FIELDS}
        try:
            project = services.create_project(actor=request.user, organization=org, **data)
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, _errors(exc))
        else:
            messages.success(request, f"Projeto {project.code} criado com as fases do ciclo de vida.")
            return redirect("projects:detail", project_id=project.pk)
    return render(request, "projects/form.html", {"form": form, "org": org, "creating": True})


@login_required
def project_edit(request, project_id):
    project = get_project_or_404(request.user, project_id, "project.edit")
    form = ProjectForm(request.POST or None, instance=project, organization=project.organization)
    if request.method == "POST" and form.is_valid():
        data = {k: form.cleaned_data.get(k) for k in PROJECT_FIELDS}
        try:
            services.update_project(
                project.pk, actor=request.user, expected_version=int(request.POST.get("version", 0)), **data
            )
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, _errors(exc))
        else:
            messages.success(request, "Projeto atualizado; alterações registradas na auditoria.")
            return redirect("projects:detail", project_id=project.pk)
    return render(request, "projects/form.html", {"form": form, "org": project.organization, "project": project})


@login_required
def project_detail(request, project_id):
    project = get_project_or_404(request.user, project_id)
    stages = list(project.stages.prefetch_related("requirements").order_by("order"))
    for st in stages:
        st.progress = stage_progress(st)
    user, org = request.user, project.organization
    perms = {
        p: rbac.has_perm(user, p, org, project)
        for p in ("project.edit", "project.close", "project.reopen", "project.view_sensitive", "task.manage")
    }
    status_choices = [c for c in ProjectStatus.choices if c[0] != project.status]
    return render(
        request,
        "projects/detail.html",
        {
            "project": project, "stages": stages, "current_stage": project.current_stage,
            "can_edit": perms["project.edit"] and not project.is_terminal,
            "can_view_sensitive": perms["project.view_sensitive"],
            "can_change_status": perms["project.edit"] or perms["project.close"] or perms["project.reopen"],
            "history": project.status_history.select_related("changed_by")[:20],
            "status_form": StatusChangeForm(choices=status_choices), "StageStatus": StageStatus,
            "tasks_open": project.tasks.exclude(status=TaskStatus.DONE).count(),
        },
    )


@login_required
def project_status(request, project_id):
    project = get_project_or_404(request.user, project_id)
    if request.method != "POST":
        return redirect("projects:detail", project_id=project.pk)
    form = StatusChangeForm(request.POST, choices=ProjectStatus.choices)
    if form.is_valid():
        try:
            services.change_status(
                project.pk, actor=request.user, to_status=form.cleaned_data["to_status"],
                reason=form.cleaned_data["reason"],
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _errors(exc))
        else:
            messages.success(request, "Status do projeto alterado e registrado.")
    else:
        messages.error(request, "Informe status e justificativa (mínimo de 10 caracteres).")
    return redirect("projects:detail", project_id=project.pk)
