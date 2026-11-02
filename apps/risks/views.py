from datetime import date
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.forms import BootstrapMixin
from apps.core.http import get_project_or_404
from apps.organizations import rbac
from apps.projects.models import Project

from . import services
from .models import (
    AIRiskCategory,
    CostCategory,
    CostKind,
    DecisionRecord,
    DecisionTopic,
    Risk,
    RiskCategory,
    RiskLevel,
    RiskStatus,
    TreatmentStrategy,
)


def _errors(exc) -> str:
    return " ".join(getattr(exc, "messages", [str(exc)]))


def project_people(project):
    return (
        get_user_model().objects.filter(
            Q(role_assignments__organization=project.organization, role_assignments__project__isnull=True)
            | Q(role_assignments__project=project),
            role_assignments__revoked_at__isnull=True,
        ).distinct().order_by("full_name", "username")
    )


class RiskForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Risk
        fields = ["title", "category", "ai_category", "stage", "probability", "impact", "owner", "description",
                  "cause", "consequence", "review_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}), "cause": forms.Textarea(attrs={"rows": 2}),
            "consequence": forms.Textarea(attrs={"rows": 2}),
            "review_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "probability": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "impact": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].queryset = project_people(project)
        self.fields["stage"].queryset = project.stages.order_by("order")


def _perm(user, perm, project):
    return rbac.has_perm(user, perm, project.organization, project)


@login_required
def risk_overview(request):
    """Visão consolidada: riscos dos projetos visíveis, filtrável, com matriz 5×5."""
    qs = Risk.objects.filter(project__in=Project.objects.filter(rbac.visible_project_filter(request.user)))
    f = {k: request.GET.get(k, "").strip() for k in ("nivel", "categoria", "ia", "status")}
    if f["nivel"] in RiskLevel.values:
        qs = qs.filter(level=f["nivel"])
    if f["categoria"] in RiskCategory.values:
        qs = qs.filter(category=f["categoria"])
    if f["ia"] in AIRiskCategory.values:
        qs = qs.filter(ai_category=f["ia"])
    if f["status"] in RiskStatus.values:
        qs = qs.filter(status=f["status"])
    risks = list(qs.select_related("project", "owner"))
    return render(request, "risks/overview.html", {
        "risks": risks, "matrix": services.risk_matrix(risks), "filters": f, "levels": RiskLevel.choices,
        "categories": RiskCategory.choices, "ai_categories": AIRiskCategory.choices, "statuses": RiskStatus.choices,
    })


@login_required
def project_risks(request, project_id):
    project = get_project_or_404(request.user, project_id)
    can_manage = _perm(request.user, "risk.manage", project) and not project.is_terminal
    form = RiskForm(request.POST or None, project=project) if can_manage else None
    if request.method == "POST":
        rbac.require_perm(request.user, "risk.manage", project.organization, project)
        if form.is_valid():
            data = dict(form.cleaned_data)
            try:
                services.create_risk(actor=request.user, project=project, **data)
            except (ValidationError, PermissionDenied) as exc:
                form.add_error(None, _errors(exc))
            else:
                messages.success(request, "Risco registrado.")
                return redirect("risks:project", project_id=project.pk)
    risks = list(project.risks.select_related("owner", "stage").prefetch_related("treatments"))
    return render(request, "risks/project.html", {
        "project": project, "risks": risks, "matrix": services.risk_matrix(risks), "form": form,
        "untreated": services.untreated_critical_risks(project), "thresholds": services.thresholds_for(project.organization),
    })


def _risk(user, risk_id) -> Risk:
    try:
        risk = Risk.objects.select_related("project__organization", "owner").get(pk=risk_id)
    except (Risk.DoesNotExist, ValidationError):
        raise Http404 from None
    get_project_or_404(user, risk.project_id)
    return risk


@login_required
def risk_detail(request, risk_id):
    risk = _risk(request.user, risk_id)
    project = risk.project
    return render(request, "risks/detail.html", {
        "risk": risk, "project": project, "treatments": risk.treatments.select_related("owner"),
        "people": project_people(project), "strategies": TreatmentStrategy.choices,
        "can_manage": _perm(request.user, "risk.manage", project) and not project.is_terminal,
        "can_accept": _perm(request.user, "risk.accept_residual", project),
    })


def _act(request, risk, fn, ok):
    try:
        fn()
    except (ValidationError, PermissionDenied, ValueError) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, ok)
    return redirect("risks:detail", risk_id=risk.pk)


@login_required
@require_POST
def risk_treatment(request, risk_id):
    risk = _risk(request.user, risk_id)
    owner = project_people(risk.project).filter(pk=request.POST.get("owner") or None).first()

    def go():
        if owner is None:
            raise ValidationError("Selecione o responsável.")
        services.add_treatment(risk.pk, actor=request.user, strategy=request.POST.get("strategy", ""),
                               description=request.POST.get("description", ""), owner=owner,
                               due_date=date.fromisoformat(request.POST.get("due_date", "")))

    return _act(request, risk, go, "Tratamento registrado.")


