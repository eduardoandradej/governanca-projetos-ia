# Status da implementação

Atualizado a cada incremento. "Concluído" = implementado **e** coberto por teste executado com sucesso.

| Incremento | Situação | Evidência |
|---|---|---|
| M0 Descoberta e desenho | Concluído | ADR-001..004, `docs/architecture/`, este arquivo |
| M1 Fundação (auth, organizações, RBAC, auditoria, layout, seed) | Concluído | `apps/accounts`, `apps/organizations`, `apps/auditlog`; testes `test_auth.py`, `test_rbac.py` |
| M2 Projetos e ciclo de vida | Concluído | `apps/projects`, `apps/lifecycle`; testes `test_projects.py`, `test_lifecycle.py`; capturas `docs/evidencias/m2/` |
| M3 Governança e gates | Concluído | `apps/governance`, `apps/evidence`; testes `test_gates.py`, `test_concurrency.py`, `test_evidence.py`; catálogo COBIT com base em ISACA (2025); template v2 |
| M4 Riscos, custos e decisões | Concluído | `apps/risks` (matriz 5×5, categorias de risco de IA ISACA fig. 5, custos Decimal, decisões versionadas, ações); `test_risks.py` |
| M5 Dados → informação → conhecimento | Concluído | `apps/analytics`: catálogo e linhagem (D), 12 KPIs com ficha técnica e snapshots (I), 6 regras determinísticas de insight com revisão humana e lições aprendidas com visibilidade controlada (K); `test_dik.py` |
| Incremento PMBOK 8 | Concluído | Referências PMBOK 8 separadas do COBIT (26 seções, título+página), abordagem de desenvolvimento (4.2) e estratégia de adoção de IA (X3.1.1) no projeto, avaliação de uso responsável de IA (X3.3, 8 fatores) bloqueando o gate 6, template v3, KPIs classificados tendência/resultado (2.1.5) |
| M6 Interface completa e API | Concluído | API `/api/v1/` (DRF, mesma autorização), exportações CSV neutralizadas e auditadas, integrações NoOp, telas para todos os módulos; `test_api_export.py` (navegação por 6 perfis) |
| M7 Qualidade, segurança e instalação | Pendente | — |
| M8 Avaliação científica (DSR) | Pendente | — |

## Testes do superprompt (T-xxx)

| ID | Situação | Teste automatizado |
|---|---|---|
| T-001 | Aprovado | `test_T001_project_persists_after_connection_reset` |
| T-002 | Aprovado | `test_T002_other_org_user_gets_404_even_with_known_id`, `test_T002_org_detail_hidden_from_other_org` |
| T-003 | Aprovado | `test_T003_project_receives_seven_stages_starting_at_phase_1` |
| T-013 | Aprovado | `test_T013_auditor_reads_audit_but_cannot_modify_project` |
| T-014 | Aprovado | `test_T014_common_user_cannot_change_roles`, `test_audit_event_append_only_*` |
| T-022 | Aprovado | `test_T022_audit_records_project_creation_without_secrets` |
| T-025 | Aprovado | `test_T025_resubmitting_request_does_not_duplicate`, idempotência de papéis |
| T-004 | Aprovado | `test_T004_gate_blocked_with_pending_mandatory_requirement` |
| T-005 | Aprovado | `test_T005_evidence_in_review_or_rejected_does_not_satisfy` |
| T-006 | Aprovado | `test_T006_requester_cannot_approve_own_gate` |
| T-007 | Aprovado | `test_T007_approval_moves_phase_exactly_once` |
| T-008 | Aprovado | `test_T008_rejection_returns_stage_with_justification` |
| T-009 | Aprovado | `test_T009_change_after_approval_requires_revalidation` |
| T-011 | Aprovado | `test_T011_exception_rules_and_history` (+3 testes de exceção) |
| T-012 | Aprovado | `test_T012_concurrent_approvals_single_advance` (threads, conexões PostgreSQL distintas; 5/5 execuções) |
| T-015 | Aprovado | `test_download_scope_quarantine_and_audit`, `test_T015_export_restricted_and_scoped` |
| T-021 | Aprovado | `test_T021_invalid_uploads_are_refused_without_storing` (7 casos), `test_T021_oversized_upload_refused` |
| T-024 | Parcial | `test_T024_full_flow_reaches_operation` (fases 1→7 via gates); riscos/relatório: M4–M6 |
| T-010 | Aprovado | `test_T010_gate_blocked_by_untreated_critical_risk`, `test_T010_exception_can_cover_critical_risk_with_security_ack` |
| T-016 | Aprovado | `test_T016_costs_use_decimal_and_totals_are_exact` |
| T-017 | Aprovado | `test_T017_default_policy_classification` (12 casos), `test_T017_policy_configurable_per_organization` |
| T-026 | Aprovado | `test_T026_unauthorized_user_cannot_create_favorable_decision_via_api` |
| T-018 | Aprovado | `test_T018_dashboard_reflects_db_changes_and_filters` |
| T-019 | Aprovado | `test_T019_data_to_information_to_knowledge_cycle` |
| T-020 | Aprovado | `test_T020_csv_formula_neutralization` (8 casos), `test_T020_export_neutralizes_and_is_audited` |
| T-023 | Aprovado | `test_T023_api_requires_authentication`, `test_T023_api_scope_isolation` |
| T-027 | Aprovado | `test_T027_new_template_version_does_not_change_started_projects` |
| T-028 | Aprovado | `test_T028_metrics_report_no_data_instead_of_100`, `test_stage_progress_without_requirements_reports_no_data` |
| Demais | Pendentes | — |

## Pendências conhecidas
- MFA para perfis privilegiados: não implementado (obrigatório antes de produção institucional).
- Telas de administração de templates de ciclo de vida por organização: somente via admin técnico.
