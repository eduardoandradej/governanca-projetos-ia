# Modelo de ameaças e controles (resumo, referência OWASP ASVS 5.0 — não verificado formalmente)

| Ameaça | Controle implementado | Evidência de teste |
|---|---|---|
| IDOR / acesso entre organizações | `get_project_or_404` + RBAC em views, serviços, API, downloads e consultas analíticas; 404 fora do escopo | `test_T002_*`, `test_T023_*`, `test_download_scope_quarantine_and_audit`, `test_T015_*` |
| Escalada de privilégio | Matriz explícita; ninguém concede papel a si; admin técnico sem direitos de negócio | `test_no_self_elevation_*`, `test_platform_admin_has_no_implicit_business_rights` |
| Bypass de gate por URL/API/concorrência | Regras no serviço; `select_for_update`; restrição única de decisão | `test_direct_post_by_unauthorized_user_is_blocked`, `test_T012_*` |
| Força bruta | Bloqueio por usuário (5/15 min) e por IP | `test_brute_force_lock_blocks_even_correct_password` |
| CSRF | Middleware Django; API por sessão exige token | `test_api_write_requires_csrf_for_session` |
| XSS | Autoescape dos templates; sem `safe` em conteúdo de usuário; download com CSP sandbox | revisão de código |
| SQL injection | ORM parametrizado; SQL bruto só em migration e teste | revisão de código |
| Upload malicioso | Lista de extensões, assinatura de conteúdo, recusa de executável/compactado, limite 10 MB, quarentena, armazenamento privado 0600 | `test_T021_*` |
| CSV injection | Neutralização de prefixos de fórmula | `test_T020_*` |
| Adulteração da auditoria | Append-only no modelo e gatilho PostgreSQL | `test_audit_event_append_only_*` |
| Vazamento em logs | Sanitização de chaves sensíveis; sem conteúdo de documentos | `test_T022_*`, `test_login_failure_is_audited_without_password` |
| Dependências vulneráveis | `pip-audit` no M7: DRF 3.16.1 (5 CVEs) atualizado para 3.18.3; resultado final sem vulnerabilidades conhecidas | `docs/pesquisa/resultados-testes.md` |
| Segredos no repositório | `.gitignore`, `.env` fora do Git, gitleaks em CI | workflow `secret-scan.yml` |
