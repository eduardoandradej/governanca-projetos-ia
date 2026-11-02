# Catálogo de regras de negócio (RN)

Situação: **Implementada** = código + teste automatizado executado com sucesso; **Parcial** = parte implementada
(detalhe na coluna); **Pendente** = ainda não implementada. Este catálogo é atualizado a cada incremento.

| ID | Regra | Implementação | Testes | Situação |
|---|---|---|---|---|
| RN-001 | Projeto possui organização, patrocinador, gerente, finalidade e código único por organização | `projects.services.create_project`; `UniqueConstraint(organization, code)` | `test_code_unique_per_organization_only`, `test_required_fields_and_people_from_same_org` | Implementada |
| RN-002 | Acesso definido por escopo organizacional/projeto, no servidor | `organizations.rbac` (`has_perm`, `require_perm`, `visible_project_filter`); `core.http.get_project_or_404` | `test_permission_matrix_scoped_by_organization`, `test_project_scoped_role_only_applies_to_that_project`, `test_T002_*` | Implementada |
| RN-003 | Fluxo padrão de 7 fases sequencial e versionado | `lifecycle.default_template` (dado em migration), `instantiate_lifecycle`, máquina de estados `STAGE_TRANSITIONS` | `test_T003_*`, `test_stage_state_machine_rejects_invalid_transition` | Implementada (avanço por gate: M3) |
| RN-004 | Gate não avança com requisito obrigatório pendente | — | — | Pendente (M3) |
| RN-005 | Evidência em revisão/rejeitada não satisfaz exigência | — | — | Pendente (M3) |
| RN-006 | Aprovador ≠ solicitante quando há segregação | Já aplicada na validação de requisito (quem atende ≠ quem valida) | `test_validation_requires_segregation_and_comment` | Parcial (gate: M3) |
| RN-007 | Parecer com autor, timestamp, justificativa e versão | `RequirementValidation` (versão do requisito) | `test_validation_requires_segregation_and_comment` | Parcial (gate: M3) |
| RN-008 | Risco crítico não tratado impede passagem | — | — | Pendente (M3/M4) |
| RN-009 | Exceção exige justificativa, validade, responsável e aceite de risco | — | — | Pendente (M3) |
| RN-010 | Mudança após aprovação força revalidação | Gancho `_flag_revalidation_if_approved` em `fulfill_requirement` | — | Parcial (M3) |
| RN-011 | Projeto encerrado/cancelado não avança nem é alterado silenciosamente | `ensure_project_writable`; `update_project`; `change_status` (reabertura exige papel e justificativa) | `test_RN011_*`, `test_closed_project_blocks_requirement_and_task_changes` | Implementada (vínculo a DecisionRecord: M4) |
| RN-012 | Métricas de registros persistidos com período/escopo | `stage_progress` retorna `None` sem denominador | `test_stage_progress_without_requirements_reports_no_data` | Parcial (M5) |
| RN-013 | Insights preservam regra, entradas e revisão humana | — | — | Pendente (M5) |
| RN-014 | Exportação autorizada, filtrada, sanitizada e auditada | Modelo `ExportRecord` | — | Pendente (M6) |
| RN-015 | Alteração de papéis registrada, sem autoelevação | `organizations.services.assign_role/revoke_role` | `test_no_self_elevation_even_for_org_admin`, `test_T014_*`, `test_org_admin_assigns_and_revokes_role_with_history` | Implementada |
| RN-016 | Custos Decimal com moeda e datas consistentes | `Project.planned_cost` Decimal + `CHECK >= 0`; `CHECK due_date >= start_date` | `test_T001_*` | Parcial (lançamentos: M4) |
| RN-017 | Anexos sem URL pública nem acesso sem permissão | `PRIVATE_MEDIA_ROOT` fora de `static/` | — | Pendente (M3) |
| RN-018 | Dados classificados não vão para base pública sem autorização | — | — | Pendente (M5) |
| RN-019 | Decisões e evidências aprovadas versionadas | — | — | Pendente (M3/M4) |
| RN-020 | Repetição de solicitação de gate não duplica decisões | — | — | Pendente (M3) |
| RN-021 | Vínculos multiorganização validados em cada operação | `_check_people_in_org`, validações de portfólio, equipe, fase e projeto nos serviços | `test_required_fields_and_people_from_same_org`, `test_cannot_assign_role_to_non_member_or_cross_org_project`, `test_task_assignment_restricted_to_project_scope` | Implementada (M1–M2) |
| RN-022 | Derivados de `seed_demo` explicitam que são demonstrativos | `Organization.is_demo`; aviso na tela do projeto | inspeção visual (`docs/evidencias/m2/04-projeto-detalhe.png`) | Parcial (indicadores: M5) |

## Regras adicionais implementadas

| ID | Regra | Implementação | Testes |
|---|---|---|---|
| RN-023 | Bloqueio temporário de login após N falhas na janela (padrão 5/15 min, por usuário; 4N por IP) | `accounts.throttle`, `ThrottledAuthenticationForm` | `test_brute_force_lock_blocks_even_correct_password` |
| RN-024 | Atendimento de requisito exige registro textual verificável (≥ 10 caracteres) | `fulfill_requirement` | `test_fulfill_requires_verifiable_note_and_permission` |
| RN-025 | Tarefa só pode ser atribuída a quem tem papel ativo no escopo do projeto | `_validate_assignee` | `test_task_assignment_restricted_to_project_scope` |
| RN-026 | Tarefa com dependência aberta não pode ser concluída; dependência circular é recusada | `update_task_status`, `add_task_dependency` | `test_task_dependencies_block_completion_and_cycles` |
| RN-027 | Administrador técnico da plataforma não tem direito implícito de negócio | `rbac.PLATFORM_PERMISSIONS` | `test_platform_admin_has_no_implicit_business_rights` |
| RN-028 | Edição concorrente de projeto detectada por versão otimista | `update_project(expected_version=…)` | `test_update_tracks_diff_and_optimistic_version` |
