from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.auditlog import services as audit
from apps.core.forms import BootstrapMixin
from apps.core.http import get_project_or_404
from apps.lifecycle.models import EvidenceKind
from apps.organizations import rbac
from apps.projects.models import DataClassification, Project

from . import services
from .models import EvidenceArtifact, EvidenceStatus, ScanStatus


def _errors(exc) -> str:
    return " ".join(getattr(exc, "messages", [str(exc)]))


class EvidenceForm(BootstrapMixin, forms.Form):
    title = forms.CharField(label="Título", max_length=200)
    kind = forms.ChoiceField(label="Tipo", choices=EvidenceKind.choices)
    requirement = forms.ChoiceField(label="Requisito atendido", required=False)
    classification = forms.ChoiceField(label="Classificação", choices=DataClassification.choices, initial="internal")
    origin = forms.CharField(label="Origem", max_length=200, required=False)
    description = forms.CharField(label="Descrição", widget=forms.Textarea(attrs={"rows": 2}), required=False)
    file = forms.FileField(label="Arquivo (PDF, PNG, JPEG, TXT; até 10 MB)", required=False)
    external_reference = forms.CharField(label="ou referência externa (localizador)", max_length=500, required=False)

    def __init__(self, *args, stage=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "—")]
        if stage is not None:
            choices += [(str(r.pk), f"{r.code} {r.title}") for r in stage.requirements.all()]
        self.fields["requirement"].choices = choices
        self.fields["file"].widget.attrs["accept"] = ".pdf,.png,.jpg,.jpeg,.txt"


def evidence_panel_context(request, stage) -> dict:
    project = stage.project
    can_upload = rbac.has_perm(request.user, "evidence.upload", project.organization, project) and not project.is_terminal
    return {
        "stage_evidences": stage.evidences.exclude(status=EvidenceStatus.ARCHIVED).select_related("requirement"),
        "evidence_form": EvidenceForm(stage=stage) if can_upload else None,
    }


@login_required
@require_POST
def evidence_create(request, project_id):
    project = get_project_or_404(request.user, project_id)
    stage = None
    if request.POST.get("stage"):
        stage = project.stages.filter(pk=request.POST["stage"]).first()
        if stage is None:
            raise Http404
    form = EvidenceForm(request.POST, request.FILES, stage=stage)
    target = redirect("lifecycle:stage", project_id=project.pk, stage_id=stage.pk) if stage else redirect(
        "evidence:project", project_id=project.pk)
    if not form.is_valid():
        messages.error(request, "Verifique os campos da evidência.")
        return target
    requirement = None
    if form.cleaned_data["requirement"]:
        requirement = stage.requirements.filter(pk=form.cleaned_data["requirement"]).first() if stage else None
        if requirement is None:
            raise Http404
    try:
        services.create_evidence(
            actor=request.user, project=project, stage=stage, requirement=requirement,
            kind=form.cleaned_data["kind"], title=form.cleaned_data["title"], uploaded=form.cleaned_data["file"],
            external_reference=form.cleaned_data["external_reference"], description=form.cleaned_data["description"],
            origin=form.cleaned_data["origin"], classification=form.cleaned_data["classification"],
        )
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, "Evidência registrada. Arquivos ficam em quarentena até a inspeção.")
    return target


def _artifact(user, artifact_id) -> EvidenceArtifact:
    try:
        artifact = EvidenceArtifact.objects.select_related("project__organization", "stage", "requirement").get(
            pk=artifact_id)
    except (EvidenceArtifact.DoesNotExist, ValidationError):
        raise Http404 from None
    get_project_or_404(user, artifact.project_id)
    return artifact


