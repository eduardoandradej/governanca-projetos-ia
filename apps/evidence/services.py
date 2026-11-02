"""Serviços de evidências: upload controlado, versões, quarentena, revisão segregada e download seguro."""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.auditlog import services as audit
from apps.lifecycle.services import DomainError, ensure_project_writable
from apps.organizations import rbac

from .models import EvidenceArtifact, EvidenceReview, EvidenceStatus, EvidenceVersion, ReviewDecision, ScanStatus

MAX_UPLOAD_BYTES = getattr(settings, "EVIDENCE_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)

# extensão → (content-type, assinaturas aceitas no início do arquivo)
ALLOWED_TYPES = {
    ".pdf": ("application/pdf", [b"%PDF-"]),
    ".png": ("image/png", [b"\x89PNG\r\n\x1a\n"]),
    ".jpg": ("image/jpeg", [b"\xff\xd8\xff"]),
    ".jpeg": ("image/jpeg", [b"\xff\xd8\xff"]),
    ".txt": ("text/plain", []),  # validado por decodificação UTF-8 sem bytes de controle binários
}
EXECUTABLE_SIGNATURES = [b"MZ", b"\x7fELF", b"#!", b"\xca\xfe\xba\xbe", b"PK\x03\x04"]


def validate_upload(uploaded) -> tuple[str, bytes]:
    """Valida extensão, tamanho e conteúdo (assinatura). Retorna (content_type, bytes)."""
    name = os.path.basename(uploaded.name or "")
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise DomainError("Tipo de arquivo não permitido. Aceitos: PDF, PNG, JPEG e TXT.")
    if uploaded.size > MAX_UPLOAD_BYTES:
        raise DomainError(f"Arquivo excede o limite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    data = uploaded.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise DomainError(f"Arquivo excede o limite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if not data:
        raise DomainError("Arquivo vazio.")
    if any(data.startswith(sig) for sig in EXECUTABLE_SIGNATURES):
        raise DomainError("Conteúdo executável ou compactado não é aceito.")
    content_type, signatures = ALLOWED_TYPES[ext]
    if signatures and not any(data.startswith(sig) for sig in signatures):
        raise DomainError("O conteúdo do arquivo não corresponde à extensão informada.")
    if ext == ".txt":
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise DomainError("Arquivo de texto deve estar em UTF-8.") from None
        if any(ord(c) < 9 or (13 < ord(c) < 32) for c in text):
            raise DomainError("Arquivo de texto contém bytes binários.")
    return content_type, data


def _store(organization_id, data: bytes) -> str:
    storage_name = f"{organization_id}/{uuid.uuid4().hex}.bin"
    path = Path(settings.PRIVATE_MEDIA_ROOT) / storage_name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as fh:
        fh.write(data)
    os.chmod(path, 0o600)
    return storage_name


def private_path(version: EvidenceVersion) -> Path:
    root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    path = (root / version.storage_name).resolve()
    if root not in path.parents:
        raise PermissionDenied("Caminho de arquivo inválido.")
    return path


def _validate_links(project, stage, requirement, task):
    """RN-021: vínculos devem pertencer ao mesmo projeto."""
    if stage is not None and stage.project_id != project.pk:
        raise DomainError("A fase não pertence ao projeto.")
    if requirement is not None and requirement.stage.project_id != project.pk:
        raise DomainError("O requisito não pertence ao projeto.")
    if requirement is not None and stage is not None and requirement.stage_id != stage.pk:
        raise DomainError("O requisito não pertence à fase informada.")
    if task is not None and task.project_id != project.pk:
        raise DomainError("A tarefa não pertence ao projeto.")


def _add_version(artifact, *, actor, uploaded=None, external_reference: str = "", change_note: str = ""):
    if not uploaded and not external_reference.strip():
        raise DomainError("Envie um arquivo ou informe uma referência externa.")
    fields = {"external_reference": external_reference.strip()[:500], "scan_status": ScanStatus.NOT_APPLICABLE}
    if uploaded:
        content_type, data = validate_upload(uploaded)
        fields.update(
            storage_name=_store(artifact.organization_id, data), original_name=os.path.basename(uploaded.name)[:200],
            content_type=content_type, size=len(data), sha256=hashlib.sha256(data).hexdigest(),
            scan_status=ScanStatus.QUARANTINED,
        )
    artifact.current_version += 1
    version = EvidenceVersion.objects.create(
        artifact=artifact, number=artifact.current_version, uploaded_by=actor, change_note=change_note[:255], **fields
    )
    return version


@audit.atomic_service
def create_evidence(*, actor, project, kind: str, title: str, uploaded=None, external_reference: str = "",
                    stage=None, requirement=None, task=None, **extra) -> EvidenceArtifact:
    rbac.require_perm(actor, "evidence.upload", project.organization, project, entity=project)
    ensure_project_writable(project)
    _validate_links(project, stage, requirement, task)
    if requirement is not None and stage is None:
        stage = requirement.stage
    artifact = EvidenceArtifact.objects.create(
        organization=project.organization, project=project, stage=stage, requirement=requirement, task=task,
        kind=kind, title=title.strip(), responsible=actor, created_by=actor, **extra,
    )
    version = _add_version(artifact, actor=actor, uploaded=uploaded, external_reference=external_reference)
    artifact.save(update_fields=["current_version", "updated_at"])
    audit.record(
        "evidence.upload", actor=actor, organization_id=project.organization_id, project_id=project.pk, entity=artifact,
        entity_version=version.number,
        after={"title": artifact.title, "kind": kind, "sha256": version.sha256, "size": version.size,
               "requirement": requirement.code if requirement else None},
    )
    return artifact


def _lock(artifact_id) -> EvidenceArtifact:
    return EvidenceArtifact.objects.select_for_update().select_related("project__organization").get(pk=artifact_id)


@audit.atomic_service
def add_version(artifact_id, *, actor, uploaded=None, external_reference: str = "", change_note: str = ""):
    """Substituição = nova versão (RN-019). Se a evidência estava aprovada, volta à revisão e o gate é revalidado."""
    artifact = _lock(artifact_id)
    project = artifact.project
    rbac.require_perm(actor, "evidence.upload", project.organization, project, entity=artifact)
    ensure_project_writable(project)
    if artifact.status == EvidenceStatus.ARCHIVED:
        raise DomainError("Evidência arquivada não recebe novas versões.")
    was_approved = artifact.status == EvidenceStatus.APPROVED
    version = _add_version(
        artifact, actor=actor, uploaded=uploaded, external_reference=external_reference, change_note=change_note
    )
    artifact.status = EvidenceStatus.IN_REVIEW
    artifact.save(update_fields=["current_version", "status", "updated_at"])
    audit.record(
        "evidence.new_version", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=artifact, entity_version=version.number,
        before={"status": "approved" if was_approved else "in_review"},
        after={"status": artifact.status, "sha256": version.sha256}, reason=change_note,
    )
    if was_approved and artifact.stage_id:
        from apps.governance.services import flag_revalidation

        flag_revalidation(artifact.stage, actor=actor, cause=f"Evidência '{artifact.title}' alterada após aprovação")
    return version


@audit.atomic_service
def inspect_version(artifact_id, *, actor, release: bool, note: str = "") -> EvidenceVersion:
    """Inspeção manual de quarentena (estratégia na ausência de antivírus no ambiente)."""
    artifact = _lock(artifact_id)
    project = artifact.project
    rbac.require_perm(actor, "evidence.inspect", project.organization, project, entity=artifact)
    version = artifact.latest
    if version.scan_status != ScanStatus.QUARANTINED:
        raise DomainError("A versão atual não está em quarentena.")
    version.scan_status = ScanStatus.RELEASED if release else ScanStatus.BLOCKED
    version.inspected_by = actor
    version.inspected_at = timezone.now()
    version.save(update_fields=["scan_status", "inspected_by", "inspected_at"])
    audit.record(
        "evidence.inspect", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=artifact, entity_version=version.number, after={"scan_status": version.scan_status}, reason=note,
    )
    return version


@audit.atomic_service
def review_evidence(artifact_id, *, actor, decision: str, comment: str) -> EvidenceArtifact:
    artifact = _lock(artifact_id)
    project = artifact.project
    rbac.require_perm(actor, "evidence.review", project.organization, project, entity=artifact)
    ensure_project_writable(project)
    if decision not in ReviewDecision.values:
        raise DomainError("Decisão inválida.")
    if artifact.status != EvidenceStatus.IN_REVIEW:
        raise DomainError("Somente evidências em revisão podem receber parecer.")
    version = artifact.latest
    if version.uploaded_by_id == actor.pk:
        raise PermissionDenied("Quem enviou a versão não pode revisá-la (segregação de funções).")
    if decision == ReviewDecision.APPROVED and version.scan_status in (ScanStatus.QUARANTINED, ScanStatus.BLOCKED):
        raise DomainError("Arquivo em quarentena ou bloqueado não pode ser aprovado.")
    comment = (comment or "").strip()
    if not comment:
        raise DomainError("O parecer é obrigatório.")
    EvidenceReview.objects.create(
        artifact=artifact, version_number=version.number, reviewer=actor, decision=decision, comment=comment
    )
    artifact.status = EvidenceStatus.APPROVED if decision == ReviewDecision.APPROVED else EvidenceStatus.REJECTED
    artifact.save(update_fields=["status", "updated_at"])
    audit.record(
        "evidence.review", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=artifact, entity_version=version.number, after={"status": artifact.status}, reason=comment,
    )
    return artifact


@audit.atomic_service
def archive_evidence(artifact_id, *, actor, reason: str) -> EvidenceArtifact:
    """Arquivamento lógico; evidências nunca são excluídas pela aplicação."""
    artifact = _lock(artifact_id)
    project = artifact.project
    rbac.require_perm(actor, "project.edit", project.organization, project, entity=artifact)
    if len((reason or "").strip()) < 10:
        raise DomainError("Justifique o arquivamento (mínimo de 10 caracteres).")
    before = artifact.status
    artifact.status = EvidenceStatus.ARCHIVED
    artifact.archived_at = timezone.now()
    artifact.save(update_fields=["status", "archived_at", "updated_at"])
    audit.record(
        "evidence.archive", actor=actor, organization_id=project.organization_id, project_id=project.pk,
        entity=artifact, before={"status": before}, after={"status": artifact.status}, reason=reason,
    )
    if before == EvidenceStatus.APPROVED and artifact.stage_id:
        from apps.governance.services import flag_revalidation

        flag_revalidation(artifact.stage, actor=actor, cause=f"Evidência aprovada '{artifact.title}' arquivada")
    return artifact


def authorize_download(actor, artifact: EvidenceArtifact, version: EvidenceVersion) -> None:
    """RN-017: download só com permissão no escopo e arquivo liberado da quarentena."""
    project = artifact.project
    rbac.require_perm(actor, "evidence.download", project.organization, project, entity=artifact)
    if not version.storage_name:
        raise DomainError("Esta versão é uma referência externa, sem arquivo.")
    if version.scan_status != ScanStatus.RELEASED:
        is_inspector = rbac.has_perm(actor, "evidence.inspect", project.organization, project)
        if not (is_inspector and version.scan_status == ScanStatus.QUARANTINED):
            raise PermissionDenied("Arquivo em quarentena: download bloqueado até a inspeção.")


def requirement_has_approved_evidence(requirement) -> bool:
    """RN-005: evidência válida = aprovada, do tipo exigido (se definido), última versão não bloqueada."""
    qs = EvidenceArtifact.objects.filter(requirement=requirement, status=EvidenceStatus.APPROVED)
    if requirement.evidence_kind:
        qs = qs.filter(kind=requirement.evidence_kind)
    for artifact in qs:
        latest = artifact.latest
        if latest and latest.scan_status in (ScanStatus.RELEASED, ScanStatus.NOT_APPLICABLE):
            return True
    return False
