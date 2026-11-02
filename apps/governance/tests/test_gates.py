"""Stage-Gates: bloqueios, segregação, aprovação única, rejeição, revalidação e exceções (T-004..T-011, T-024, T-025)."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.auditlog.models import AuditEvent
from apps.evidence import services as ev
from apps.governance import services as gov
from apps.governance.models import ExceptionStatus, GateDecision, GateStatus
from apps.lifecycle import services as lc
from apps.lifecycle.models import StageStatus
from apps.organizations.models import Role
from apps.organizations.services import bootstrap_role
from tests_support.factories import approved_evidence, complete_stage_requirements, pass_gate, txt_upload

pytestmark = pytest.mark.django_db


def s(project, order):
    return project.stages.get(order=order)


def test_T004_gate_blocked_with_pending_mandatory_requirement(org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage, skip=("F1-R3",))
    with pytest.raises(ValidationError, match="F1-R3"):
        gov.request_gate(stage.pk, actor=org_a.manager)
    stage.refresh_from_db()
    assert stage.status == StageStatus.IN_PROGRESS
    assert AuditEvent.objects.filter(action="gate.request", result="denied", project_id=project_a.pk).exists()


def test_T005_evidence_in_review_or_rejected_does_not_satisfy(org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage, skip=("F1-R1",))
    req = stage.requirements.get(code="F1-R1")
    lc.fulfill_requirement(req.pk, actor=org_a.manager, note="Caso de negócio redigido.")
    lc.validate_requirement(req.pk, actor=org_a.security, decision="approved", comment="ok")
    art = ev.create_evidence(actor=org_a.executor, project=project_a, requirement=req, kind="business_case",
                             title="Caso de negócio", uploaded=txt_upload())
    with pytest.raises(ValidationError, match="falta evidência aprovada"):
        gov.request_gate(stage.pk, actor=org_a.manager)  # em revisão
    ev.inspect_version(art.pk, actor=org_a.security, release=True)
    ev.review_evidence(art.pk, actor=org_a.approver, decision="rejected", comment="Sem análise de custos.")
    with pytest.raises(ValidationError, match="falta evidência aprovada"):
        gov.request_gate(stage.pk, actor=org_a.manager)  # rejeitada
    ev.add_version(art.pk, actor=org_a.executor, uploaded=txt_upload(content=b"v2 com custos\n"), change_note="v2")
    ev.inspect_version(art.pk, actor=org_a.security, release=True)
    ev.review_evidence(art.pk, actor=org_a.approver, decision="approved", comment="Completo.")
    assert gov.request_gate(stage.pk, actor=org_a.manager).status == GateStatus.REQUESTED


def test_T006_requester_cannot_approve_own_gate(org_a, project_a):
    stage = s(project_a, 1)
    bootstrap_role(organization=org_a.org, user=org_a.manager, role=Role.GATE_APPROVER)  # acumula papéis
    complete_stage_requirements(org_a, stage)
    gate = gov.request_gate(stage.pk, actor=org_a.manager)
    with pytest.raises(PermissionDenied, match="segregação"):
        gov.approve_gate(stage.pk, actor=org_a.manager, justification="Autoaprovação indevida", request_number=1)
    gate.refresh_from_db()
    assert gate.status == GateStatus.REQUESTED and not GateDecision.objects.filter(gate=gate).exists()
    assert AuditEvent.objects.filter(action="gate.approve", result="denied", actor=org_a.manager).exists()


def test_T007_approval_moves_phase_exactly_once(org_a, project_a):
    stage = s(project_a, 1)
    gate = pass_gate(org_a, stage)
    stage.refresh_from_db()
    assert gate.status == GateStatus.APPROVED and stage.status == StageStatus.APPROVED
    assert s(project_a, 2).status == StageStatus.IN_PROGRESS
    with pytest.raises(ValidationError, match="já foi decidida"):
        gov.approve_gate(stage.pk, actor=org_a.sponsor, justification="Segunda aprovação", request_number=1)
    assert GateDecision.objects.filter(gate=gate, decision="approved").count() == 1
    assert AuditEvent.objects.filter(action="gate.approve", result="success", entity_id=str(gate.pk)).count() == 1
    decision = GateDecision.objects.get(gate=gate)
    assert decision.decided_by == org_a.approver and decision.justification
    assert {r["code"] for r in decision.requirements_snapshot} >= {"F1-R1", "F1-R5"}


def test_approver_without_permission_cannot_approve(org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage)
    gov.request_gate(stage.pk, actor=org_a.manager)
    for user in (org_a.executor, org_a.reader, org_a.admin):
        with pytest.raises(PermissionDenied):
            gov.approve_gate(stage.pk, actor=user, justification="Sem papel de aprovador", request_number=1)


def test_T008_rejection_returns_stage_with_justification(org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage)
    gov.request_gate(stage.pk, actor=org_a.manager)
    with pytest.raises(ValidationError, match="obrigatória"):
        gov.reject_gate(stage.pk, actor=org_a.approver, justification="", request_number=1)
    gov.reject_gate(stage.pk, actor=org_a.approver, justification="Detalhar benefícios esperados.", request_number=1)
    stage.refresh_from_db()
    assert stage.status == StageStatus.RETURNED
    assert GateDecision.objects.get(decision="rejected").justification == "Detalhar benefícios esperados."
    gate = gov.request_gate(stage.pk, actor=org_a.manager)
    assert gate.request_number == 2  # nova solicitação, histórico preservado


def test_T025_resubmitting_request_does_not_duplicate(org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage)
    g1 = gov.request_gate(stage.pk, actor=org_a.manager)
    g2 = gov.request_gate(stage.pk, actor=org_a.manager)
    assert g1.request_number == g2.request_number == 1
    assert AuditEvent.objects.filter(action="gate.request", result="success").count() == 1


def test_sequential_progression_enforced(org_a, project_a):
    with pytest.raises(ValidationError, match="Não é possível solicitar"):
        gov.request_gate(s(project_a, 3).pk, actor=org_a.manager)


def test_T009_change_after_approval_requires_revalidation(org_a, project_a):
    stage1 = s(project_a, 1)
    pass_gate(org_a, stage1)
    art = stage1.requirements.get(code="F1-R1").evidences.get()
    ev.add_version(art.pk, actor=org_a.executor, uploaded=txt_upload(content=b"alterado\n"), change_note="Ajuste")
    gate1 = stage1.gate
    gate1.refresh_from_db()
    assert gate1.revalidation_required and gate1.status == GateStatus.APPROVED
    stage2 = s(project_a, 2)
    complete_stage_requirements(org_a, stage2)
    with pytest.raises(ValidationError, match="revalidação"):
        gov.request_gate(stage2.pk, actor=org_a.manager)
    with pytest.raises(ValidationError, match="Revalidação bloqueada"):  # evidência nova ainda em revisão
        gov.revalidate_gate(stage1.pk, actor=org_a.approver, justification="Revisão da mudança")
    ev.inspect_version(art.pk, actor=org_a.security, release=True)
    ev.review_evidence(art.pk, actor=org_a.approver, decision="approved", comment="Mudança aceita")
    gov.revalidate_gate(stage1.pk, actor=org_a.approver, justification="Mudança analisada e aceita")
    assert gov.request_gate(stage2.pk, actor=org_a.manager).status == GateStatus.REQUESTED
    assert GateDecision.objects.filter(gate=gate1, decision="revalidated").count() == 1


def test_requirement_change_after_approval_flags_revalidation(org_a, project_a):
    stage1 = s(project_a, 1)
    pass_gate(org_a, stage1)
    req = stage1.requirements.get(code="F1-R3")
    lc.fulfill_requirement(req.pk, actor=org_a.manager, note="Indicadores-alvo revisados após aprovação.")
    stage1.gate.refresh_from_db()
    assert stage1.gate.revalidation_required


def test_T011_exception_rules_and_history(org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage, skip=("F1-R4",))
    req = stage.requirements.get(code="F1-R4")
    until = timezone.localdate() + timedelta(days=30)
    with pytest.raises(PermissionDenied):
        gov.grant_exception(stage.pk, actor=org_a.manager, requirement=req, valid_until=until,
                              justification="Classificação depende de inventário em andamento",
                              residual_risk="Baixo impacto, monitorado")
    with pytest.raises(ValidationError, match="validade"):
        gov.grant_exception(stage.pk, actor=org_a.sponsor, requirement=req, valid_until=timezone.localdate(),
                              justification="Classificação depende de inventário em andamento",
                              residual_risk="Baixo impacto")
    exc = gov.grant_exception(stage.pk, actor=org_a.sponsor, requirement=req, valid_until=until,
                              justification="Classificação depende de inventário em andamento",
                              residual_risk="Baixo impacto; revisão na fase 2")
    assert exc.status == ExceptionStatus.ACTIVE
    gate = gov.request_gate(stage.pk, actor=org_a.manager)
    gate = gov.approve_gate(stage.pk, actor=org_a.approver, justification="Aprovado com exceção formal",
                            request_number=gate.request_number)
    decision = GateDecision.objects.get(gate=gate, decision="approved")
    assert decision.exceptions_applied[0]["requirement"] == "F1-R4"
    gov.revoke_exception(exc.pk, actor=org_a.sponsor, reason="Inventário concluído")
    exc.refresh_from_db()
    assert exc.status == ExceptionStatus.REVOKED  # revogada, não excluída
    assert AuditEvent.objects.filter(action="gate.exception", entity_id=str(exc.pk)).exists()


def test_exception_never_applies_to_legal_requirement(org_a, project_a):
    pass_gate(org_a, s(project_a, 1))
    stage2 = s(project_a, 2)
    legal = stage2.requirements.get(code="F2-R4")
    assert legal.is_legal
    with pytest.raises(ValidationError, match="legais"):
        gov.grant_exception(stage2.pk, actor=org_a.sponsor, requirement=legal,
                            valid_until=timezone.localdate() + timedelta(days=10),
                            justification="Tentativa de dispensar LGPD por prazo", residual_risk="Alto")
    assert AuditEvent.objects.filter(action="gate.exception", result="denied").exists()


def test_expired_exception_does_not_unblock(org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage, skip=("F1-R4",))
    exc = gov.grant_exception(stage.pk, actor=org_a.sponsor, requirement=stage.requirements.get(code="F1-R4"),
                              valid_until=timezone.localdate() + timedelta(days=5),
                              justification="Classificação depende de inventário em andamento",
                              residual_risk="Baixo impacto, monitorado")
    type(exc).objects.filter(pk=exc.pk).update(valid_until=timezone.localdate() - timedelta(days=1))
    with pytest.raises(ValidationError, match="F1-R4"):
        gov.request_gate(stage.pk, actor=org_a.manager)


def test_confidential_project_exception_requires_security_ack(org_a):
    project = org_a.create_project(code="IA-CONF", data_classification="confidential")
    stage = s(project, 1)
    complete_stage_requirements(org_a, stage, skip=("F1-R4",))
    exc = gov.grant_exception(stage.pk, actor=org_a.sponsor, requirement=stage.requirements.get(code="F1-R4"),
                              valid_until=timezone.localdate() + timedelta(days=5),
                              justification="Classificação depende de inventário em andamento",
                              residual_risk="Médio, com monitoramento")
    assert exc.status == ExceptionStatus.PENDING_SECURITY
    with pytest.raises(ValidationError):
        gov.request_gate(stage.pk, actor=org_a.manager)
    gov.acknowledge_exception(exc.pk, actor=org_a.security)
    assert gov.request_gate(stage.pk, actor=org_a.manager).status == GateStatus.REQUESTED


def test_T024_full_flow_reaches_operation(org_a, project_a):
    for order in range(1, 7):
        pass_gate(org_a, s(project_a, order))
    stages = {st.order: st.status for st in project_a.stages.all()}
    assert all(stages[o] == StageStatus.APPROVED for o in range(1, 7))
    assert stages[7] == StageStatus.IN_PROGRESS  # entrada em operação após aceite (gate da fase 6)
    with pytest.raises(ValidationError, match="acompanhamento contínuo"):
        gov.request_gate(s(project_a, 7).pk, actor=org_a.manager)
    assert GateDecision.objects.filter(gate__stage__project=project_a, decision="approved").count() == 6


def test_gate_web_flow_and_queue(client, org_a, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage)
    client.force_login(org_a.manager)
    client.post(reverse("governance:request", args=[project_a.pk, stage.pk]), {"note": "Pronto"})
    client.force_login(org_a.approver)
    queue = client.get(reverse("governance:queue")).content.decode()
    assert "IA-ALFA-01" in queue
    page = client.get(reverse("lifecycle:stage", args=[project_a.pk, stage.pk])).content.decode()
    assert "Aprovar" in page and "Nenhum bloqueio encontrado" in page
    client.post(reverse("governance:approve", args=[project_a.pk, stage.pk]),
                {"justification": "Aprovado pela interface", "request_number": 1})
    stage.refresh_from_db()
    assert stage.status == StageStatus.APPROVED


def test_direct_post_by_unauthorized_user_is_blocked(client, org_a, org_b, project_a):
    stage = s(project_a, 1)
    complete_stage_requirements(org_a, stage)
    gov.request_gate(stage.pk, actor=org_a.manager)
    client.force_login(org_b.approver)  # aprovador de OUTRA organização
    resp = client.post(reverse("governance:approve", args=[project_a.pk, stage.pk]),
                       {"justification": "Tentativa externa", "request_number": 1})
    assert resp.status_code == 404
    client.force_login(org_a.executor)
    client.post(reverse("governance:approve", args=[project_a.pk, stage.pk]),
                {"justification": "Sem permissão", "request_number": 1})
    stage.refresh_from_db()
    assert stage.status == StageStatus.SUBMITTED


def test_framework_page_lists_isaca_mappings(client, org_a):
    client.force_login(org_a.reader)
    body = client.get(reverse("governance:framework")).content.decode()
    assert "EDM05" in body and "ISACA 2025" in body and "MEA04" in body


def test_approved_evidence_helper_requires_segregated_review(org_a, project_a):
    req = s(project_a, 1).requirements.get(code="F1-R1")
    art = approved_evidence(org_a, req)
    assert art.status == "approved"
