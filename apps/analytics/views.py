from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.forms import BootstrapMixin
from apps.core.http import get_project_or_404
from apps.organizations import rbac
from apps.organizations.models import Organization
from apps.risks.views import project_people

from . import metrics, rules, services
from .models import AssetKind, DataAsset, Insight, InsightStatus, LessonLearned, LessonVisibility, MetricSnapshot


def _errors(exc) -> str:
    return " ".join(getattr(exc, "messages", [str(exc)]))


def _org_filter(request):
    org_id = request.GET.get("organizacao") or request.POST.get("organizacao") or None
    orgs = list(rbac.organizations_for(request.user))
    if org_id and org_id not in {str(o.pk) for o in orgs}:
        raise Http404
    return org_id, orgs


@login_required
def home(request):
    org_id, orgs = _org_filter(request)
    ctx = services.portfolio_dashboard(request.user, organization_id=org_id)
    reviewable = [o for o in orgs if rbac.has_perm(request.user, "insight.review", o)]
    ctx.update({
        "organizations": orgs, "selected_org": org_id, "reviewable_orgs": reviewable,
        "open_insights": Insight.objects.filter(
            project__in=services.scoped_projects(request.user, organization_id=org_id),
            status__in=[InsightStatus.PROPOSED, InsightStatus.REVIEWED]).select_related("project")[:10],
    })
    return render(request, "analytics/home.html", ctx)


@login_required
def metric_detail(request, code):
    code = code.upper()
    if code not in metrics.CALCULATORS:
        raise Http404
    org_id, orgs = _org_filter(request)
    projects = services.scoped_projects(request.user, organization_id=org_id)
    result = metrics.compute(code, projects)
    snaps = MetricSnapshot.objects.filter(metric__code=code, organization__in=orgs)
    if org_id:
        snaps = snaps.filter(organization_id=org_id)
    return render(request, "analytics/metric.html", {
        "code": code, "definition": metrics.DEFINITIONS_BY_CODE[code], "result": result,
        "snapshots": snaps.select_related("organization")[:20], "organizations": orgs, "selected_org": org_id,
        "project_count": projects.count(), "has_demo": projects.filter(organization__is_demo=True).exists(),
    })


def _org_for_action(request) -> Organization:
    org_id, orgs = _org_filter(request)
    org = next((o for o in orgs if str(o.pk) == org_id), None)
    if org is None:
        raise Http404
    return org


@login_required
@require_POST
def run_insights(request):
    org = _org_for_action(request)
    try:
        created = services.generate_insights(actor=request.user, organization=org)
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, f"Regras executadas: {len(created)} novo(s) insight(s) proposto(s).")
    return redirect(f"/inteligencia/?organizacao={org.pk}")


@login_required
@require_POST
def capture(request):
    org = _org_for_action(request)
    try:
        n = services.capture_snapshots(actor=request.user, organization=org)
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, f"{n} indicadores registrados em snapshot.")
    return redirect(f"/inteligencia/?organizacao={org.pk}")


@login_required
def insight_list(request):
    projects = services.scoped_projects(request.user)
    qs = Insight.objects.filter(project__in=projects).select_related("project", "reviewed_by", "approved_by")
    status = request.GET.get("status", "")
    if status in InsightStatus.values:
        qs = qs.filter(status=status)
    return render(request, "analytics/insights.html", {"insights": qs[:200], "statuses": InsightStatus.choices,
                                                       "status": status, "rules": rules.RULES})


def _insight(user, insight_id) -> Insight:
    try:
        ins = Insight.objects.select_related("project", "organization").get(pk=insight_id)
    except (Insight.DoesNotExist, ValidationError):
        raise Http404 from None
    get_project_or_404(user, ins.project_id)
    return ins


@login_required
def insight_detail(request, insight_id):
    ins = _insight(request.user, insight_id)
    p = ins.project
    return render(request, "analytics/insight.html", {
        "ins": ins, "rule": rules.RULES.get(ins.rule_code, {}), "reviews": ins.reviews.select_related("reviewer"),
        "can_review": rbac.has_perm(request.user, "insight.review", p.organization, p),
        "can_approve": rbac.has_perm(request.user, "lesson.approve", p.organization, p),
        "can_lesson": rbac.has_perm(request.user, "lesson.manage", p.organization, p),
        "people": project_people(p), "lessons": ins.lessons.all(),
    })


