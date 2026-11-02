# Resultados de testes efetivamente executados

Somente execuções reais são registradas aqui. Ambiente de cada rodada indicado.

## Rodada M2 — 2026-11-02

- Ambiente: Ubuntu 24.04 (container de desenvolvimento), Python 3.12.3, Django 5.2.18, PostgreSQL 16.15,
  psycopg 3.2.13, pytest 9.2.0, pytest-django 4.14.0.
- Banco: PostgreSQL de teste isolado `test_govia` (criado/destruído pelo pytest-django).
- Comando: `.venv/bin/pytest -v`
- Resultado: **44 testes, 44 aprovados, 0 falhas** (8,07 s).
- Defeito encontrado e corrigido durante a rodada: eventos de auditoria de negação eram desfeitos pelo
  rollback da transação (ver ADR-004). Teste que detectou: `test_no_self_elevation_even_for_org_admin`.

Teste de fumaça manual automatizado (Playwright + Chromium, servidor `runserver` local, dados de `seed_demo`):

| Passo | Resultado observado |
|---|---|
| GET /contas/entrar/ | 200 |
| Login demo.gerente | redirecionado para / |
| GET /, /projetos/, detalhe IA-2026-01, fase 1, Kanban | 200 em todas |
| Alterar status de tarefa via HTMX no Kanban | cartão atualizado para "Bloqueada" |
| demo.beta.gerente acessando projeto da Alfa por URL direta | **404** |

Capturas: `docs/evidencias/m2/*.png`.

<details><summary>Saída por teste</summary>

```
apps/accounts/tests/test_auth.py::test_login_success_is_audited PASSED
apps/accounts/tests/test_auth.py::test_login_failure_is_audited_without_password PASSED
apps/accounts/tests/test_auth.py::test_brute_force_lock_blocks_even_correct_password PASSED
apps/accounts/tests/test_auth.py::test_password_reset_sends_token_and_does_not_enumerate PASSED
apps/accounts/tests/test_auth.py::test_password_policy_rejects_short_password PASSED
apps/accounts/tests/test_auth.py::test_protected_pages_require_login PASSED
apps/accounts/tests/test_auth.py::test_healthz_checks_database PASSED
apps/accounts/tests/test_auth.py::test_logout_requires_post_and_is_audited PASSED
apps/lifecycle/tests/test_lifecycle.py::test_fulfill_requires_verifiable_note_and_permission PASSED
apps/lifecycle/tests/test_lifecycle.py::test_validation_requires_segregation_and_comment PASSED
apps/lifecycle/tests/test_lifecycle.py::test_stage_state_machine_rejects_invalid_transition PASSED
apps/lifecycle/tests/test_lifecycle.py::test_cannot_fulfill_requirement_of_not_started_stage PASSED
apps/lifecycle/tests/test_lifecycle.py::test_stage_progress_without_requirements_reports_no_data PASSED
apps/lifecycle/tests/test_lifecycle.py::test_task_assignment_restricted_to_project_scope PASSED
apps/lifecycle/tests/test_lifecycle.py::test_task_dependencies_block_completion_and_cycles PASSED
apps/lifecycle/tests/test_lifecycle.py::test_assignee_can_update_own_task_but_reader_cannot PASSED
apps/lifecycle/tests/test_lifecycle.py::test_task_status_via_htmx_and_requirement_via_web PASSED
apps/lifecycle/tests/test_lifecycle.py::test_closed_project_blocks_requirement_and_task_changes PASSED
apps/organizations/tests/test_rbac.py::test_permission_matrix_scoped_by_organization PASSED
apps/organizations/tests/test_rbac.py::test_unknown_permission_raises PASSED
apps/organizations/tests/test_rbac.py::test_suspended_membership_loses_access PASSED
apps/organizations/tests/test_rbac.py::test_project_scoped_role_only_applies_to_that_project PASSED
apps/organizations/tests/test_rbac.py::test_platform_admin_has_no_implicit_business_rights PASSED
apps/organizations/tests/test_rbac.py::test_T014_common_user_cannot_change_roles PASSED
apps/organizations/tests/test_rbac.py::test_no_self_elevation_even_for_org_admin PASSED
apps/organizations/tests/test_rbac.py::test_org_admin_assigns_and_revokes_role_with_history PASSED
apps/organizations/tests/test_rbac.py::test_cannot_assign_role_to_non_member_or_cross_org_project PASSED
apps/organizations/tests/test_rbac.py::test_T002_org_detail_hidden_from_other_org PASSED
apps/organizations/tests/test_rbac.py::test_audit_event_append_only_in_application PASSED
apps/organizations/tests/test_rbac.py::test_audit_event_append_only_in_database_trigger PASSED
apps/organizations/tests/test_rbac.py::test_T013_auditor_reads_audit_but_cannot_modify_project PASSED
apps/organizations/tests/test_rbac.py::test_audit_list_restricted_and_scoped PASSED
apps/projects/tests/test_projects.py::test_T003_project_receives_seven_stages_starting_at_phase_1 PASSED
apps/projects/tests/test_projects.py::test_code_unique_per_organization_only PASSED
apps/projects/tests/test_projects.py::test_required_fields_and_people_from_same_org PASSED
apps/projects/tests/test_projects.py::test_reader_cannot_create_project PASSED
apps/projects/tests/test_projects.py::test_T002_other_org_user_gets_404_even_with_known_id PASSED
apps/projects/tests/test_projects.py::test_project_views_render_for_member PASSED
apps/projects/tests/test_projects.py::test_create_project_via_web_form PASSED
apps/projects/tests/test_projects.py::test_T022_audit_records_project_creation_without_secrets PASSED
apps/projects/tests/test_projects.py::test_update_tracks_diff_and_optimistic_version PASSED
apps/projects/tests/test_projects.py::test_RN011_closed_project_is_read_only_and_reopen_requires_authority PASSED
apps/projects/tests/test_projects.py::test_T027_new_template_version_does_not_change_started_projects PASSED
apps/projects/tests/test_projects.py::test_T001_project_persists_after_connection_reset PASSED
============================== 44 passed in 8.07s ==============================
```
</details>
