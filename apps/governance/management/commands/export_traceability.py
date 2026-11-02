"""Gera docs/governanca/matriz-controles.md e docs/dados/indicadores.md a partir do banco/código."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.analytics import metrics, rules
from apps.governance.models import ControlMapping, FrameworkReference, GovernanceObjective
from apps.lifecycle.models import LifecycleTemplateVersion


class Command(BaseCommand):
    help = "Exporta matrizes de rastreabilidade COBIT/PMBOK e fichas de indicadores para Markdown."

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR) / "docs"
        version = LifecycleTemplateVersion.objects.filter(status="published", template__organization__isnull=True)\
            .order_by("-number").first()
        lines = [
            "# Matriz de controles e rastreabilidade (gerada automaticamente)",
            "",
            "Gerada por `python manage.py export_traceability`. Associações são **interpretação da equipe**, exceto as",
            "marcadas como *ISACA 2025* (citadas em ISACA, *Leveraging COBIT for Effective AI System Governance*, 2025,",
            "com página). Não constitui certificação de conformidade com COBIT 2019 ou PMBOK.",
            "",
            f"Template vigente: **{version}** — {version.source_reference}" if version else "",
            "",
            "## 1. Objetivos COBIT 2019",
            "",
            "| Objetivo | Fase de IA (ISACA) | IA confiável | Fonte / páginas | Requisitos (template vigente) | Funcionalidades |",
            "|---|---|---|---|---|---|",
        ]
        for o in GovernanceObjective.objects.all():
            maps = ControlMapping.objects.filter(objective=o).select_related("requirement_template__stage_template")
            current = version.pk if version else None
            reqs = sorted({
                f"{m.requirement_template.code}{' ¹' if m.basis == 'isaca_ai_2025' else ''}" for m in maps
                if m.requirement_template and m.requirement_template.stage_template.template_version_id == current
            })
            feats = [m.feature for m in maps if m.feature]
            src = "ISACA 2025" if "Leveraging" in o.source else "Interpretação da equipe"
            lines.append(f"| {o.code} {o.name} | {o.ai_lifecycle_phase} | {o.trustworthy_ai or '—'} | {src} p. "
                         f"{o.source_pages} | {', '.join(reqs) or '—'} | {'; '.join(feats) or '—'} |")
        lines += ["", "¹ mapeamento citado no white paper ISACA (2025); demais: interpretação da equipe.", "",
                  "## 2. PMI PMBOK Guide 8ª ed. (tabela separada)", "",
                  "| Seção | Título | Parte · páginas | Uso no sistema | Mapeamentos |", "|---|---|---|---|---|"]
        for r in FrameworkReference.objects.prefetch_related("mappings__requirement_template"):
            maps = sorted({m.requirement_template.code if m.requirement_template else m.feature
                           for m in r.mappings.all()})
            lines.append(f"| {r.section} | {r.title} | {r.part} · p. {r.pages} | {r.analysis} | {'; '.join(maps) or '—'} |")
        lines += ["", "## 3. Requisitos do template vigente", "", "| Fase | Código | Requisito | Obrig. | Evidência | Legal | COBIT |",
                  "|---|---|---|---|---|---|---|"]
        if version:
            for st in version.stages.order_by("order").prefetch_related("requirements"):
                for rq in st.requirements.order_by("order"):
                    lines.append(f"| {st.order} | {rq.code} | {rq.title} | {'sim' if rq.mandatory else 'não'} | "
                                 f"{rq.get_evidence_kind_display() if rq.requires_evidence else '—'} | "
                                 f"{'sim' if rq.is_legal else 'não'} | {rq.cobit_ref} |")
        (base / "governanca" / "matriz-controles.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        ind = ["# Indicadores (fichas técnicas) e regras de insight (gerado automaticamente)", "",
               "Cálculo em `apps/analytics/metrics.py`; sem denominador ou dados → \"Sem dados\" (nunca 100%).", ""]
        for d in metrics.DEFINITIONS:
            ind += [f"## {d['code']} — {d['name']}", "",
                    f"- Definição: {d['definition']}", f"- Numerador: {d['numerator'] or '—'}",
                    f"- Denominador: {d['denominator'] or '—'}", f"- Regra: `{d['calculation']}`",
                    f"- Unidade: {d['unit']} · Tipo: {d['indicator_type']} ({d['pmbok_ref']}) · COBIT: {d['cobit_ref']}",
                    f"- Filtros: {d['filters']} · Fonte: {d['source']} · Periodicidade: {d['periodicity']}",
                    f"- Limitações: {d['limitations']}", ""]
        ind += ["# Regras determinísticas de insight", "", "| Regra | Nome | Parâmetros | Descrição | Análogo PMBOK 8 X3 |",
                "|---|---|---|---|---|"]
        for code, r in rules.RULES.items():
            ind.append(f"| {code} | {r['name']} | `{r['params']}` | {r['description']} | {r['pmbok_x3']} |")
        (base / "dados" / "indicadores.md").write_text("\n".join(ind) + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS("Matrizes e fichas exportadas."))
