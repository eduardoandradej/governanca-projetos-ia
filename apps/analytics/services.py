"""Serviços das camadas D→I→K, sempre filtrados por escopo de permissão no servidor."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.auditlog import services as audit
from apps.lifecycle.services import DomainError, ensure_project_writable
from apps.organizations import rbac
from apps.organizations.models import MembershipStatus, RoleAssignment
from apps.projects.models import DataClassification, Project

from . import metrics, rules
from .models import (
    DataAsset,
    DataAssetVersion,
    DataLineage,
    Insight,
    InsightReview,
    InsightStatus,
    LessonLearned,
    LessonStatus,
    LessonVisibility,
    MetricDefinition,
    MetricSnapshot,
)

SENSITIVE = (DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED)


def scoped_projects(user, organization_id=None, project_id=None):
    """Projetos visíveis ao usuário, com filtros opcionais (validados contra o escopo)."""
    qs = Project.objects.filter(rbac.visible_project_filter(user))
    if organization_id:
        qs = qs.filter(organization_id=organization_id)
    if project_id:
        qs = qs.filter(pk=project_id)
    return qs


# ------------------------------------------------------------------------------------------- Dados (D)


@audit.atomic_service
def create_asset(*, actor, project, name: str, kind: str, purpose: str, owner, **fields) -> DataAsset:
    rbac.require_perm(actor, "data.manage", project.organization, project, entity=project)
    ensure_project_writable(project)
    if not rbac.roles_for(owner, project.organization, project):
        raise DomainError("O proprietário precisa ter papel ativo no projeto.")
    try:
        with transaction.atomic():
            asset = DataAsset.objects.create(organization=project.organization, project=project, name=name.strip(),
                                             kind=kind, purpose=purpose.strip(), owner=owner, created_by=actor, **fields)
    except IntegrityError as exc:
        raise DomainError("Já existe ativo com este nome no projeto.") from exc
    DataAssetVersion.objects.create(asset=asset, version=asset.current_version, locator=asset.locator,
                                    change_note="Registro inicial", created_by=actor)
    audit.record("data.asset_create", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=asset, after={"name": asset.name, "kind": kind, "classification": asset.classification,
                                      "personal_data": asset.contains_personal_data})
    return asset


@audit.atomic_service
def add_asset_version(asset_id, *, actor, version: str, locator: str = "", change_note: str = "") -> DataAssetVersion:
    asset = DataAsset.objects.select_for_update().select_related("project__organization").get(pk=asset_id)
    project = asset.project
    rbac.require_perm(actor, "data.manage", project.organization, project, entity=asset)
    if asset.versions.filter(version=version).exists():
        raise DomainError("Versão já registrada.")
    v = DataAssetVersion.objects.create(asset=asset, version=version, locator=locator, change_note=change_note,
                                        created_by=actor)
    asset.current_version, asset.locator = version, locator or asset.locator
    asset.save(update_fields=["current_version", "locator", "updated_at"])
    audit.record("data.asset_version", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=asset, after={"version": version})
    return v


@audit.atomic_service
def add_lineage(*, actor, source: DataAsset, target: DataAsset, transformation: str) -> DataLineage:
    project = target.project
    rbac.require_perm(actor, "data.manage", project.organization, project, entity=target)
    if source.organization_id != target.organization_id:
        raise DomainError("Linhagem só entre ativos da mesma organização.")  # RN-021
    if not rbac.has_perm(actor, "project.view", source.organization, source.project):
        raise PermissionDenied("Sem acesso ao ativo de origem.")
    if source.pk == target.pk:
        raise DomainError("Origem e saída devem ser ativos distintos.")
    if _reaches(target, source):
        raise DomainError("A linhagem criaria um ciclo.")
    edge, _ = DataLineage.objects.get_or_create(
        source=source, target=target,
        defaults={"organization": target.organization, "transformation": transformation.strip(), "created_by": actor},
    )
    audit.record("data.lineage", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=edge, after={"source": source.name, "target": target.name})
    return edge


def _reaches(start: DataAsset, goal: DataAsset) -> bool:
    frontier, seen = [start.pk], set()
    while frontier:
        node = frontier.pop()
        if node == goal.pk:
            return True
        if node in seen:
            continue
        seen.add(node)
        frontier.extend(DataLineage.objects.filter(source_id=node).values_list("target_id", flat=True))
    return False


def lineage_for(asset: DataAsset) -> dict:
    return {
        "upstream": list(asset.upstream.select_related("source")),
        "downstream": list(asset.downstream.select_related("target")),
    }


# -------------------------------------------------------------------------------------- Informação (I)


def sync_definitions() -> None:
    for d in metrics.DEFINITIONS:
        MetricDefinition.objects.update_or_create(code=d["code"], defaults={k: v for k, v in d.items() if k != "code"})


def _dec(v):
    return None if v is None else Decimal(str(v))


@audit.atomic_service
def capture_snapshots(*, actor, organization) -> int:
    """Grava snapshots dos indicadores no escopo da organização (usuário precisa de analytics.view)."""
    rbac.require_perm(actor, "analytics.view", organization)
    sync_definitions()
    projects = scoped_projects(actor, organization_id=organization.pk)
    n = 0
    for code, result in metrics.compute_all(projects).items():
        MetricSnapshot.objects.create(
            metric=MetricDefinition.objects.get(code=code), organization=organization, value=_dec(result.value),
            numerator=_dec(result.numerator), denominator=_dec(result.denominator),
            details={"details": result.details, "lineage": result.lineage, "project_count": projects.count()},
            is_demo=organization.is_demo, computed_by=actor,
        )
        n += 1
    audit.record("analytics.snapshot", actor=actor, organization_id=organization.pk, after={"metrics": n})
    return n


def portfolio_dashboard(user, organization_id=None) -> dict:
    projects = scoped_projects(user, organization_id=organization_id)
    results = metrics.compute_all(projects)
    rows = []
    for p in projects.select_related("organization", "manager").order_by("organization__name", "code"):
        st = p.current_stage
        prog = None
        if st:
            from apps.lifecycle.services import stage_progress

            prog = stage_progress(st)
        rows.append({"project": p, "stage": st, "progress": prog})
    return {
        "results": results, "definitions": metrics.DEFINITIONS_BY_CODE, "rows": rows,
        "has_demo": projects.filter(organization__is_demo=True).exists(), "computed_at": timezone.now(),
        "project_count": projects.count(),
    }


# ------------------------------------------------------------------------------------- Conhecimento (K)


@audit.atomic_service
def generate_insights(*, actor, organization, parameters: dict | None = None) -> list[Insight]:
    """Executa as regras determinísticas no escopo do usuário. Idempotente por fingerprint (sem duplicar)."""
    rbac.require_perm(actor, "insight.review", organization)
    projects = scoped_projects(actor, organization_id=organization.pk)
    created = []
    for code, spec in rules.RULES.items():
        params = {**spec["params"], **(parameters or {}).get(code, {})}
        for c in rules.EVALUATORS[code](projects, params):
            fingerprint = f"{code}|{c.project.pk}|{c.key}"
            if Insight.objects.filter(fingerprint=fingerprint, status__in=["proposed", "reviewed"]).exists():
                continue
            ins = Insight.objects.create(
                organization=organization, project=c.project, rule_code=code, title=c.title[:200],
                message=c.message, parameters=c.parameters, supporting_data=c.supporting_data,
                fingerprint=fingerprint, is_demo=organization.is_demo, created_by=actor,
            )
            created.append(ins)
    audit.record("insight.generate", actor=actor, organization_id=organization.pk,
                 after={"created": len(created), "rules": list(rules.RULES)})
    return created


def _lock_insight(insight_id) -> Insight:
    return Insight.objects.select_for_update(of=("self",)).select_related("organization", "project").get(pk=insight_id)


def _transition_insight(ins, actor, to_status, note):
    InsightReview.objects.create(insight=ins, reviewer=actor, from_status=ins.status, to_status=to_status, note=note)
    before = ins.status
    ins.status = to_status
    ins.justification = note
    audit.record("insight.review", actor=actor, organization_id=ins.organization_id, project_id=ins.project_id,
                 entity=ins, before={"status": before}, after={"status": to_status}, reason=note)


@audit.atomic_service
def review_insight(insight_id, *, actor, note: str) -> Insight:
    ins = _lock_insight(insight_id)
    rbac.require_perm(actor, "insight.review", ins.organization, ins.project, entity=ins)
    if ins.status != InsightStatus.PROPOSED:
        raise DomainError("Somente insights propostos podem ser revisados.")
    if len((note or "").strip()) < 10:
        raise DomainError("Registre a análise (mínimo de 10 caracteres).")
    _transition_insight(ins, actor, InsightStatus.REVIEWED, note.strip())
    ins.reviewed_by = actor
    ins.save()
    return ins


@audit.atomic_service
def approve_insight(insight_id, *, actor, note: str, action_title: str = "", action_owner=None,
                    action_due=None) -> Insight:
    """Converte o insight em recomendação institucional (aprovador ≠ revisor) e, opcionalmente, em ação."""
    ins = _lock_insight(insight_id)
    rbac.require_perm(actor, "lesson.approve", ins.organization, ins.project, entity=ins)
    if ins.status != InsightStatus.REVIEWED:
        raise DomainError("O insight precisa ser revisado antes da aprovação.")
    if ins.reviewed_by_id == actor.pk:
        raise PermissionDenied("Quem revisou o insight não pode aprová-lo (segregação de funções).")
    if len((note or "").strip()) < 10:
        raise DomainError("Justificativa obrigatória (mínimo de 10 caracteres).")
    if action_title:
        from apps.risks.services import create_action

        ins.action = create_action(actor=actor, project=ins.project, title=action_title, owner=action_owner,
                                   due_date=action_due, origin=f"insight {ins.rule_code}")
    _transition_insight(ins, actor, InsightStatus.APPROVED, note.strip())
    ins.approved_by = actor
    ins.save()
    return ins


@audit.atomic_service
def discard_insight(insight_id, *, actor, note: str) -> Insight:
    ins = _lock_insight(insight_id)
    rbac.require_perm(actor, "insight.review", ins.organization, ins.project, entity=ins)
    if ins.status in (InsightStatus.APPROVED, InsightStatus.DISCARDED):
        raise DomainError("Insight já finalizado.")
    if len((note or "").strip()) < 10:
        raise DomainError("Justifique o descarte (mínimo de 10 caracteres).")
    _transition_insight(ins, actor, InsightStatus.DISCARDED, note.strip())
    ins.save()
    return ins


@audit.atomic_service
def create_lesson(*, actor, project, title: str, context: str, lesson: str, recommendation: str,
                  source_insight=None, **taxonomy) -> LessonLearned:
    rbac.require_perm(actor, "lesson.manage", project.organization, project, entity=project)
    if source_insight is not None and source_insight.project_id != project.pk:
        raise DomainError("O insight de origem pertence a outro projeto.")
    for label, v in (("título", title), ("contexto", context), ("lição", lesson), ("recomendação", recommendation)):
        if not (v or "").strip():
            raise DomainError(f"Campo obrigatório: {label}.")
    obj = LessonLearned.objects.create(
        organization=project.organization, project=project, title=title.strip(), context=context.strip(),
        lesson=lesson.strip(), recommendation=recommendation.strip(), source_insight=source_insight,
        platform_type=taxonomy.pop("platform_type", project.platform_type),
        classification=taxonomy.pop("classification", project.data_classification),
        is_demo=project.organization.is_demo, created_by=actor, **taxonomy,
    )
    audit.record("lesson.create", actor=actor, organization_id=project.organization_id, project_id=project.pk,
                 entity=obj, after={"title": obj.title, "insight": str(source_insight.pk) if source_insight else None})
    return obj


@audit.atomic_service
def approve_lesson(lesson_id, *, actor, visibility: str, disclosure_justification: str = "") -> LessonLearned:
    """RN-018: lição de projeto confidencial/restrito só é divulgada à organização com justificativa explícita."""
    obj = LessonLearned.objects.select_for_update().select_related("project", "organization").get(pk=lesson_id)
    rbac.require_perm(actor, "lesson.approve", obj.organization, obj.project, entity=obj)
    if obj.status != LessonStatus.DRAFT:
        raise DomainError("Somente rascunhos podem ser aprovados.")
    if visibility not in LessonVisibility.values:
        raise DomainError("Visibilidade inválida.")
    sensitive = obj.classification in SENSITIVE or obj.project.data_classification in SENSITIVE
    if visibility == LessonVisibility.ORGANIZATION and sensitive:
        if len((disclosure_justification or "").strip()) < 20:
            audit.record("lesson.approve", actor=actor, result="denied", organization_id=obj.organization_id,
                         project_id=obj.project_id, entity=obj, reason="Divulgação de lição classificada sem justificativa")
            raise DomainError("Lição de projeto confidencial/restrito exige justificativa de divulgação (≥ 20).")
    obj.status = LessonStatus.APPROVED
    obj.visibility = visibility
    obj.disclosure_justification = disclosure_justification.strip()
    obj.approved_by, obj.approved_at = actor, timezone.now()
    obj.save()
    audit.record("lesson.approve", actor=actor, organization_id=obj.organization_id, project_id=obj.project_id,
                 entity=obj, after={"visibility": visibility, "classification": obj.classification},
                 reason=disclosure_justification)
    return obj


def visible_lessons(user):
    """Lições do próprio escopo de projetos + lições aprovadas e divulgadas às organizações do usuário.

    Nunca cruza organizações (RN-018/RN-021)."""
    member_orgs = RoleAssignment.objects.filter(
        user=user, revoked_at__isnull=True, organization__memberships__user=user,
        organization__memberships__status=MembershipStatus.ACTIVE,
    ).values("organization_id")
    project_ids = Project.objects.filter(rbac.visible_project_filter(user)).values("id")
    return LessonLearned.objects.filter(
        Q(project_id__in=project_ids)
        | Q(organization_id__in=member_orgs, status=LessonStatus.APPROVED, visibility=LessonVisibility.ORGANIZATION)
    ).exclude(status=LessonStatus.ARCHIVED).distinct()
