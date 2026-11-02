"""Evidências: upload controlado, quarentena, revisão segregada, download com escopo (T-015 parcial, T-021, RN-017/019)."""

import hashlib
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.auditlog.models import AuditEvent
from apps.evidence import services as ev
from apps.evidence.models import EvidenceArtifact, ScanStatus
from tests_support.factories import txt_upload

pytestmark = pytest.mark.django_db


def _req(project, code="F1-R1"):
    return project.stages.get(order=1).requirements.get(code=code)


def _files_in_storage():
    root = Path(settings.PRIVATE_MEDIA_ROOT)
    return sorted(p for p in root.rglob("*") if p.is_file())


@pytest.mark.parametrize(
    "name,content,msg",
    [
        ("malware.exe", b"MZ\x90\x00", "não permitido"),
        ("disfarcado.pdf", b"MZ\x90\x00binario", "executável"),
        ("falso.pdf", b"isto nao e pdf", "não corresponde"),
        ("imagem.png", b"%PDF-1.4", "não corresponde"),
        ("texto.txt", b"\x00\x01\x02binario", "binários"),
        ("pacote.pdf", b"PK\x03\x04zip", "executável"),
        ("vazio.txt", b"", "vazio"),
    ],
)
def test_T021_invalid_uploads_are_refused_without_storing(org_a, project_a, name, content, msg):
    before = _files_in_storage()
    with pytest.raises(ValidationError, match=msg):
        ev.create_evidence(actor=org_a.executor, project=project_a, requirement=_req(project_a), kind="business_case",
                           title="x", uploaded=SimpleUploadedFile(name, content))
    assert _files_in_storage() == before
    assert not EvidenceArtifact.objects.exists()


def test_T021_oversized_upload_refused(org_a, project_a, settings, monkeypatch):
    monkeypatch.setattr(ev, "MAX_UPLOAD_BYTES", 100)
    with pytest.raises(ValidationError, match="limite"):
        ev.create_evidence(actor=org_a.executor, project=project_a, kind="other", title="grande",
                           uploaded=txt_upload(content=b"a" * 101))


def test_valid_upload_stored_privately_with_hash(org_a, project_a):
    content = b"%PDF-1.4\n% sintetico\n"
    art = ev.create_evidence(actor=org_a.executor, project=project_a, requirement=_req(project_a),
                             kind="business_case", title="Caso", uploaded=SimpleUploadedFile("caso.pdf", content))
    v = art.latest
    assert v.sha256 == hashlib.sha256(content).hexdigest() and v.content_type == "application/pdf"
    assert v.scan_status == ScanStatus.QUARANTINED
    path = ev.private_path(v)
    assert path.read_bytes() == content
    assert str(settings.BASE_DIR / "static") not in str(path)
    assert oct(path.stat().st_mode)[-3:] == "600"


def test_cross_project_links_rejected(org_a, project_a):
    other = org_a.create_project(code="IA-OUTRO")
    with pytest.raises(ValidationError, match="não pertence"):
        ev.create_evidence(actor=org_a.executor, project=project_a, requirement=_req(other), kind="other",
                           title="x", external_reference="ata-01")


def test_review_segregation_and_quarantine(org_a, project_a):
    art = ev.create_evidence(actor=org_a.manager, project=project_a, kind="plan", title="Plano",
                             uploaded=txt_upload())
    with pytest.raises(PermissionDenied, match="segregação"):
        ev.review_evidence(art.pk, actor=org_a.manager, decision="approved", comment="auto")
    with pytest.raises(ValidationError, match="quarentena"):
        ev.review_evidence(art.pk, actor=org_a.approver, decision="approved", comment="ok")
    with pytest.raises(PermissionDenied):
        ev.inspect_version(art.pk, actor=org_a.manager, release=True)
    ev.inspect_version(art.pk, actor=org_a.security, release=True, note="ok")
    assert ev.review_evidence(art.pk, actor=org_a.approver, decision="approved", comment="ok").status == "approved"


def test_new_version_keeps_history(org_a, project_a):
    art = ev.create_evidence(actor=org_a.executor, project=project_a, kind="plan", title="Plano",
                             external_reference="wiki/plano-v1")
    ev.add_version(art.pk, actor=org_a.executor, external_reference="wiki/plano-v2", change_note="revisão")
    art.refresh_from_db()
    assert art.current_version == 2
    assert list(art.versions.order_by("number").values_list("external_reference", flat=True)) == [
        "wiki/plano-v1", "wiki/plano-v2"]


def test_download_scope_quarantine_and_audit(client, org_a, org_b, project_a):
    art = ev.create_evidence(actor=org_a.executor, project=project_a, kind="plan", title="Plano",
                             uploaded=txt_upload(content=b"conteudo sintetico\n"))
    url = reverse("evidence:download", args=[art.pk, 1])
    client.force_login(org_a.manager)
    assert client.get(url).status_code == 403  # em quarentena
    ev.inspect_version(art.pk, actor=org_a.security, release=True)
    resp = client.get(url)
    assert resp.status_code == 200 and b"".join(resp.streaming_content) == b"conteudo sintetico\n"
    assert "attachment" in resp["Content-Disposition"]
    assert AuditEvent.objects.filter(action="evidence.download", actor=org_a.manager).count() == 1
    client.force_login(org_a.reader)
    assert client.get(url).status_code == 403  # leitor não baixa
    client.force_login(org_b.admin)
    assert client.get(url).status_code == 404  # T-015: outra organização
    assert client.get(reverse("evidence:detail", args=[art.pk])).status_code == 404


def test_archive_is_logical_and_approved_cannot_be_deleted(org_a, project_a):
    art = ev.create_evidence(actor=org_a.executor, project=project_a, kind="plan", title="Plano",
                             external_reference="ata")
    with pytest.raises(ValidationError):
        ev.archive_evidence(art.pk, actor=org_a.manager, reason="curto")
    ev.archive_evidence(art.pk, actor=org_a.manager, reason="Substituída por documento consolidado")
    assert EvidenceArtifact.objects.filter(pk=art.pk, status="archived").exists()


def test_upload_via_web_form(client, org_a, project_a):
    stage = project_a.stages.get(order=1)
    client.force_login(org_a.executor)
    resp = client.post(reverse("evidence:create", args=[project_a.pk]), {
        "stage": stage.pk, "title": "Caso de negócio v1", "kind": "business_case",
        "requirement": _req(project_a).pk, "classification": "internal",
        "file": SimpleUploadedFile("caso.txt", b"Caso de negocio sintetico\n"),
    })
    assert resp.status_code == 302
    art = EvidenceArtifact.objects.get(title="Caso de negócio v1")
    assert art.requirement.code == "F1-R1" and art.latest.scan_status == ScanStatus.QUARANTINED
    detail = client.get(reverse("evidence:detail", args=[art.pk])).content.decode()
    assert "Em quarentena" in detail and "/var/" not in detail and art.latest.storage_name not in detail
