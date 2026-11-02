"""Serviços de Stage-Gate: solicitação, avaliação de bloqueios, aprovação, rejeição, exceções e revalidação.

Garantias:
- Avanço sequencial (fase N só solicita gate se N-1 estiver aprovada/concluída e sem revalidação pendente).
- Bloqueios avaliados no SERVIDOR na solicitação e novamente na aprovação (RN-004, RN-005, RN-008).
- Segregação solicitante ≠ aprovador (RN-006); parecer com autor, justificativa e snapshot versionado (RN-007).
- Concorrência: `select_for_update` em gate e fase + restrição única de decisão final por solicitação (RN-020).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.utils import timezone

from apps.auditlog import services as audit
from apps.lifecycle.models import RequirementStatus, StageInstance, StageStatus
from apps.lifecycle.services import DomainError, ensure_project_writable, transition_stage
from apps.organizations import rbac
from apps.projects.models import DataClassification

from .models import (
    ExceptionStatus,
    FactorStatus,
    Gate,
    GateDecision,
    GateDecisionType,
    GateException,
    GateStatus,
    ResponsibleAIAssessment,
    ResponsibleAIFactor,
)

MAX_EXCEPTION_DAYS = 180


@dataclass
class GateEvaluation:
    blockers: list[str] = field(default_factory=list)
    exceptions_applied: list[dict] = field(default_factory=list)
    snapshot: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blockers


def get_or_create_gate(stage: StageInstance) -> Gate:
    gate, _ = Gate.objects.get_or_create(stage=stage)
    return gate


def _critical_risks(stage: StageInstance) -> list[str]:
    """Riscos críticos sem tratamento (módulo de riscos, M4). Ausente o módulo, não há bloqueio a avaliar."""
    try:
        from apps.risks.services import untreated_critical_risks
    except ImportError:
        return []
    return [str(r) for r in untreated_critical_risks(stage.project)]


def evaluate(stage: StageInstance, *, ignore_own_revalidation: bool = False) -> GateEvaluation:
    """Avalia todos os bloqueios de passagem da fase. Não altera estado."""
    from apps.evidence.services import requirement_has_approved_evidence

    ev = GateEvaluation()
    today = timezone.localdate()
    exceptions = [e for e in stage.exceptions.all() if e.is_effective(today)]
    req_exceptions = {e.requirement_id: e for e in exceptions if e.requirement_id}
    for req in stage.requirements.all().order_by("order"):
        ev.snapshot.append({"code": req.code, "version": req.version, "status": req.status, "mandatory": req.mandatory})
        if not req.mandatory:
            continue
        problems = []
        if req.status != RequirementStatus.VALIDATED:
            problems.append(f"{req.code}: requisito obrigatório não validado ({req.get_status_display().lower()})")
        if req.requires_evidence and not requirement_has_approved_evidence(req):
            problems.append(f"{req.code}: falta evidência aprovada do tipo '{req.get_evidence_kind_display()}'")
        if problems:
            exc = req_exceptions.get(req.pk)
            if exc and not req.is_legal:
                ev.exceptions_applied.append(
                    {"exception": str(exc.pk), "requirement": req.code, "valid_until": exc.valid_until.isoformat()}
                )
            else:
                ev.blockers.extend(problems)
    if stage.block_on_critical_risk:
        risks = _critical_risks(stage)
        if risks:
            risk_exc = next((e for e in exceptions if e.covers_critical_risks), None)
            if risk_exc:
                ev.exceptions_applied.append(
                    {"exception": str(risk_exc.pk), "critical_risks": risks, "valid_until": risk_exc.valid_until.isoformat()}
                )
            else:
                ev.blockers.extend(f"Risco crítico sem tratamento: {r}" for r in risks)
    if stage.requires_responsible_ai:
        ev.blockers.extend(responsible_ai_blockers(stage.project))
    previous = stage.project.stages.filter(order=stage.order - 1).first()
    if previous is not None:
        if previous.status not in (StageStatus.APPROVED, StageStatus.COMPLETED):
            ev.blockers.append(f"A fase anterior ({previous.order}. {previous.name}) ainda não foi aprovada.")
        prev_gate = Gate.objects.filter(stage=previous).first()
        if prev_gate and prev_gate.revalidation_required:
            ev.blockers.append(f"O gate da fase {previous.order} exige revalidação: {prev_gate.revalidation_cause}")
    gate = Gate.objects.filter(stage=stage).first()
    if gate and gate.revalidation_required and not ignore_own_revalidation:
        ev.blockers.append(f"Este gate exige revalidação: {gate.revalidation_cause}")
    return ev


def _lock(stage_id) -> tuple[StageInstance, Gate]:
    stage = StageInstance.objects.select_for_update().select_related("project__organization").get(pk=stage_id)
    get_or_create_gate(stage)
    gate = Gate.objects.select_for_update().get(stage=stage)
    return stage, gate


def _audit(action, actor, stage, gate, *, result="success", reason="", before=None, after=None):
    audit.record(
        action, actor=actor, result=result, organization_id=stage.project.organization_id,
        project_id=stage.project_id, entity=gate, entity_version=gate.request_number, before=before, after=after,
        reason=reason,
    )


@audit.atomic_service
def request_gate(stage_id, *, actor, note: str = "") -> Gate:
    stage, gate = _lock(stage_id)
    project = stage.project
    rbac.require_perm(actor, "gate.request", project.organization, project, entity=stage)
    ensure_project_writable(project)
    if not stage.has_exit_gate:
        raise DomainError("Esta fase é de acompanhamento contínuo e não possui gate de saída.")
    if gate.status == GateStatus.REQUESTED:
        return gate  # reenvio do formulário não duplica a solicitação (T-025)
    if stage.status not in (StageStatus.IN_PROGRESS, StageStatus.RETURNED):
        raise DomainError(f"Não é possível solicitar o gate com a fase '{stage.get_status_display()}'.")
    ev = evaluate(stage)
    if not ev.ok:
        _audit("gate.request", actor, stage, gate, result="denied", reason="; ".join(ev.blockers)[:2000])
        raise DomainError("Passagem bloqueada: " + " | ".join(ev.blockers))
    gate.status = GateStatus.REQUESTED
    gate.request_number += 1
    gate.requested_by = actor
    gate.requested_at = timezone.now()
    gate.request_note = note
    gate.requirements_snapshot = ev.snapshot
    gate.version += 1
    gate.save()
    transition_stage(stage, StageStatus.SUBMITTED, actor=actor, reason=f"Gate solicitado (solicitação nº {gate.request_number})")
    _audit("gate.request", actor, stage, gate, after={"request_number": gate.request_number,
                                                       "exceptions": ev.exceptions_applied}, reason=note)
    return gate


@audit.atomic_service
def approve_gate(stage_id, *, actor, justification: str, request_number: int) -> Gate:
    stage, gate = _lock(stage_id)
    project = stage.project
    rbac.require_perm(actor, "gate.approve", project.organization, project, entity=stage)
    ensure_project_writable(project)
    if gate.status != GateStatus.REQUESTED or gate.request_number != request_number:
        raise DomainError("Esta solicitação de gate já foi decidida ou não está mais vigente.")
    if stage.requires_segregation and gate.requested_by_id == actor.pk:
        _audit("gate.approve", actor, stage, gate, result="denied", reason="Segregação: solicitante não aprova")
        raise PermissionDenied("Quem solicitou a passagem não pode aprová-la (segregação de funções).")
    justification = (justification or "").strip()
    if len(justification) < 10:
        raise DomainError("A justificativa da aprovação é obrigatória (mínimo de 10 caracteres).")
    ev = evaluate(stage)
    if not ev.ok:
        _audit("gate.approve", actor, stage, gate, result="denied", reason="; ".join(ev.blockers)[:2000])
        raise DomainError("Aprovação bloqueada: " + " | ".join(ev.blockers))
    try:
        GateDecision.objects.create(
            gate=gate, request_number=gate.request_number, decision=GateDecisionType.APPROVED, decided_by=actor,
            justification=justification, requirements_snapshot=ev.snapshot, exceptions_applied=ev.exceptions_applied,
        )
    except IntegrityError as exc:  # defesa adicional contra corrida
        raise DomainError("Esta solicitação já possui decisão registrada.") from exc
    gate.status = GateStatus.APPROVED
    gate.version += 1
    gate.save(update_fields=["status", "version", "updated_at"])
    transition_stage(stage, StageStatus.APPROVED, actor=actor, reason=justification)
    nxt = project.stages.filter(order=stage.order + 1).select_for_update().first()
    if nxt is not None and nxt.status == StageStatus.NOT_STARTED:
        transition_stage(nxt, StageStatus.IN_PROGRESS, actor=actor, reason=f"Gate da fase {stage.order} aprovado")
    _audit("gate.approve", actor, stage, gate, before={"status": "requested"}, after={"status": "approved"},
           reason=justification)
    return gate


@audit.atomic_service
def reject_gate(stage_id, *, actor, justification: str, request_number: int) -> Gate:
    stage, gate = _lock(stage_id)
    project = stage.project
    rbac.require_perm(actor, "gate.approve", project.organization, project, entity=stage)
    if gate.status != GateStatus.REQUESTED or gate.request_number != request_number:
        raise DomainError("Esta solicitação de gate já foi decidida ou não está mais vigente.")
    if stage.requires_segregation and gate.requested_by_id == actor.pk:
        raise PermissionDenied("Quem solicitou a passagem não pode decidi-la (segregação de funções).")
    justification = (justification or "").strip()
    if len(justification) < 10:
        raise DomainError("A observação da devolução é obrigatória (mínimo de 10 caracteres).")
    GateDecision.objects.create(
        gate=gate, request_number=gate.request_number, decision=GateDecisionType.REJECTED, decided_by=actor,
        justification=justification, requirements_snapshot=evaluate(stage).snapshot,
    )
    gate.status = GateStatus.REJECTED
    gate.version += 1
    gate.save(update_fields=["status", "version", "updated_at"])
    transition_stage(stage, StageStatus.RETURNED, actor=actor, reason=justification)
    _audit("gate.reject", actor, stage, gate, after={"status": "rejected"}, reason=justification)
    return gate


@audit.atomic_service
def cancel_request(stage_id, *, actor, reason: str) -> Gate:
    stage, gate = _lock(stage_id)
    project = stage.project
    rbac.require_perm(actor, "gate.request", project.organization, project, entity=stage)
    if gate.status != GateStatus.REQUESTED:
        raise DomainError("Não há solicitação vigente para cancelar.")
    GateDecision.objects.create(
        gate=gate, request_number=gate.request_number, decision=GateDecisionType.CANCELLED, decided_by=actor,
        justification=reason or "Cancelada pelo solicitante",
    )
    gate.status = GateStatus.CANCELLED
    gate.save(update_fields=["status", "updated_at"])
    transition_stage(stage, StageStatus.IN_PROGRESS, actor=actor, reason=reason or "Solicitação cancelada")
    _audit("gate.cancel", actor, stage, gate, reason=reason)
    return gate


def flag_revalidation(stage: StageInstance, *, actor, cause: str) -> None:
    """RN-010: alteração após aprovação não preserva aprovação aparentemente válida.

    Regra documentada: o gate permanece no histórico como aprovado, mas recebe `revalidation_required`; enquanto
    pendente, bloqueia a passagem da fase seguinte (e o próprio gate) até nova revalidação por aprovador.
    """
    gate = Gate.objects.select_for_update().filter(stage=stage).first()
    if gate is None or gate.status != GateStatus.APPROVED:
        return
    gate.revalidation_required = True
    gate.revalidation_cause = cause[:500]
    gate.version += 1
    gate.save(update_fields=["revalidation_required", "revalidation_cause", "version", "updated_at"])
    _audit("gate.revalidation_flagged", actor, stage, gate, reason=cause)


@audit.atomic_service
def revalidate_gate(stage_id, *, actor, justification: str) -> Gate:
    stage, gate = _lock(stage_id)
    project = stage.project
    rbac.require_perm(actor, "gate.approve", project.organization, project, entity=stage)
    if not gate.revalidation_required:
        raise DomainError("Este gate não possui revalidação pendente.")
    if len((justification or "").strip()) < 10:
        raise DomainError("Justificativa obrigatória (mínimo de 10 caracteres).")
    ev = evaluate(stage, ignore_own_revalidation=True)
    if not ev.ok:
        _audit("gate.revalidate", actor, stage, gate, result="denied", reason="; ".join(ev.blockers)[:2000])
        raise DomainError("Revalidação bloqueada: " + " | ".join(ev.blockers))
    GateDecision.objects.create(
        gate=gate, request_number=gate.request_number, decision=GateDecisionType.REVALIDATED, decided_by=actor,
        justification=justification, requirements_snapshot=ev.snapshot, exceptions_applied=ev.exceptions_applied,
    )
    cause = gate.revalidation_cause
    gate.revalidation_required = False
    gate.revalidation_cause = ""
    gate.version += 1
    gate.save(update_fields=["revalidation_required", "revalidation_cause", "version", "updated_at"])
    _audit("gate.revalidate", actor, stage, gate, before={"cause": cause}, reason=justification)
    return gate


@audit.atomic_service
def grant_exception(stage_id, *, actor, justification: str, residual_risk: str, valid_until,
                    requirement=None, covers_critical_risks: bool = False) -> GateException:
    stage = StageInstance.objects.select_for_update().select_related("project__organization").get(pk=stage_id)
    project = stage.project
    rbac.require_perm(actor, "gate.exception.grant", project.organization, project, entity=stage)
    ensure_project_writable(project)
    if requirement is None and not covers_critical_risks:
        raise DomainError("Informe o requisito excepcionado ou a dispensa de bloqueio por risco crítico.")
    if requirement is not None:
        if requirement.stage_id != stage.pk:
            raise DomainError("O requisito não pertence a esta fase.")
        if requirement.is_legal:
            _audit("gate.exception", actor, stage, get_or_create_gate(stage), result="denied",
                   reason=f"Exceção a requisito legal ({requirement.code})")
            raise DomainError("Requisitos legais obrigatórios não admitem exceção.")
    today = timezone.localdate()
    if valid_until <= today or valid_until > today + timedelta(days=MAX_EXCEPTION_DAYS):
        raise DomainError(f"A validade deve ser futura e de no máximo {MAX_EXCEPTION_DAYS} dias.")
    if len((justification or "").strip()) < 20 or len((residual_risk or "").strip()) < 10:
        raise DomainError("Justificativa (≥ 20) e risco residual aceito (≥ 10 caracteres) são obrigatórios.")
    security_sensitive = (
        covers_critical_risks
        or project.data_classification in (DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED)
        or (requirement is not None and requirement.evidence_kind == "security_report")
    )
    exc = GateException.objects.create(
        stage=stage, requirement=requirement, covers_critical_risks=covers_critical_risks,
        justification=justification.strip(), residual_risk=residual_risk.strip(), valid_until=valid_until,
        granted_by=actor, created_by=actor, requires_security_ack=security_sensitive,
        status=ExceptionStatus.PENDING_SECURITY if security_sensitive else ExceptionStatus.ACTIVE,
    )
    audit.record(
        "gate.exception", actor=actor, organization_id=project.organization_id, project_id=project.pk, entity=exc,
        after={"requirement": requirement.code if requirement else None, "critical_risks": covers_critical_risks,
               "valid_until": valid_until.isoformat(), "status": exc.status, "residual_risk": exc.residual_risk},
        reason=justification,
    )
    return exc


@audit.atomic_service
def acknowledge_exception(exception_id, *, actor) -> GateException:
    exc = GateException.objects.select_for_update().select_related("stage__project__organization").get(pk=exception_id)
    project = exc.stage.project
    rbac.require_perm(actor, "gate.exception.security_ack", project.organization, project, entity=exc)
    if exc.status != ExceptionStatus.PENDING_SECURITY:
        raise DomainError("A exceção não aguarda ciência de segurança.")
    if exc.granted_by_id == actor.pk:
        raise PermissionDenied("Quem concedeu a exceção não pode dar a ciência de segurança.")
    exc.status = ExceptionStatus.ACTIVE
    exc.security_ack_by = actor
    exc.security_ack_at = timezone.now()
    exc.save(update_fields=["status", "security_ack_by", "security_ack_at", "updated_at"])
    audit.record("gate.exception_ack", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=exc, after={"status": exc.status})
    return exc


@audit.atomic_service
def revoke_exception(exception_id, *, actor, reason: str) -> GateException:
    exc = GateException.objects.select_for_update().select_related("stage__project__organization").get(pk=exception_id)
    project = exc.stage.project
    rbac.require_perm(actor, "gate.exception.grant", project.organization, project, entity=exc)
    if exc.status == ExceptionStatus.REVOKED:
        return exc
    exc.status = ExceptionStatus.REVOKED
    exc.revoked_at = timezone.now()
    exc.save(update_fields=["status", "revoked_at", "updated_at"])
    audit.record("gate.exception_revoke", actor=actor, organization_id=project.organization_id,
                 project_id=project.pk, entity=exc, after={"status": exc.status}, reason=reason)
    return exc


# ------------------------------------------------------------- Uso responsável de IA (PMBOK 8 X3.3 + ISACA 2025)


def responsible_ai_rows(project) -> list[ResponsibleAIAssessment]:
    existing = {a.factor: a for a in ResponsibleAIAssessment.objects.filter(project=project).select_related(
        "accountable", "assessed_by")}
    return [existing.get(f) or ResponsibleAIAssessment(project=project, factor=f) for f in ResponsibleAIFactor.values]


def responsible_ai_blockers(project) -> list[str]:
    out = []
    for row in responsible_ai_rows(project):
        if row.status == FactorStatus.PENDING:
            out.append(f"Uso responsável de IA: fator '{row.get_factor_display()}' pendente de avaliação")
    return out


@audit.atomic_service
def assess_responsible_ai(project, *, actor, factor: str, status: str, measures: str, accountable=None):
    """Registra a avaliação de um fator. Tratado/não aplicável exige justificativa e humano responsável."""
    from apps.projects.models import Project

    project = Project.objects.select_for_update().select_related("organization").get(pk=project.pk)
    rbac.require_perm(actor, "responsible_ai.assess", project.organization, project, entity=project)
    ensure_project_writable(project)
    if factor not in ResponsibleAIFactor.values or status not in FactorStatus.values:
        raise DomainError("Fator ou situação inválidos.")
    if status != FactorStatus.PENDING:
        if len((measures or "").strip()) < 20:
            raise DomainError("Descreva as medidas adotadas ou a justificativa (mínimo de 20 caracteres).")
        if accountable is None or not rbac.roles_for(accountable, project.organization, project):
            raise DomainError("Indique o humano responsável, com papel ativo no projeto (PMBOK 8 X3.3).")
    row, created = ResponsibleAIAssessment.objects.get_or_create(
        project=project, factor=factor, defaults={"created_by": actor})
    before = {"status": row.status, "version": row.version}
    row.status, row.measures, row.accountable = status, (measures or "").strip(), accountable
    row.assessed_by, row.assessed_at = actor, timezone.now()
    if not created:
        row.version += 1
    row.save()
    audit.record("responsible_ai.assess", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=row, entity_version=row.version, before=before,
                 after={"factor": factor, "status": status, "accountable": accountable.username if accountable else None})
    for stage in project.stages.filter(requires_responsible_ai=True):
        flag_revalidation(stage, actor=actor, cause=f"Avaliação de uso responsável de IA alterada ({factor})")
    return row