@login_required
def evidence_detail(request, artifact_id):
    artifact = _artifact(request.user, artifact_id)
    project, user = artifact.project, request.user
    perm = lambda p: rbac.has_perm(user, p, project.organization, project)  # noqa: E731
    latest = artifact.latest
    return render(request, "evidence/detail.html", {
        "artifact": artifact, "project": project, "latest": latest,
        "versions": artifact.versions.select_related("uploaded_by", "inspected_by"),
        "reviews": artifact.reviews.select_related("reviewer"),
        "can_upload": perm("evidence.upload") and artifact.status != EvidenceStatus.ARCHIVED and not project.is_terminal,
        "can_review": perm("evidence.review") and artifact.status == EvidenceStatus.IN_REVIEW,
        "can_inspect": perm("evidence.inspect") and latest and latest.scan_status == ScanStatus.QUARANTINED,
        "can_archive": perm("project.edit") and artifact.status != EvidenceStatus.ARCHIVED,
        "can_download": perm("evidence.download"),
    })


def _act(request, artifact, fn, ok):
    try:
        fn()
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _errors(exc))
    else:
        messages.success(request, ok)
    return redirect("evidence:detail", artifact_id=artifact.pk)


@login_required
@require_POST
def evidence_new_version(request, artifact_id):
    artifact = _artifact(request.user, artifact_id)
    return _act(request, artifact, lambda: services.add_version(
        artifact.pk, actor=request.user, uploaded=request.FILES.get("file"),
        external_reference=request.POST.get("external_reference", ""),
        change_note=request.POST.get("change_note", "")), "Nova versão registrada; evidência volta para revisão.")


@login_required
@require_POST
def evidence_inspect(request, artifact_id):
    artifact = _artifact(request.user, artifact_id)
    release = request.POST.get("release") == "1"
    return _act(request, artifact, lambda: services.inspect_version(
        artifact.pk, actor=request.user, release=release, note=request.POST.get("note", "")),
        "Arquivo liberado após inspeção." if release else "Arquivo bloqueado.")


@login_required
@require_POST
def evidence_review(request, artifact_id):
    artifact = _artifact(request.user, artifact_id)
    return _act(request, artifact, lambda: services.review_evidence(
        artifact.pk, actor=request.user, decision=request.POST.get("decision", ""),
        comment=request.POST.get("comment", "")), "Parecer registrado.")


@login_required
@require_POST
def evidence_archive(request, artifact_id):
    artifact = _artifact(request.user, artifact_id)
    return _act(request, artifact, lambda: services.archive_evidence(
        artifact.pk, actor=request.user, reason=request.POST.get("reason", "")), "Evidência arquivada.")


@login_required
def evidence_download(request, artifact_id, number):
    artifact = _artifact(request.user, artifact_id)
    version = artifact.versions.filter(number=number).first()
    if version is None:
        raise Http404
    try:
        services.authorize_download(request.user, artifact, version)
    except ValidationError as exc:
        messages.error(request, _errors(exc))
        return redirect("evidence:detail", artifact_id=artifact.pk)
    path = services.private_path(version)
    if not path.exists():
        raise Http404("Arquivo indisponível.")
    audit.record("evidence.download", actor=request.user, organization_id=artifact.organization_id,
                 project_id=artifact.project_id, entity=artifact, entity_version=version.number)
    response = FileResponse(open(path, "rb"), as_attachment=True, filename=version.original_name or "evidencia",
                            content_type=version.content_type or "application/octet-stream")
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return response


@login_required
def evidence_list(request, project_id=None):
    qs = EvidenceArtifact.objects.select_related("project", "stage", "requirement", "responsible")
    project = None
    if project_id:
        project = get_project_or_404(request.user, project_id)
        qs = qs.filter(project=project)
    else:
        qs = qs.filter(project__in=Project.objects.filter(rbac.visible_project_filter(request.user)))
    f = {k: request.GET.get(k, "").strip() for k in ("status", "tipo", "q")}
    if f["status"] in EvidenceStatus.values:
        qs = qs.filter(status=f["status"])
    if f["tipo"] in EvidenceKind.values:
        qs = qs.filter(kind=f["tipo"])
    if f["q"]:
        qs = qs.filter(title__icontains=f["q"])
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "evidence/list.html", {
        "page": page, "project": project, "filters": f, "statuses": EvidenceStatus.choices,
        "kinds": EvidenceKind.choices,
    })