@login_required
@require_POST
def risk_reassess(request, risk_id):
    risk = _risk(request.user, risk_id)
    return _act(request, risk, lambda: services.update_risk_assessment(
        risk.pk, actor=request.user, probability=int(request.POST.get("probability", 0)),
        impact=int(request.POST.get("impact", 0)), reason=request.POST.get("reason", "")), "Risco reavaliado.")


@login_required
@require_POST
def risk_accept(request, risk_id):
    risk = _risk(request.user, risk_id)
    return _act(request, risk, lambda: services.accept_residual(
        risk.pk, actor=request.user, residual_probability=int(request.POST.get("residual_probability", 0)),
        residual_impact=int(request.POST.get("residual_impact", 0)),
        justification=request.POST.get("justification", "")), "Risco residual aceito formalmente.")


class CostForm(BootstrapMixin, forms.Form):
    category = forms.ChoiceField(label="Categoria", choices=CostCategory.choices)
    kind = forms.ChoiceField(label="Tipo", choices=CostKind.choices)
    amount = forms.DecimalField(label="Valor", max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    entry_date = forms.DateField(label="Data de competência", widget=forms.DateInput(attrs={"type": "date"}))
    justification = forms.CharField(label="Justificativa", max_length=255)
    source_document = forms.CharField(label="Fonte documental", max_length=255, required=False)


@login_required
def project_costs(request, project_id):
    project = get_project_or_404(request.user, project_id)
    if not _perm(request.user, "project.view_sensitive", project):
        rbac.require_perm(request.user, "project.view_sensitive", project.organization, project, entity=project)
    can_manage = _perm(request.user, "cost.manage", project) and not project.is_terminal
    form = CostForm(request.POST or None) if can_manage else None
    if request.method == "POST":
        rbac.require_perm(request.user, "cost.manage", project.organization, project)
        if form.is_valid():
            try:
                services.add_cost(actor=request.user, project=project, **form.cleaned_data)
            except (ValidationError, PermissionDenied, InvalidOperation) as exc:
                form.add_error(None, _errors(exc))
            else:
                messages.success(request, "Lançamento registrado.")
                return redirect("risks:costs", project_id=project.pk)
    return render(request, "risks/costs.html", {
        "project": project, "summary": services.cost_summary(project), "form": form,
        "entries": project.cost_entries.select_related("created_by")[:100],
    })


class DecisionForm(BootstrapMixin, forms.Form):
    topic = forms.ChoiceField(label="Tema", choices=DecisionTopic.choices)
    agenda = forms.CharField(label="Pauta", max_length=255)
    alternatives = forms.CharField(label="Alternativas consideradas", widget=forms.Textarea(attrs={"rows": 2}))
    decision = forms.CharField(label="Decisão", widget=forms.Textarea(attrs={"rows": 2}))
    rationale = forms.CharField(label="Motivação", widget=forms.Textarea(attrs={"rows": 2}))
    risks_considered = forms.CharField(label="Riscos considerados", widget=forms.Textarea(attrs={"rows": 2}),
                                       required=False)


@login_required
def project_decisions(request, project_id):
    project = get_project_or_404(request.user, project_id)
    can_record = _perm(request.user, "decision.record", project)
    form = DecisionForm(request.POST or None) if can_record else None
    if request.method == "POST":
        rbac.require_perm(request.user, "decision.record", project.organization, project)
        if form.is_valid():
            try:
                services.propose_decision(actor=request.user, project=project, **form.cleaned_data)
            except (ValidationError, PermissionDenied) as exc:
                form.add_error(None, _errors(exc))
            else:
                messages.success(request, "Decisão registrada como proposta.")
                return redirect("risks:decisions", project_id=project.pk)
    return render(request, "risks/decisions.html", {
        "project": project, "form": form,
        "decisions": project.decisions.select_related("proposed_by", "decided_by", "supersedes"),
        "can_decide": _perm(request.user, "decision.approve", project), "can_record": can_record,
        "actions": project.action_items.select_related("owner", "decision"),
    })


def _decision(user, decision_id) -> DecisionRecord:
    try:
        rec = DecisionRecord.objects.select_related("project").get(pk=decision_id)
    except (DecisionRecord.DoesNotExist, ValidationError):
        raise Http404 from None
    get_project_or_404(user, rec.project_id)
    return rec


@login_required
@require_POST
def decision_decide(request, decision_id):
    rec = _decision(request.user, decision_id)
    try:
        services.decide(rec.pk, actor=request.user, approve=request.POST.get("approve") == "1",
                        note=request.POST.get("note", ""))
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, "Parecer registrado.")
    return redirect("risks:decisions", project_id=rec.project_id)


@login_required
@require_POST
def decision_revise(request, decision_id):
    rec = _decision(request.user, decision_id)
    try:
        services.revise_decision(rec.pk, actor=request.user, decision=request.POST.get("decision", ""),
                                 rationale=request.POST.get("rationale", ""))
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, "Nova versão proposta; a anterior permanece vigente até a aprovação.")
    return redirect("risks:decisions", project_id=rec.project_id)
