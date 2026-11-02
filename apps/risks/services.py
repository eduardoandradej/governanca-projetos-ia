"""Serviços de riscos, custos, decisões e ações (RN-008, RN-016, RN-019)."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db.models import Max, Q, Sum
from django.utils import timezone

from apps.auditlog import services as audit
from apps.lifecycle.services import DomainError, ensure_project_writable
from apps.organizations import rbac
from apps.organizations.models import Organization

from .models import (
    DEFAULT_THRESHOLDS,
    ActionItem,
    CostCategory,
    CostEntry,
    CostKind,
    DecisionRecord,
    DecisionStatus,
    Risk,
    RiskLevel,
    RiskPolicy,
    RiskStatus,
    RiskTreatment,
    TreatmentStatus,
    classify,
)

# ------------------------------------------------------------------------------------------- Riscos


def thresholds_for(organization: Organization) -> tuple[int, int, int]:
    policy = RiskPolicy.objects.filter(organization=organization).first()
    return (policy.critical_min, policy.high_min, policy.medium_min) if policy else DEFAULT_THRESHOLDS


def _recalculate(risk: Risk) -> None:
    risk.score = risk.probability * risk.impact
    risk.level = classify(risk.score, *thresholds_for(risk.organization))


def _check_member(project, user, label):
    if user is not None and not rbac.roles_for(user, project.organization, project):
        raise DomainError(f"O {label} precisa ter papel ativo no projeto.")


def _next_code(model, project, prefix) -> str:
    n = model.objects.filter(project=project).count() + 1
    while model.objects.filter(project=project, code=f"{prefix}-{n:03d}").exists():
        n += 1
    return f"{prefix}-{n:03d}"


@audit.atomic_service
def create_risk(*, actor, project, title: str, category: str, probability: int, impact: int, owner, **fields) -> Risk:
    rbac.require_perm(actor, "risk.manage", project.organization, project, entity=project)
    ensure_project_writable(project)
    _check_member(project, owner, "proprietário")
    stage = fields.get("stage")
    if stage is not None and stage.project_id != project.pk:
        raise DomainError("A fase não pertence ao projeto.")
    for v in (probability, impact):
        if not 1 <= int(v) <= 5:
            raise DomainError("Probabilidade e impacto devem estar entre 1 e 5.")
    risk = Risk(organization=project.organization, project=project, code=_next_code(Risk, project, "R"),
                title=title.strip(), category=category, probability=probability, impact=impact, owner=owner,
                created_by=actor, **fields)
    _recalculate(risk)
    risk.save()
    audit.record("risk.create", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=risk, after={"code": risk.code, "score": risk.score, "level": risk.level,
                                     "category": category, "ai_category": risk.ai_category})
    return risk


@audit.atomic_service
def update_risk_assessment(risk_id, *, actor, probability: int, impact: int, reason: str = "") -> Risk:
    risk = Risk.objects.select_for_update().select_related("project__organization", "organization").get(pk=risk_id)
    project = risk.project
    rbac.require_perm(actor, "risk.manage", project.organization, project, entity=risk)
    ensure_project_writable(project)
    before = {"probability": risk.probability, "impact": risk.impact, "level": risk.level}
    risk.probability, risk.impact = int(probability), int(impact)
    if not (1 <= risk.probability <= 5 and 1 <= risk.impact <= 5):
        raise DomainError("Probabilidade e impacto devem estar entre 1 e 5.")
    _recalculate(risk)
    risk.version += 1
    risk.save()
    audit.record("risk.reassess", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=risk, entity_version=risk.version, before=before,
                 after={"probability": risk.probability, "impact": risk.impact, "level": risk.level}, reason=reason)
    return risk


@audit.atomic_service
def add_treatment(risk_id, *, actor, strategy: str, description: str, owner, due_date) -> RiskTreatment:
    risk = Risk.objects.select_for_update().select_related("project__organization").get(pk=risk_id)
    project = risk.project
    rbac.require_perm(actor, "risk.manage", project.organization, project, entity=risk)
    ensure_project_writable(project)
    _check_member(project, owner, "responsável")
    if len((description or "").strip()) < 10:
        raise DomainError("Descreva a medida de tratamento (mínimo de 10 caracteres).")
    treatment = RiskTreatment.objects.create(risk=risk, strategy=strategy, description=description.strip(),
                                             owner=owner, due_date=due_date, created_by=actor)
    if risk.status == RiskStatus.IDENTIFIED:
        risk.status = RiskStatus.TREATING
        risk.save(update_fields=["status", "updated_at"])
    audit.record("risk.treatment", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=risk, after={"strategy": strategy, "due_date": due_date, "owner": owner.username})
    return treatment


@audit.atomic_service
def accept_residual(risk_id, *, actor, residual_probability: int, residual_impact: int, justification: str) -> Risk:
    """Aceite formal de risco residual pelo patrocinador (perfil autorizado)."""
    risk = Risk.objects.select_for_update().select_related("project__organization").get(pk=risk_id)
    project = risk.project
    rbac.require_perm(actor, "risk.accept_residual", project.organization, project, entity=risk)
    if len((justification or "").strip()) < 10:
        raise DomainError("Justificativa do aceite obrigatória (mínimo de 10 caracteres).")
    risk.residual_probability, risk.residual_impact = int(residual_probability), int(residual_impact)
    risk.residual_accepted_by = actor
    risk.residual_accepted_at = timezone.now()
    risk.status = RiskStatus.ACCEPTED
    risk.version += 1
    risk.save()
    audit.record("risk.accept_residual", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=risk, entity_version=risk.version,
                 after={"residual": risk.residual_score, "status": risk.status}, reason=justification)
    return risk


def untreated_critical_risks(project):
    """RN-008 (regra documentada): risco crítico é 'não tratado' se não estiver aceito/encerrado e não possuir
    nenhum tratamento ativo (planejado, em execução ou concluído) com responsável e prazo."""
    active = [TreatmentStatus.PLANNED, TreatmentStatus.IN_PROGRESS, TreatmentStatus.DONE]
    return (
        Risk.objects.filter(project=project, level=RiskLevel.CRITICAL)
        .exclude(status__in=[RiskStatus.ACCEPTED, RiskStatus.CLOSED])
        .exclude(treatments__status__in=active)
        .distinct()
    )


def risk_matrix(risks) -> list[list[dict]]:
    """Matriz 5×5 (linhas = impacto 5→1, colunas = probabilidade 1→5) com contagens dos riscos informados."""
    counts = defaultdict(int)
    for r in risks:
        counts[(r.impact, r.probability)] += 1
    return [
        [{"impact": i, "probability": p, "count": counts[(i, p)], "level": classify(i * p)} for p in range(1, 6)]
        for i in range(5, 0, -1)
    ]


# ------------------------------------------------------------------------------------------- Custos


@audit.atomic_service
def add_cost(*, actor, project, category: str, kind: str, amount, entry_date, justification: str,
             source_document: str = "", stage=None) -> CostEntry:
    rbac.require_perm(actor, "cost.manage", project.organization, project, entity=project)
    ensure_project_writable(project)
    if isinstance(amount, float):
        raise DomainError("Valores monetários devem ser Decimal, nunca float.")
    amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    if amount <= 0:
        raise DomainError("O valor deve ser positivo.")
    if category not in CostCategory.values or kind not in CostKind.values:
        raise DomainError("Categoria ou tipo de custo inválido.")
    if project.start_date and entry_date < project.start_date.replace(year=project.start_date.year - 1):
        raise DomainError("Data de competência incoerente com o período do projeto.")
    if stage is not None and stage.project_id != project.pk:
        raise DomainError("A fase não pertence ao projeto.")
    if len((justification or "").strip()) < 5:
        raise DomainError("Justificativa obrigatória.")
    entry = CostEntry.objects.create(
        project=project, stage=stage, category=category, kind=kind, amount=amount, currency=project.currency,
        entry_date=entry_date, justification=justification.strip(), source_document=source_document, created_by=actor,
    )
    audit.record("cost.create", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=entry, after={"category": category, "kind": kind, "amount": amount, "currency": entry.currency})
    return entry


def cost_summary(project) -> dict:
    """Totais por categoria (Decimal). Previsto inclui lançamentos 'previsto'; custo planejado do projeto à parte."""
    rows = (
        CostEntry.objects.filter(project=project)
        .values("category", "kind")
        .annotate(total=Sum("amount"))
    )
    zero = Decimal("0.00")
    table = {c: {"label": label, "planned": zero, "actual": zero} for c, label in CostCategory.choices}
    for row in rows:
        table[row["category"]][row["kind"]] = row["total"] or zero
    planned = sum((v["planned"] for v in table.values()), zero)
    actual = sum((v["actual"] for v in table.values()), zero)
    budget = project.planned_cost
    return {
        "rows": table, "planned_total": planned, "actual_total": actual, "budget": budget,
        "variance": actual - budget, "currency": project.currency,
        "execution_percent": (actual / budget * 100).quantize(Decimal("0.1")) if budget else None,
    }


# ----------------------------------------------------------------------------------------- Decisões


@audit.atomic_service
def propose_decision(*, actor, project, agenda: str, alternatives: str, decision: str, rationale: str,
                     topic: str = "general", risks_considered: str = "", evidences=()) -> DecisionRecord:
    rbac.require_perm(actor, "decision.record", project.organization, project, entity=project)
    if topic != "reopen":
        ensure_project_writable(project)
    for label, value in (("pauta", agenda), ("alternativas", alternatives), ("decisão", decision),
                         ("motivação", rationale)):
        if not (value or "").strip():
            raise DomainError(f"Campo obrigatório: {label}.")
    rec = DecisionRecord.objects.create(
        project=project, code=_next_code(DecisionRecord, project, "D"), topic=topic, agenda=agenda.strip(),
        alternatives=alternatives.strip(), decision=decision.strip(), rationale=rationale.strip(),
        risks_considered=risks_considered, proposed_by=actor, created_by=actor,
    )
    for e in evidences:
        if e.project_id != project.pk:
            raise DomainError("Evidência de outro projeto não pode ser vinculada.")
        rec.evidences.add(e)
    audit.record("decision.propose", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=rec, entity_version=rec.version, after={"code": rec.code, "topic": topic, "agenda": rec.agenda})
    return rec


@audit.atomic_service
def decide(decision_id, *, actor, approve: bool, note: str) -> DecisionRecord:
    rec = DecisionRecord.objects.select_for_update().select_related("project__organization").get(pk=decision_id)
    project = rec.project
    rbac.require_perm(actor, "decision.approve", project.organization, project, entity=rec)
    if rec.status != DecisionStatus.PROPOSED:
        raise DomainError("Somente decisões propostas podem ser aprovadas ou rejeitadas.")
    if rec.proposed_by_id == actor.pk:
        raise PermissionDenied("Quem propôs a decisão não pode aprová-la (segregação de funções).")
    if len((note or "").strip()) < 5:
        raise DomainError("Parecer obrigatório.")
    rec.status = DecisionStatus.APPROVED if approve else DecisionStatus.REJECTED
    rec.decided_by, rec.decided_at, rec.decision_note = actor, timezone.now(), note.strip()
    rec.save()
    if approve and rec.supersedes_id:
        DecisionRecord.objects.filter(pk=rec.supersedes_id).update(status=DecisionStatus.SUPERSEDED)
    audit.record("decision.decide", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=rec, entity_version=rec.version, after={"status": rec.status}, reason=note)
    return rec


@audit.atomic_service
def revise_decision(decision_id, *, actor, decision: str, rationale: str, alternatives: str = "") -> DecisionRecord:
    """RN-019: alteração de decisão aprovada gera nova versão; a anterior só é substituída quando a nova é aprovada."""
    old = DecisionRecord.objects.select_for_update().select_related("project__organization").get(pk=decision_id)
    project = old.project
    rbac.require_perm(actor, "decision.record", project.organization, project, entity=old)
    if old.status != DecisionStatus.APPROVED:
        raise DomainError("Somente decisões aprovadas são revisadas por nova versão.")
    if hasattr(old, "superseded_by"):
        raise DomainError("Esta versão já possui revisão.")
    last = DecisionRecord.objects.filter(project=project, code=old.code).aggregate(m=Max("version"))["m"]
    new = DecisionRecord.objects.create(
        project=project, code=old.code, version=last + 1, topic=old.topic, agenda=old.agenda,
        alternatives=alternatives or old.alternatives, decision=decision.strip(), rationale=rationale.strip(),
        risks_considered=old.risks_considered, proposed_by=actor, created_by=actor, supersedes=old,
    )
    audit.record("decision.revise", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=new, entity_version=new.version, before={"version": old.version}, after={"version": new.version})
    return new


def approved_reopen_decision(project, decision_id):
    return DecisionRecord.objects.filter(
        Q(pk=decision_id), project=project, topic="reopen", status=DecisionStatus.APPROVED
    ).first()


@audit.atomic_service
def create_action(*, actor, project, title: str, owner, due_date=None, decision=None, origin: str = "") -> ActionItem:
    rbac.require_perm(actor, "decision.record", project.organization, project, entity=project)
    _check_member(project, owner, "responsável")
    if decision is not None and decision.project_id != project.pk:
        raise DomainError("Decisão de outro projeto.")
    item = ActionItem.objects.create(project=project, title=title.strip(), owner=owner, due_date=due_date,
                                     decision=decision, origin=origin, created_by=actor)
    audit.record("action.create", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=item, after={"title": item.title, "origin": origin})
    return item
