from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.http import get_project_or_404
from apps.lifecycle.models import RequirementInstance, StageInstance
from apps.organizations import rbac
from apps.organizations.models import RoleAssignment

from . import services
from .models import ControlMapping, Gate, GateException, GateStatus, GovernanceObjective


def _errors(exc) -> str:
    return " ".join(getattr(exc, "messages", [str(exc)]))


def _stage(user, project_id, stage_id) -> StageInstance:
    project = get_project_or_404(user, project_id)
    try:
        return StageInstance.objects.select_related("project__organization").get(pk=stage_id, project=project)
    except (StageInstance.DoesNotExist, ValidationError):
        raise Http404 from None


def gate_context(request, stage) -> dict:
    """Contexto do painel de gate exibido na página da fase."""
    from apps.evidence.views import evidence_panel_context

    gate = services.get_or_create_gate(stage) if stage.has_exit_gate else None
    evaluation = services.evaluate(stage)
    project = stage.project
    ctx = {
        "gate_template": "governance/_gate_panel.html",
        "gate": gate,
        "evaluation": evaluation,
        "decisions": gate.decisions.select_related("decided_by") if gate else [],
        "exceptions": stage.exceptions.select_related("requirement", "granted_by", "security_ack_by"),
        "exception_requirements": stage.requirements.filter(is_legal=False, mandatory=True),
        "today": date.today(),
        "can_ack": rbac.has_perm(request.user, "gate.exception.security_ack", project.organization, project),
        "can_request": rbac.has_perm(request.user, "gate.request", project.organization, project)
        and not project.is_terminal,
        "can_decide": rbac.has_perm(request.user, "gate.approve", project.organization, project)
        and not project.is_terminal,
        "can_grant_exception": rbac.has_perm(request.user, "gate.exception.grant", project.organization, project)
        and not project.is_terminal,
    }
    ctx.update(evidence_panel_context(request, stage))
    return ctx


def _redirect(stage):
    return redirect("lifecycle:stage", project_id=stage.project_id, stage_id=stage.pk)


def _run(request, stage, fn, ok_message):
    try:
        fn()
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, ok_message)
    return _redirect(stage)


def _request_number(request) -> int:
    try:
        return int(request.POST.get("request_number", "0"))
    except ValueError:
        return 0


@login_required
@require_POST
def gate_request(request, project_id, stage_id):
    stage = _stage(request.user, project_id, stage_id)
    return _run(request, stage, lambda: services.request_gate(stage.pk, actor=request.user,
                                                              note=request.POST.get("note", "")),
                "Passagem solicitada; aguardando aprovador habilitado.")


@login_required
@require_POST
def gate_approve(request, project_id, stage_id):
    stage = _stage(request.user, project_id, stage_id)
    return _run(request, stage, lambda: services.approve_gate(
        stage.pk, actor=request.user, justification=request.POST.get("justification", ""),
        request_number=_request_number(request)), "Gate aprovado; a próxima fase foi iniciada.")


@login_required
@require_POST
def gate_reject(request, project_id, stage_id):
    stage = _stage(request.user, project_id, stage_id)
    return _run(request, stage, lambda: services.reject_gate(
        stage.pk, actor=request.user, justification=request.POST.get("justification", ""),
        request_number=_request_number(request)), "Gate rejeitado; fase devolvida ao responsável.")


@login_required
@require_POST
def gate_cancel(request, project_id, stage_id):
    stage = _stage(request.user, project_id, stage_id)
    return _run(request, stage, lambda: services.cancel_request(stage.pk, actor=request.user,
                                                                reason=request.POST.get("reason", "")),
                "Solicitação cancelada.")


@login_required
@require_POST
def gate_revalidate(request, project_id, stage_id):
    stage = _stage(request.user, project_id, stage_id)
    return _run(request, stage, lambda: services.revalidate_gate(
        stage.pk, actor=request.user, justification=request.POST.get("justification", "")), "Gate revalidado.")


@login_required
@require_POST
def exception_create(request, project_id, stage_id):
    stage = _stage(request.user, project_id, stage_id)
    req = None
    if request.POST.get("requirement"):
        req = RequirementInstance.objects.filter(pk=request.POST["requirement"], stage=stage).first()
        if req is None:
            raise Http404

    def go():
        try:
            valid_until = date.fromisoformat(request.POST.get("valid_until", ""))
        except ValueError:
            raise ValidationError("Data de validade inválida.") from None
        services.grant_exception(
            stage.pk, actor=request.user, justification=request.POST.get("justification", ""),
            residual_risk=request.POST.get("residual_risk", ""), valid_until=valid_until, requirement=req,
            covers_critical_risks=request.POST.get("covers_critical_risks") == "on",
        )

    return _run(request, stage, go, "Exceção formal registrada (visível no gate e na auditoria).")


def _exception(user, exception_id) -> GateException:
    try:
        exc = GateException.objects.select_related("stage__project").get(pk=exception_id)
    except (GateException.DoesNotExist, ValidationError):
        raise Http404 from None
    get_project_or_404(user, exc.stage.project_id)
    return exc


@login_required
@require_POST
def exception_ack(request, exception_id):
    exc = _exception(request.user, exception_id)
    return _run(request, exc.stage, lambda: services.acknowledge_exception(exc.pk, actor=request.user),
                "Ciência de segurança registrada; exceção ativa.")


@login_required
@require_POST
def exception_revoke(request, exception_id):
    exc = _exception(request.user, exception_id)
    return _run(request, exc.stage, lambda: services.revoke_exception(
        exc.pk, actor=request.user, reason=request.POST.get("reason", "")), "Exceção revogada (histórico mantido).")


@login_required
def approval_queue(request):
    """Fila do aprovador: solicitações pendentes e revalidações nos projetos em que o usuário pode aprovar."""
    roles = rbac.PERMISSIONS["gate.approve"]
    assignments = RoleAssignment.objects.filter(
        user=request.user, role__in=roles, revoked_at__isnull=True,
        organization__memberships__user=request.user, organization__memberships__status="active",
    )
    org_ids = assignments.filter(project__isnull=True).values("organization_id")
    project_ids = assignments.filter(project__isnull=False).values("project_id")
    from django.db.models import Q

    scope = Q(stage__project__organization_id__in=org_ids) | Q(stage__project_id__in=project_ids)
    gates = (
        Gate.objects.filter(scope)
        .filter(Q(status=GateStatus.REQUESTED) | Q(revalidation_required=True))
        .select_related("stage__project__organization", "requested_by")
        .order_by("requested_at")
    )
    return render(request, "governance/queue.html", {"gates": gates})


@login_required
def framework(request):
    objectives = GovernanceObjective.objects.prefetch_related(
        Prefetch(
            "mappings",
            queryset=ControlMapping.objects.select_related(
                "requirement_template__stage_template__template_version"
            ).filter(
                ~Q_retired()
            ),
        )
    )
    return render(request, "governance/framework.html", {"objectives": objectives})


def Q_retired():  # noqa: N802 - helper de filtro
    from django.db.models import Q

    return Q(requirement_template__stage_template__template_version__status="retired")
