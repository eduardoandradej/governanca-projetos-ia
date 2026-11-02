# Matriz de rastreabilidade: referencial → requisito → implementação → tela → teste → evidência

| Referencial (interpretação) | Requisito/RN | Entidade / serviço | Tela / API | Teste | Evidência |
|---|---|---|---|---|---|
| COBIT BAI11; PMBOK 2.1 Governança | RN-003/004 ciclo de 7 fases e gates | `StageInstance`, `governance.services.evaluate/request_gate/approve_gate` | Fase do projeto, `/gates/`, `/api/v1/projetos/{id}/stages/` | T-003, T-004, T-007, T-024 | m8/02, m8/05 |
| COBIT EDM01; PMBOK 3.6 Líder responsável; X3.3 responsabilização | RN-006/007/015 segregação e autoria | `rbac`, `approve_gate`, `validate_requirement`, `review_evidence`, `decide`, `approve_insight` | Painéis de gate, evidência, decisões, insights | T-006, T-014, T-026 | m8/03, m8/05 |
| COBIT APO12/EDM03; PMBOK 2.7; ISACA fig. 5 | RN-008 risco crítico bloqueia | `Risk`, `untreated_critical_risks` | Riscos (matriz 5×5) | T-010, T-017 | m8/04 |
| COBIT APO14; ISACA p. 13 (dados) | RN-018/021 dados e linhagem | `DataAsset`, `DataLineage`, `add_lineage` | Aba Dados | T-019, `test_catalog_*` | — |
| COBIT BAI06; PMBOK 2.1.6.8 mudanças | RN-010/019 revalidação e versões | `flag_revalidation`, `EvidenceVersion`, `revise_decision` | Painel do gate, evidência, decisões | T-009, `test_decision_lifecycle_*` | — |
| COBIT BAI07; PMBOK 2.1.6.9 | RN-031 entrada em operação | `approve_gate` (fase 6 → 7) | Linha do tempo | T-024 | m8/05 |
| COBIT MEA01; PMBOK 2.1.5 indicadores | RN-012 KPIs com ficha | `analytics.metrics` | Visão geral, `/inteligencia/indicadores/K02/`, `/api/v1/indicadores/` | T-018, T-028 | m8/07 |
| PMBOK 2.1.6.6 conhecimento; ISACA (monitoramento) | RN-013/035 insights e lições | `rules`, `Insight`, `LessonLearned` | Insights, lições | T-019 | m8/08 |
| COBIT MEA02 controle interno | RN-002/017/014 escopo, anexos, exportação | `get_project_or_404`, `authorize_download`, `csv_response` | Downloads, exportação | T-002, T-015, T-020, T-021, T-023 | m8/10 |
| PMBOK X3.3; ISACA IA confiável | RN-037 uso responsável de IA | `ResponsibleAIAssessment`, `responsible_ai_blockers` | Aba Uso responsável de IA | `test_gate_6_requires_responsible_ai_assessment` | — |
| COBIT MEA02 / auditoria | F09 trilha append-only | `AuditEvent` + gatilho | `/auditoria/` | T-013, T-022 | m8/09 |

Matriz completa objetivo→requisito do template: `docs/governanca/matriz-controles.md`.
