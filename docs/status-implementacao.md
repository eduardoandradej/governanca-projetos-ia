# Status da implementação

Atualizado a cada incremento. "Concluído" = implementado **e** coberto por teste executado com sucesso.

| Incremento | Situação | Evidência |
|---|---|---|
| M0 Descoberta e desenho | Concluído | ADR-001..004, `docs/architecture/`, este arquivo |
| M1 Fundação (auth, organizações, RBAC, auditoria, layout, seed) | Concluído | `apps/accounts`, `apps/organizations`, `apps/auditlog`; testes `test_auth.py`, `test_rbac.py` |
| M2 Projetos e ciclo de vida | Concluído | `apps/projects`, `apps/lifecycle`; testes `test_projects.py`, `test_lifecycle.py`; capturas `docs/evidencias/m2/` |
| M3 Governança e gates | Pendente | — |
| M4 Riscos, custos e decisões | Pendente | — |
| M5 Dados → informação → conhecimento | Pendente | — |
| M6 Interface completa e API | Pendente | — |
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
| T-025 | Parcial | idempotência de concessão de papel (`test_org_admin_assigns_and_revokes_role_with_history`) |
| T-027 | Aprovado | `test_T027_new_template_version_does_not_change_started_projects` |
| T-028 | Parcial | `test_stage_progress_without_requirements_reports_no_data` |
| Demais | Pendentes | — |

## Pendências conhecidas
- MFA para perfis privilegiados: não implementado (obrigatório antes de produção institucional).
- Telas de administração de templates de ciclo de vida por organização: somente via admin técnico.
- Reabertura de projeto ainda não exige vínculo a `DecisionRecord` (virá no M4).
