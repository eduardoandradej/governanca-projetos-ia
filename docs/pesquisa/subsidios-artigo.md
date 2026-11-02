# Subsídios para o artigo (até 5 páginas, template IV SIEEG — formatação final conforme regras da disciplina)

**Título provisório:** Da prova de conceito à produção: um modelo integrado de governança e gestão de projetos para
implantação de plataformas corporativas de IA.

**Resumo (rascunho, ~150 palavras).** Projetos de implantação de plataformas corporativas de IA enfrentam dificuldades de
rastreabilidade, responsabilização e critérios de passagem entre experimentação e produção. Este trabalho, conduzido
segundo a Design Science Research, desenvolveu e avaliou preliminarmente um MVP web que integra o COBIT 2019 — à luz do
white paper da ISACA (2025) sobre governança de sistemas de IA — e o PMBOK 8, incluindo seu apêndice de IA. O artefato
implementa um ciclo de sete fases com Stage-Gates baseados em requisitos verificáveis, evidências revisadas e riscos
tratados; segregação de funções; trilha de auditoria append-only; e uma cadeia dados → informação → conhecimento com
indicadores de ficha técnica, insights determinísticos com revisão humana e lições aprendidas. A avaliação funcional, em
cenário sintético, executou 138 testes automatizados em PostgreSQL e um roteiro de demonstração em navegador, atendendo
aos dez critérios do protocolo. Limitações e próximos passos são discutidos.

**Fluxograma (para figura):** Fase 1 Oportunidade → [Gate: requisitos validados + evidências aprovadas + riscos críticos
tratados + segregação] → Fase 2 Viabilidade → … → Fase 6 Homologação → [Gate + uso responsável de IA] → Fase 7 Operação
(contínua) ⟲ indicadores → insights → revisão humana → ação/lição.

**Tabela compacta (resultados):**

| Critério | Resultado |
|---|---|
| Fluxo 1→7 com gates | Atendido (teste + E2E) |
| Bloqueios (requisito, evidência, risco) | Atendido |
| Segregação e concorrência | Atendido (1 decisão em 2 aprovações simultâneas) |
| Isolamento entre organizações | Atendido (404 em telas, API, downloads, exportação) |
| D→I→K | Atendido (KPI 16,7% = 1/6; insight I02 rastreável; lição aprovada) |
| Segurança e operação | Atendido em laboratório (pip-audit corrigiu 5 CVEs; restauração verificada) |

**Mensagens para a discussão:** (i) governança como controles verificáveis no servidor, não como checklists; (ii) a exigência
de revisão humana dos insights alinha-se à estratégia de "assistência" do PMBOK 8 X3; (iii) o mapeamento ISACA (2025)
liga fases do ciclo de IA aos domínios EDM→APO→BAI→DSS→MEA; (iv) limitações: cenário sintético, sem usuários reais.

**Referências a verificar antes de citar (ABNT NBR 6023):** ISACA (2025) — verificada; PMI (2025) PMBOK 8 — capítulos
verificados; ISACA (2018) COBIT 2019 — a verificar; Peffers et al. (2007) — a verificar; NIST AI RMF (2023) — a verificar.
