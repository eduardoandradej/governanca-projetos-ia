from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.forms import BootstrapMixin
from apps.core.http import get_project_or_404
from apps.organizations import rbac

from . import services
from .models import RequirementInstance, StageInstance, Task, TaskStatus, Team, ValidationDecision


def _errors(exc) -> str:
    return " ".join(getattr(exc, "messages", [str(exc)]))


def _get_stage(user, project_id, stage_id) -> StageInstance:
    project = get_project_or_404(user, project_id)
    try:
        return StageInstance.objects.select_related("project__organization").get(pk=stage_id, project=project)
    except (StageInstance.DoesNotExist, ValidationError):
        raise Http404 from None


class TaskForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assignee", "team", "due_date", "priority"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        from django.db.models import Q

        self.fields["assignee"].queryset = (
            get_user_model()
            .objects.filter(
                Q(role_assignments__organization=project.organization, role_assignments__project__isnull=True)
                | Q(role_assignments__project=project),
                role_assignments__revoked_at__isnull=True,
            )
            .distinct()
            .order_by("full_name", "username")
        )
        self.fields["team"].queryset = Team.objects.filter(organization=project.organization)


@login_required
def stage_detail(request, project_id, stage_id):
    stage = _get_stage(request.user, project_id, stage_id)
    project, org, user = stage.project, stage.project.organization, request.user
    requirements = stage.requirements.select_related("fulfilled_by").prefetch_related("validations__validator")
    perms = {
        p: rbac.has_perm(user, p, org, project)
        for p in ("requirement.fulfill", "requirement.validate", "task.manage", "stage.start", "gate.request",
                  "gate.approve", "gate.exception.grant")
    }
    context = {
        "project": project, "stage": stage, "requirements": requirements, "perms": perms,
        "progress": services.stage_progress(stage), "tasks": stage.tasks.select_related("assignee", "team"),
        "task_form": TaskForm(project=project) if perms["task.manage"] else None,
        "history": stage.history.select_related("changed_by"), "ValidationDecision": ValidationDecision,
        "can_fulfill": perms["requirement.fulfill"] and not project.is_terminal
        and stage.status in ("in_progress", "returned", "approved"),
        "can_validate": perms["requirement.validate"] and not project.is_terminal,
        "can_resume": perms["stage.start"] and stage.status == "returned" and not project.is_terminal,
    }
    try:
        from apps.governance.views import gate_context

        context.update(gate_context(request, stage))
    except ImportError:
        pass
    return render(request, "lifecycle/stage_detail.html", context)


@login_required
@require_POST
def requirement_fulfill(request, project_id, stage_id, requirement_id):
    stage = _get_stage(request.user, project_id, stage_id)
    if not RequirementInstance.objects.filter(pk=requirement_id, stage=stage).exists():
        raise Http404
    try:
        services.fulfill_requirement(requirement_id, actor=request.user, note=request.POST.get("note", ""))
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, "Atendimento do requisito registrado.")
    return redirect("lifecycle:stage", project_id=project_id, stage_id=stage.pk)


@login_required
@require_POST
def requirement_validate(request, project_id, stage_id, requirement_id):
    stage = _get_stage(request.user, project_id, stage_id)
    if not RequirementInstance.objects.filter(pk=requirement_id, stage=stage).exists():
        raise Http404
    try:
        services.validate_requirement(
            requirement_id, actor=request.user, decision=request.POST.get("decision", ""),
            comment=request.POST.get("comment", ""),
        )
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, "Validação registrada.")
    return redirect("lifecycle:stage", project_id=project_id, stage_id=stage.pk)


@login_required
@require_POST
def stage_resume(request, project_id, stage_id):
    stage = _get_stage(request.user, project_id, stage_id)
    try:
        services.resume_stage(stage.pk, actor=request.user, reason=request.POST.get("reason", ""))
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    return redirect("lifecycle:stage", project_id=project_id, stage_id=stage.pk)


@login_required
@require_POST
def task_create(request, project_id, stage_id):
    stage = _get_stage(request.user, project_id, stage_id)
    form = TaskForm(request.POST, project=stage.project)
    if form.is_valid():
        try:
            services.create_task(actor=request.user, project=stage.project, stage=stage, **form.cleaned_data)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _errors(exc))
        else:
            messages.success(request, "Tarefa criada.")
    else:
        messages.error(request, "Verifique os campos da tarefa: " + "; ".join(
            f"{k}: {', '.join(v)}" for k, v in form.errors.items()))
    return redirect("lifecycle:stage", project_id=project_id, stage_id=stage.pk)


@login_required
def task_board(request, project_id):
    project = get_project_or_404(request.user, project_id)
    tasks = project.tasks.select_related("assignee", "stage", "team")
    stage_filter = request.GET.get("fase", "")
    if stage_filter.isdigit():
        tasks = tasks.filter(stage__order=int(stage_filter))
    columns = [(value, label, [t for t in tasks if t.status == value]) for value, label in TaskStatus.choices]
    view = request.GET.get("visao", "kanban")
    return render(
        request, "lifecycle/task_board.html",
        {"project": project, "columns": columns, "tasks": tasks, "view": view, "statuses": TaskStatus.choices,
         "stages": project.stages.order_by("order"), "stage_filter": stage_filter,
         "can_manage": rbac.has_perm(request.user, "task.manage", project.organization, project)},
    )


@login_required
@require_POST
def task_status(request, project_id, task_id):
    project = get_project_or_404(request.user, project_id)
    if not Task.objects.filter(pk=task_id, project=project).exists():
        raise Http404
    try:
        task = services.update_task_status(task_id, actor=request.user, status=request.POST.get("status", ""))
    except (ValidationError, PermissionDenied) as exc:
        if request.headers.get("HX-Request"):
            return render(request, "partials/alert.html", {"level": "danger", "message": _errors(exc)}, status=422)
        messages.error(request, _errors(exc))
    else:
        if request.headers.get("HX-Request"):
            return render(request, "lifecycle/_task_card.html", {"task": task, "project": project,
                                                                "statuses": TaskStatus.choices, "can_manage": True})
        messages.success(request, "Status da tarefa atualizado.")
    from django.urls import reverse

    view = "lista" if request.POST.get("visao") == "lista" else "kanban"
    return redirect(f"{reverse('lifecycle:tasks', kwargs={'project_id': project.pk})}?visao={view}")
