# Catálogo de regras de negócio (RN)

Situação: **Implementada** = código + teste automatizado executado com sucesso; **Parcial** = parte implementada
(detalhe na coluna); **Pendente** = ainda não implementada. Este catálogo é atualizado a cada incremento.

| ID | Regra | Implementação | Testes | Situação |
|---|---|---|---|---|
| RN-001 | Projeto possui organização, patrocinador, gerente, finalidade e código único por organização | `projects.services.create_project`; `UniqueConstraint(organization, code)` | `test_code_unique_per_organization_only`, `test_required_fields_and_people_from_same_org` | Implementada |
| RN-002 | Acesso definido por escopo organizacional/projeto, no servidor | `organizations.rbac` (`has_perm`, `require_perm`, `visible_project_filter`); `core.http.get_project_or_404` | `test_permission_matrix_scoped_by_organization`, `test_project_scoped_role_only_applies_to_that_project`, `test_T002_*` | Implementada |
| RN-003 | Fluxo padrão de 7 fases sequencial e versionado | `lifecycle.default_template` (v1 e v2 como dado), `instantiate_lifecycle`, `STAGE_TRANSITIONS`, avanço só por gate | `test_T003_*`, `test_sequential_progression_enforced`, `test_T024_full_flow_reaches_operation` | Implementada |
| RN-004 | Gate não avança com requisito obrigatório pendente | `governance.services.evaluate` na solicitação e na aprovação | `test_T004_gate_blocked_with_pending_mandatory_requirement` | Implementada |
| RN-005 | Evidência em revisão/rejeitada não satisfaz exigência | `evidence.services.requirement_has_approved_evidence` | `test_T005_evidence_in_review_or_rejected_does_not_satisfy` | Implementada |
| RN-006 | Aprovador ≠ solicitante quando há segregação | `approve_gate`/`reject_gate`; também requisito (quem atende ≠ valida) e evidência (quem envia ≠ revisa) | `test_T006_requester_cannot_approve_own_gate`, `test_review_segregation_and_quarantine` | Implementada |
| RN-007 | Parecer com autor, timestamp, justificativa e versão | `GateDecision` (request_number + snapshot de requisitos com versões) | `test_T007_approval_moves_phase_exactly_once` | Implementada |
| RN-008 | Risco crítico não tratado impede passagem | `risks.services.untreated_critical_risks` (crítico, não aceito/encerrado, sem tratamento ativo) usado em `governance.evaluate`; exceção formal com ciência de segurança | `test_T010_gate_blocked_by_untreated_critical_risk`, `test_T010_exception_can_cover_critical_risk_with_security_ack` | Implementada |
| RN-009 | Exceção exige justificativa, validade, responsável e aceite de risco | `grant_exception` (≤ 180 dias, nunca legal, ciência de segurança em projetos confidenciais), revogação lógica | `test_T011_*`, `test_exception_never_applies_to_legal_requirement`, `test_expired_exception_does_not_unblock`, `test_confidential_project_exception_requires_security_ack` | Implementada |
| RN-010 | Mudança após aprovação força revalidação | `flag_revalidation` (requisito ou evidência alterada/arquivada) bloqueia gate seguinte até `revalidate_gate` | `test_T009_change_after_approval_requires_revalidation`, `test_requirement_change_after_approval_flags_revalidation` | Implementada |
| RN-011 | Projeto encerrado/cancelado não avança nem é alterado silenciosamente | `ensure_project_writable`; `change_status` (reabertura exige papel + `DecisionRecord` aprovado de tema reabertura) | `test_RN011_*`, `test_closed_project_blocks_requirement_and_task_changes` | Implementada |
| RN-012 | Métricas de registros persistidos com período/escopo | `analytics.metrics` (12 KPIs; `None` sem denominador; linhagem), escopo por `scoped_projects` | `test_T018_*`, `test_T028_*`, `test_cost_and_overdue_metrics_exact` | Implementada |
| RN-013 | Insights preservam regra, entradas, origem e revisão humana | `Insight` (regra, parâmetros, dados de sustentação, fingerprint), `InsightReview`, revisor ≠ aprovador | `test_T019_data_to_information_to_knowledge_cycle` | Implementada |
| RN-014 | Exportação autorizada, filtrada, sanitizada e auditada | `core.exports.csv_response` (neutralização, `ExportRecord`, auditoria); `export.data`/`audit.view` | `test_T020_*`, `test_T015_export_restricted_and_scoped`, `test_audit_export_only_for_auditors` | Implementada |
| RN-015 | Alteração de papéis registrada, sem autoelevação | `organizations.services.assign_role/revoke_role` | `test_no_self_elevation_even_for_org_admin`, `test_T014_*`, `test_org_admin_assigns_and_revokes_role_with_history` | Implementada |
| RN-016 | Custos Decimal com moeda e datas consistentes | `CostEntry` Decimal(14,2) + CHECK > 0; `add_cost` recusa float, usa moeda do projeto | `test_T016_costs_use_decimal_and_totals_are_exact`, `test_costs_reject_float_negative_and_unauthorized` | Implementada |
| RN-017 | Anexos sem URL pública nem acesso sem permissão | `PRIVATE_MEDIA_ROOT` (0600, nome aleatório), `authorize_download`, quarentena | `test_download_scope_quarantine_and_audit`, `test_valid_upload_stored_privately_with_hash` | Implementada |
| RN-018 | Dados classificados não vão para base pública sem autorização | `approve_lesson` exige justificativa para divulgar lição de projeto confidencial/restrito; `visible_lessons` nunca cruza organizações | `test_RN018_classified_lesson_needs_disclosure_and_never_crosses_orgs` | Implementada |
| RN-019 | Decisões e evidências aprovadas versionadas | `EvidenceVersion`; `revise_decision` cria nova versão e só substitui a anterior quando aprovada | `test_new_version_keeps_history`, `test_decision_lifecycle_versioning_and_segregation` | Implementada |
| RN-020 | Repetição de solicitação de gate não duplica decisões | Idempotência em `request_gate`; `UniqueConstraint` de decisão final por solicitação; `select_for_update` | `test_T025_resubmitting_request_does_not_duplicate`, `test_T012_concurrent_approvals_single_advance` | Implementada |
| RN-021 | Vínculos multiorganização validados em cada operação | `_check_people_in_org`, validações de portfólio, equipe, fase e projeto nos serviços | `test_required_fields_and_people_from_same_org`, `test_cannot_assign_role_to_non_member_or_cross_org_project`, `test_task_assignment_restricted_to_project_scope` | Implementada (M1–M2) |
| RN-022 | Derivados de `seed_demo` explicitam que são demonstrativos | `is_demo` em organização, insight, snapshot e lição; avisos no painel, KPIs, insights e projeto | `test_RN022_demo_flag_propagates` | Implementada |

