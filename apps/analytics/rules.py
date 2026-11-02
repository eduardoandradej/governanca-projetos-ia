"""Regras determinísticas e explicáveis que geram INSIGHTS (camada K) — não há IA generativa aqui.

Cada regra devolve candidatos com: alvo (projeto), título, mensagem, parâmetros e dados de sustentação
(identificadores e valores lidos do PostgreSQL). Insight é sugestão de análise; só vira recomendação
institucional após revisão e aprovação humanas (RN-013).
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Count, Q
from django.utils import timezone

from apps.lifecycle.models import StageStatus, TaskStatus


@dataclass
class Candidate:
    rule_code: str
    project: object
    key: str
    title: str
    message: str
    parameters: dict
    supporting_data: dict


# `pmbok_x3`: caso de uso análogo em PMBOK 8, Apêndice X3, tabela X3-1 (p. 240–242). As regras daqui são
# determinísticas (não usam IA); a analogia indica o nível de supervisão humana esperado (X3.1.1, p. 238–239):
# saída de "assistência" não é considerada completa sem análise humana — daí a revisão obrigatória dos insights.
RULES = {
    "I01": dict(pmbok_x3="Early warning signaling (assistência)",
                name="Fase acima do tempo de referência", params={"max_days_in_stage": 45},
                description="Fase corrente iniciada há mais dias que o parâmetro."),
    "I02": dict(pmbok_x3="Risk impact analysis (assistência)",
                name="Riscos altos/críticos sem plano de tratamento", params={"min_count": 2},
                description="Quantidade de riscos alto/crítico abertos sem tratamento ativo ≥ parâmetro."),
    "I03": dict(pmbok_x3="Early warning signaling (assistência)",
                name="Gate reprovado repetidamente", params={"min_rejections": 2},
                description="Mesmo gate com número de rejeições ≥ parâmetro (tipicamente evidências incompletas)."),
    "I04": dict(pmbok_x3="Real-time monitoring (automação)",
                name="Execução orçamentária acima do limite", params={"max_percent": 90},
                description="Custo realizado / custo planejado ≥ parâmetro (%)."),
    "I05": dict(pmbok_x3="Real-time monitoring (automação)",
                name="Concentração de tarefas vencidas", params={"min_overdue": 3},
                description="Tarefas vencidas no projeto ≥ parâmetro."),
    "I06": dict(pmbok_x3="Early warning signaling (assistência)",
                name="Evidências rejeitadas recorrentes", params={"min_rejected": 2},
                description="Evidências com status rejeitada no projeto ≥ parâmetro."),
}


def rule_i01(projects, p):
    from .metrics import current_stages

    now = timezone.now()
    out = []
    for st in current_stages(projects.filter(status="active")):
        if st.started_at and st.status in (StageStatus.IN_PROGRESS, StageStatus.RETURNED):
            days = (now - st.started_at).days
            if days > p["max_days_in_stage"]:
                out.append(Candidate(
                    "I01", st.project, f"stage:{st.pk}",
                    f"{st.project.code}: fase {st.order} acima do tempo de referência",
                    f"O projeto permanece há {days} dias na fase {st.order} ({st.name}), acima do limite de "
                    f"{p['max_days_in_stage']} dias definido na regra.",
                    p, {"stage_id": str(st.pk), "stage_order": st.order, "days_in_stage": days,
                        "started_at": st.started_at.isoformat()}))
    return out


def rule_i02(projects, p):
    from apps.risks.models import Risk

    active = ["planned", "in_progress", "done"]
    out = []
    for project in projects.filter(status="active"):
        risks = list(Risk.objects.filter(project=project, level__in=["high", "critical"])
                     .exclude(status__in=["accepted", "closed"]).exclude(treatments__status__in=active)
                     .distinct().values("id", "code", "level"))
        if len(risks) >= p["min_count"]:
            out.append(Candidate(
                "I02", project, "risks-untreated", f"{project.code}: {len(risks)} riscos altos/críticos sem tratamento",
                f"{len(risks)} riscos de nível alto ou crítico estão sem plano de tratamento ("
                + ", ".join(r["code"] for r in risks) + f"). Limite da regra: {p['min_count']}.",
                p, {"risks": [{"id": str(r["id"]), "code": r["code"], "level": r["level"]} for r in risks]}))
    return out


def rule_i03(projects, p):
    from apps.governance.models import Gate

    gates = (Gate.objects.filter(stage__project__in=projects)
             .annotate(rej=Count("decisions", filter=Q(decisions__decision="rejected")))
             .filter(rej__gte=p["min_rejections"]).select_related("stage__project"))
    out = []
    for g in gates:
        notes = list(g.decisions.filter(decision="rejected").values_list("justification", flat=True))
        out.append(Candidate(
            "I03", g.stage.project, f"gate:{g.pk}",
            f"{g.stage.project.code}: gate da fase {g.stage.order} reprovado {g.rej} vezes",
            f"O gate da fase {g.stage.order} recebeu {g.rej} rejeições. Justificativas registradas: "
            + " | ".join(n[:120] for n in notes), p,
            {"gate_id": str(g.pk), "stage_order": g.stage.order, "rejections": g.rej, "justifications": notes}))
    return out


def rule_i04(projects, p):
    from apps.risks.services import cost_summary

    out = []
    for project in projects.filter(status="active", planned_cost__gt=0):
        s = cost_summary(project)
        if s["execution_percent"] is not None and s["execution_percent"] >= p["max_percent"]:
            out.append(Candidate(
                "I04", project, "budget", f"{project.code}: execução orçamentária em {s['execution_percent']}%",
                f"O custo realizado ({s['currency']} {s['actual_total']}) atingiu {s['execution_percent']}% do "
                f"planejado ({s['currency']} {s['budget']}); limite da regra: {p['max_percent']}%.",
                p, {"actual": str(s["actual_total"]), "budget": str(s["budget"]),
                    "execution_percent": str(s["execution_percent"])}))
    return out


def rule_i05(projects, p):
    from apps.lifecycle.models import Task

    today = timezone.localdate()
    out = []
    for project in projects.filter(status="active"):
        tasks = list(Task.objects.filter(project=project, due_date__lt=today).exclude(status=TaskStatus.DONE)
                     .values("id", "title", "due_date"))
        if len(tasks) >= p["min_overdue"]:
            out.append(Candidate(
                "I05", project, "overdue-tasks", f"{project.code}: {len(tasks)} tarefas vencidas",
                f"Há {len(tasks)} tarefas não concluídas com prazo vencido (limite {p['min_overdue']}).", p,
                {"tasks": [{"id": str(t["id"]), "title": t["title"], "due_date": t["due_date"].isoformat()}
                           for t in tasks]}))
    return out


def rule_i06(projects, p):
    from apps.evidence.models import EvidenceArtifact

    out = []
    for project in projects.filter(status="active"):
        rej = list(EvidenceArtifact.objects.filter(project=project, status="rejected").values("id", "title"))
        if len(rej) >= p["min_rejected"]:
            out.append(Candidate(
                "I06", project, "evidence-rejected", f"{project.code}: {len(rej)} evidências rejeitadas",
                f"{len(rej)} evidências estão rejeitadas e aguardam nova versão (limite {p['min_rejected']}).", p,
                {"evidences": [{"id": str(e["id"]), "title": e["title"]} for e in rej]}))
    return out


EVALUATORS = {"I01": rule_i01, "I02": rule_i02, "I03": rule_i03, "I04": rule_i04, "I05": rule_i05, "I06": rule_i06}