@login_required
@require_POST
def insight_action(request, insight_id, action):
    ins = _insight(request.user, insight_id)
    note = request.POST.get("note", "")
    try:
        if action == "revisar":
            services.review_insight(ins.pk, actor=request.user, note=note)
        elif action == "aprovar":
            owner = project_people(ins.project).filter(pk=request.POST.get("action_owner") or None).first()
            due = request.POST.get("action_due") or None
            services.approve_insight(ins.pk, actor=request.user, note=note,
                                     action_title=request.POST.get("action_title", "").strip() if owner else "",
                                     action_owner=owner, action_due=date.fromisoformat(due) if due else None)
        elif action == "descartar":
            services.discard_insight(ins.pk, actor=request.user, note=note)
        elif action == "licao":
            services.create_lesson(
                actor=request.user, project=ins.project, source_insight=ins, title=request.POST.get("title", ""),
                context=ins.message, lesson=request.POST.get("lesson", ""),
                recommendation=request.POST.get("recommendation", ""),
                stage_order=ins.supporting_data.get("stage_order"),
            )
        else:
            raise Http404
    except (ValidationError, PermissionDenied, ValueError) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, "Registro efetuado e auditado.")
    return redirect("analytics:insight", insight_id=ins.pk)


@login_required
def lesson_list(request):
    qs = services.visible_lessons(request.user).select_related("project", "organization", "approved_by")
    f = {k: request.GET.get(k, "").strip() for k in ("q", "tipo", "etapa", "risco", "status")}
    if f["q"]:
        from django.db.models import Q

        qs = qs.filter(Q(title__icontains=f["q"]) | Q(lesson__icontains=f["q"]) | Q(recommendation__icontains=f["q"]))
    if f["tipo"]:
        qs = qs.filter(platform_type=f["tipo"])
    if f["etapa"].isdigit():
        qs = qs.filter(stage_order=int(f["etapa"]))
    if f["risco"]:
        qs = qs.filter(risk_category=f["risco"])
    if f["status"]:
        qs = qs.filter(status=f["status"])
    from apps.projects.models import PlatformType
    from apps.risks.models import RiskCategory

    return render(request, "analytics/lessons.html", {
        "lessons": qs[:200], "filters": f, "platforms": PlatformType.choices, "risks": RiskCategory.choices,
    })


@login_required
@require_POST
def lesson_approve(request, lesson_id):
    try:
        lesson = LessonLearned.objects.select_related("project").get(pk=lesson_id)
    except (LessonLearned.DoesNotExist, ValidationError):
        raise Http404 from None
    get_project_or_404(request.user, lesson.project_id)
    try:
        services.approve_lesson(lesson.pk, actor=request.user, visibility=request.POST.get("visibility", "project"),
                                disclosure_justification=request.POST.get("disclosure_justification", ""))
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, "Lição aprovada.")
    return redirect("analytics:lessons")


class AssetForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = DataAsset
        fields = ["name", "kind", "owner", "purpose", "description", "source_system", "classification", "locator",
                  "current_version", "source_updated_at", "declared_quality", "retention", "usage_restriction",
                  "contains_personal_data"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2}),
                   "source_updated_at": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].queryset = project_people(project)


@login_required
def project_data(request, project_id):
    project = get_project_or_404(request.user, project_id)
    can_manage = rbac.has_perm(request.user, "data.manage", project.organization, project) and not project.is_terminal
    form = AssetForm(request.POST or None, project=project) if can_manage else None
    if request.method == "POST" and request.POST.get("form") == "asset":
        rbac.require_perm(request.user, "data.manage", project.organization, project)
        if form.is_valid():
            try:
                services.create_asset(actor=request.user, project=project, **form.cleaned_data)
            except (ValidationError, PermissionDenied) as exc:
                form.add_error(None, _errors(exc))
            else:
                messages.success(request, "Ativo catalogado.")
                return redirect("analytics:project_data", project_id=project.pk)
    if request.method == "POST" and request.POST.get("form") == "lineage":
        assets = {str(a.pk): a for a in DataAsset.objects.filter(organization=project.organization)}
        src, tgt = assets.get(request.POST.get("source")), assets.get(request.POST.get("target"))
        try:
            if not src or not tgt or tgt.project_id != project.pk:
                raise ValidationError("Selecione origem e saída válidas (a saída deve ser deste projeto).")
            services.add_lineage(actor=request.user, source=src, target=tgt,
                                 transformation=request.POST.get("transformation", ""))
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _errors(exc))
        else:
            messages.success(request, "Linhagem registrada.")
        return redirect("analytics:project_data", project_id=project.pk)
    assets = project.data_assets.select_related("owner").prefetch_related("upstream__source", "downstream__target")
    from apps.analytics.models import DataLineage

    return render(request, "analytics/project_data.html", {
        "project": project, "assets": assets, "form": form, "can_manage": can_manage, "kinds": AssetKind.choices,
        "edges": DataLineage.objects.filter(target__project=project).select_related("source", "target"),
        "lineage_sources": DataAsset.objects.filter(project__in=services.scoped_projects(
            request.user, organization_id=project.organization_id)),
    })


@login_required
def project_knowledge(request, project_id):
    project = get_project_or_404(request.user, project_id)
    return render(request, "analytics/project_knowledge.html", {
        "project": project, "insights": project.insights.all()[:50], "lessons": project.lessons.all(),
        "can_approve": rbac.has_perm(request.user, "lesson.approve", project.organization, project),
        "visibilities": LessonVisibility.choices,
    })