## Regras adicionais implementadas

| ID | Regra | Implementação | Testes |
|---|---|---|---|
| RN-023 | Bloqueio temporário de login após N falhas na janela (padrão 5/15 min, por usuário; 4N por IP) | `accounts.throttle`, `ThrottledAuthenticationForm` | `test_brute_force_lock_blocks_even_correct_password` |
| RN-024 | Atendimento de requisito exige registro textual verificável (≥ 10 caracteres) | `fulfill_requirement` | `test_fulfill_requires_verifiable_note_and_permission` |
| RN-025 | Tarefa só pode ser atribuída a quem tem papel ativo no escopo do projeto | `_validate_assignee` | `test_task_assignment_restricted_to_project_scope` |
| RN-026 | Tarefa com dependência aberta não pode ser concluída; dependência circular é recusada | `update_task_status`, `add_task_dependency` | `test_task_dependencies_block_completion_and_cycles` |
| RN-027 | Administrador técnico da plataforma não tem direito implícito de negócio | `rbac.PLATFORM_PERMISSIONS` | `test_platform_admin_has_no_implicit_business_rights` |
| RN-028 | Edição concorrente de projeto detectada por versão otimista | `update_project(expected_version=…)` | `test_update_tracks_diff_and_optimistic_version` |
| RN-029 | Upload aceita apenas PDF/PNG/JPEG/TXT ≤ 10 MB com assinatura coerente; executáveis/compactados recusados | `evidence.services.validate_upload` | `test_T021_*` |
| RN-030 | Arquivo enviado fica em quarentena até inspeção registrada por segurança/conformidade; não pode ser aprovado nem distribuído antes | `inspect_version`, `review_evidence`, `authorize_download` | `test_review_segregation_and_quarantine`, `test_download_scope_quarantine_and_audit` |
| RN-031 | Fase 7 (operação) não possui gate de saída; sua entrada exige aprovação do gate da fase 6 (aceite) | `StageTemplate.has_exit_gate`, `approve_gate` | `test_T024_full_flow_reaches_operation` |
| RN-032 | Classificação de risco por P×I com limiares configuráveis por organização (padrão: crítico ≥ 20, alto ≥ 12, médio ≥ 6) | `RiskPolicy`, `classify` | `test_T017_*` |
| RN-033 | Aceite de risco residual somente pelo patrocinador, com justificativa | `accept_residual` | `test_residual_acceptance_requires_sponsor` |
| RN-034 | Quem propõe uma decisão não a aprova | `decide` | `test_proposer_cannot_approve_own_decision` |
| RN-035 | Regras de insight são idempotentes: recálculo não duplica insight aberto para o mesmo alvo | `UniqueConstraint` parcial em `Insight.fingerprint` | `test_T019_*` |
| RN-036 | Linhagem só entre ativos da mesma organização e sem ciclos | `add_lineage`, `_reaches` | `test_T019_*`, `test_catalog_requires_permission_and_same_org` |
| RN-037 | Gate da fase 6 (template v3) exige os 8 fatores de uso responsável de IA tratados ou justificados, cada um com humano responsável (PMBOK 8 X3.3) | `assess_responsible_ai`, `responsible_ai_blockers` | `test_gate_6_requires_responsible_ai_assessment` |
