"""Indicadores gerenciais (camada I): ficha técnica + cálculo a partir de registros persistidos (RN-012).

Regras gerais:
- Todo indicador recebe um queryset de projetos JÁ filtrado por permissão/escopo.
- Sem denominador (ou sem dados), o valor é None → interface exibe "Sem dados", nunca 100% (T-028).
- `lineage` descreve entidades, filtros e contagens que sustentam o número.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.lifecycle.models import RequirementStatus, StageStatus, TaskStatus


@dataclass
class MetricResult:
    code: str
    value: Decimal | int | None
    numerator: Decimal | int | None = None
    denominator: Decimal | int | None = None
    details: dict = field(default_factory=dict)
    lineage: dict = field(default_factory=dict)

    @property
    def has_data(self) -> bool:
        return self.value is not None


def _pct(num, den) -> Decimal | None:
    if not den:
        return None
    return (Decimal(num) * 100 / Decimal(den)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


DEFINITIONS = [
    dict(code="K01", indicator_type="lagging", pmbok_ref="PMBOK 8 2.1 Governance",
         name="Projetos ativos", unit="projetos", cobit_ref="BAI11",
         definition="Quantidade de projetos com status 'em andamento' no escopo.", numerator="projetos ativos",
         denominator="", calculation="COUNT(projetos WHERE status='active')",
         filters="organização, portfólio, projeto, permissões do usuário", source="projects_project",
         periodicity="sob demanda (tempo real)", limitations="Não pondera porte ou criticidade."),
    dict(code="K02", indicator_type="leading", pmbok_ref="PMBOK 8 2.1.5.1 Leading Indicators",
         name="Conclusão de checklists da fase corrente", unit="%", cobit_ref="BAI11",
         definition="Requisitos obrigatórios validados nas fases correntes dos projetos ativos.",
         numerator="requisitos obrigatórios validados nas fases correntes",
         denominator="requisitos obrigatórios das fases correntes", calculation="numerador / denominador × 100",
         filters="escopo de projetos", source="lifecycle_requirementinstance, lifecycle_stageinstance",
         periodicity="tempo real", limitations="Fase corrente = menor fase não aprovada; requisitos opcionais excluídos."),
    dict(code="K03", indicator_type="leading", pmbok_ref="PMBOK 8 2.1.6.8 Assess and Implement Changes",
         name="Gates pendentes de decisão", unit="gates", cobit_ref="BAI11",
         definition="Solicitações de passagem aguardando aprovação.", numerator="gates com status 'solicitado'",
         denominator="", calculation="COUNT(gates WHERE status='requested')", filters="escopo de projetos",
         source="governance_gate", periodicity="tempo real", limitations="Não inclui revalidações (ver detalhe)."),
    dict(code="K04", indicator_type="leading", pmbok_ref="PMBOK 8 2.7 Risk Performance Domain",
         name="Riscos altos e críticos em aberto", unit="riscos", cobit_ref="APO12",
         definition="Riscos de nível alto/crítico não aceitos nem encerrados.", numerator="riscos alto/crítico abertos",
         denominator="", calculation="COUNT(riscos WHERE nível IN (alto, crítico) AND status NOT IN (aceito, encerrado))",
         filters="escopo de projetos", source="risks_risk", periodicity="tempo real",
         limitations="Depende da política de limiares da organização."),
    dict(code="K05", indicator_type="leading", pmbok_ref="PMBOK 8 2.1.5.1 Leading Indicators",
         name="Tarefas vencidas", unit="tarefas", cobit_ref="BAI11",
         definition="Tarefas não concluídas com prazo anterior a hoje.", numerator="tarefas vencidas", denominator="",
         calculation="COUNT(tarefas WHERE prazo < hoje AND status != concluída)", filters="escopo de projetos",
         source="lifecycle_task", periodicity="diária", limitations="Tarefas sem prazo não entram."),
    dict(code="K06", indicator_type="leading", pmbok_ref="PMBOK 8 2.1.6.7 Monitor and Control Project Performance",
         name="Tempo médio na fase corrente", unit="dias", cobit_ref="MEA01",
         definition="Média de dias desde o início da fase corrente dos projetos ativos.",
         numerator="soma de dias nas fases correntes", denominator="projetos ativos com fase corrente iniciada",
         calculation="numerador / denominador", filters="escopo de projetos", source="lifecycle_stageinstance",
         periodicity="diária", limitations="Não compara com duração planejada quando esta não é informada."),
    dict(code="K07", indicator_type="lagging", pmbok_ref="PMBOK 8 2.1.5.2 Lagging Indicators (variação de prazo)",
         name="Aderência a prazos", unit="%", cobit_ref="MEA01",
         definition="Projetos ativos com prazo final ainda não ultrapassado.",
         numerator="projetos ativos com prazo ≥ hoje", denominator="projetos ativos com prazo definido",
         calculation="numerador / denominador × 100", filters="escopo de projetos", source="projects_project",
         periodicity="diária", limitations="Projetos sem prazo são excluídos do denominador."),
    dict(code="K08", indicator_type="lagging", pmbok_ref="PMBOK 8 2.1.5.2 Lagging Indicators (variação de custo)",
         name="Execução orçamentária", unit="%", cobit_ref="EDM02",
         definition="Custo realizado lançado em relação ao custo planejado dos projetos.",
         numerator="soma de lançamentos realizados", denominator="soma do custo planejado dos projetos",
         calculation="numerador / denominador × 100", filters="escopo de projetos; somente mesma moeda (BRL)",
         source="risks_costentry, projects_project", periodicity="sob demanda",
         limitations="Soma apenas projetos em BRL; não converte moedas; depende de lançamentos completos."),
    dict(code="K09", indicator_type="lagging", pmbok_ref="PMBOK 8 2.1.6.5 Manage Quality Assurance",
         name="Taxa de aprovação de evidências", unit="%", cobit_ref="MEA02",
         definition="Evidências aprovadas entre as que já receberam parecer final.",
         numerator="evidências aprovadas", denominator="evidências aprovadas + rejeitadas",
         calculation="numerador / denominador × 100", filters="escopo de projetos", source="evidence_evidenceartifact",
         periodicity="tempo real", limitations="Considera o status atual, não o histórico de versões."),
    dict(code="K10", indicator_type="leading", pmbok_ref="PMBOK 8 2.1.2 Project Governance Models",
         name="Decisões pendentes", unit="decisões", cobit_ref="EDM01",
         definition="Decisões propostas ainda sem parecer.", numerator="decisões propostas", denominator="",
         calculation="COUNT(decisões WHERE status='proposta')", filters="escopo de projetos",
         source="risks_decisionrecord", periodicity="tempo real", limitations="—"),
    dict(code="K11", indicator_type="lagging", pmbok_ref="PMBOK 8 4.2 Project Development Approaches",
         name="Distribuição por abordagem de implantação", unit="projetos", cobit_ref="APO03",
         definition="Quantidade de projetos por abordagem (local, nuvem privada, pública, híbrida, borda).",
         numerator="projetos por abordagem", denominator="", calculation="COUNT agrupado por abordagem",
         filters="escopo de projetos", source="projects_project", periodicity="tempo real",
         limitations="Abordagem é declarada no cadastro."),
    dict(code="K12", indicator_type="lagging", pmbok_ref="PMBOK 8 2.1.6.8 Assess and Implement Changes",
         name="Taxa de rejeição de gates", unit="%", cobit_ref="BAI11",
         definition="Pareceres de rejeição entre as decisões finais de gate.", numerator="rejeições",
         denominator="aprovações + rejeições", calculation="numerador / denominador × 100",
         filters="escopo de projetos", source="governance_gatedecision", periodicity="sob demanda",
         limitations="Cancelamentos e revalidações não entram."),
]


def current_stages(projects):
    from apps.lifecycle.models import StageInstance

    stages = StageInstance.objects.filter(project__in=projects).exclude(
        status__in=[StageStatus.APPROVED, StageStatus.COMPLETED]
    ).order_by("project_id", "order")
    seen, result = set(), []
    for st in stages:
        if st.project_id not in seen:
            seen.add(st.project_id)
            result.append(st)
    return result


def k01(projects):
    qs = projects.filter(status="active")
    return MetricResult("K01", qs.count(), lineage={"entity": "projects.Project", "filter": "status=active",
                                                    "ids": [str(p) for p in qs.values_list("id", flat=True)[:50]]})


def k02(projects):
    from apps.lifecycle.models import RequirementInstance

    stage_ids = [s.pk for s in current_stages(projects.filter(status="active"))]
    reqs = RequirementInstance.objects.filter(stage_id__in=stage_ids, mandatory=True)
    den = reqs.count()
    num = reqs.filter(status=RequirementStatus.VALIDATED).count()
    return MetricResult("K02", _pct(num, den), num, den,
                        lineage={"entity": "lifecycle.RequirementInstance",
                                 "filter": "mandatory=True AND fase corrente", "stages": len(stage_ids)})


def k03(projects):
    from apps.governance.models import Gate

    qs = Gate.objects.filter(stage__project__in=projects)
    pending = qs.filter(status="requested").count()
    reval = qs.filter(revalidation_required=True).count()
    return MetricResult("K03", pending, details={"revalidations": reval},
                        lineage={"entity": "governance.Gate", "filter": "status=requested"})


def k04(projects):
    from apps.risks.models import Risk

    qs = Risk.objects.filter(project__in=projects, level__in=["high", "critical"]).exclude(
        status__in=["accepted", "closed"])
    by_level = dict(qs.values_list("level").annotate(n=Count("id")))
    return MetricResult("K04", qs.count(), details={"by_level": by_level},
                        lineage={"entity": "risks.Risk", "filter": "level∈{high,critical} ∧ status∉{accepted,closed}"})


def k05(projects):
    from apps.lifecycle.models import Task

    today = timezone.localdate()
    qs = Task.objects.filter(project__in=projects, due_date__lt=today).exclude(status=TaskStatus.DONE)
    return MetricResult("K05", qs.count(), lineage={"entity": "lifecycle.Task", "filter": f"due_date<{today} ∧ status≠done"})


def k06(projects):
    now = timezone.now()
    stages = [s for s in current_stages(projects.filter(status="active")) if s.started_at]
    if not stages:
        return MetricResult("K06", None, 0, 0, lineage={"entity": "lifecycle.StageInstance"})
    total = sum((now - s.started_at).days for s in stages)
    value = (Decimal(total) / Decimal(len(stages))).quantize(Decimal("0.1"))
    return MetricResult("K06", value, total, len(stages), lineage={"entity": "lifecycle.StageInstance",
                                                                    "filter": "fase corrente iniciada"})


def k07(projects):
    today = timezone.localdate()
    qs = projects.filter(status="active", due_date__isnull=False)
    den = qs.count()
    num = qs.filter(due_date__gte=today).count()
    return MetricResult("K07", _pct(num, den), num, den,
                        lineage={"entity": "projects.Project", "filter": "status=active ∧ due_date definido"})


def k08(projects):
    from apps.risks.models import CostEntry

    brl = projects.filter(currency="BRL")
    budget = brl.aggregate(t=Sum("planned_cost"))["t"] or Decimal("0")
    actual = CostEntry.objects.filter(project__in=brl, kind="actual").aggregate(t=Sum("amount"))["t"] or Decimal("0")
    return MetricResult("K08", _pct(actual, budget) if budget else None, actual, budget,
                        details={"currency": "BRL"},
                        lineage={"entity": "risks.CostEntry + projects.Project", "filter": "kind=actual; currency=BRL"})


def k09(projects):
    from apps.evidence.models import EvidenceArtifact

    qs = EvidenceArtifact.objects.filter(project__in=projects)
    approved = qs.filter(status="approved").count()
    rejected = qs.filter(status="rejected").count()
    return MetricResult("K09", _pct(approved, approved + rejected), approved, approved + rejected,
                        lineage={"entity": "evidence.EvidenceArtifact", "filter": "status∈{approved,rejected}"})


def k10(projects):
    from apps.risks.models import DecisionRecord

    n = DecisionRecord.objects.filter(project__in=projects, status="proposed").count()
    return MetricResult("K10", n, lineage={"entity": "risks.DecisionRecord", "filter": "status=proposed"})


def k11(projects):
    counts = Counter(projects.values_list("deployment_approach", flat=True))
    return MetricResult("K11", sum(counts.values()), details={"distribution": dict(counts)},
                        lineage={"entity": "projects.Project", "group_by": "deployment_approach"})


def k12(projects):
    from apps.governance.models import GateDecision

    qs = GateDecision.objects.filter(gate__stage__project__in=projects)
    agg = qs.aggregate(a=Count("id", filter=Q(decision="approved")), r=Count("id", filter=Q(decision="rejected")))
    return MetricResult("K12", _pct(agg["r"], agg["a"] + agg["r"]), agg["r"], agg["a"] + agg["r"],
                        lineage={"entity": "governance.GateDecision", "filter": "decision∈{approved,rejected}"})


CALCULATORS = {f.__name__.upper(): f for f in (k01, k02, k03, k04, k05, k06, k07, k08, k09, k10, k11, k12)}
DEFINITIONS_BY_CODE = {d["code"]: d for d in DEFINITIONS}


def compute(code: str, projects) -> MetricResult:
    return CALCULATORS[code](projects)


def compute_all(projects) -> dict[str, MetricResult]:
    return {code: fn(projects) for code, fn in CALCULATORS.items()}
