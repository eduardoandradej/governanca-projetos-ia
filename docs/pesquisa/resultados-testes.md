# Resultados de testes efetivamente executados

## Rodada final — 2026-11-02

- Ambiente: container Ubuntu 24.04; Python 3.12.3; Django 5.2.18; djangorestframework 3.18.3; PostgreSQL 16.15;
  psycopg 3.2.13; pytest 9.2.0; pytest-django 4.14.0; Chromium/Playwright pré-instalados.
- Comando: `./scripts/test.sh` (ruff → `manage.py check` → migrações pendentes → pytest em `test_govia`).
- Resultado: **138 testes, 138 aprovados, 0 falhas** (≈ 39 s). Lint sem erros; nenhuma migração pendente.

| Arquivo | Testes |
|---|---:|
| accounts/test_auth.py | 8 |
| organizations/test_rbac.py | 14 |
| projects/test_projects.py | 12 |
| lifecycle/test_lifecycle.py | 10 |
| evidence/test_evidence.py | 15 |
| governance/test_gates.py | 19 |
| governance/test_concurrency.py | 1 (repetido 5×: 5/5) |
| risks/test_risks.py | 25 |
| analytics/test_dik.py | 12 |
| api/test_api_export.py | 19 |
| core/test_seed_demo.py | 3 |

### Avaliação por critério do protocolo

| Critério | Resultado observado | Situação |
|---|---|---|
| C1 | `test_T024_full_flow_reaches_operation`: 6 gates aprovados, fase 7 em andamento; E2E aprovou gate 1 pela interface | Atendido |
| C2 | Gate recusado com lista exata de bloqueios (requisitos, evidência, risco crítico) — teste e E2E passo 2/4a | Atendido |
| C3 | Autoaprovação recusada (gate, requisito, evidência, decisão, insight); API recusa decisão sem papel (403) | Atendido |
| C4 | Duas aprovações simultâneas: 1 sucesso, 1 `DomainError`; 1 decisão, 1 transição, 1 evento | Atendido |
| C5 | 404 para outra organização em telas, API, download e exportação; E2E: usuário Beta → HTTP 404 | Atendido |
| C6 | `UPDATE`/`DELETE` em `auditlog_auditevent` recusados pelo gatilho; negações preservadas após rollback | Atendido |
| C7 | K02 = 16,7% (1/6) recalculado após validação; insight I02 com parâmetros e IDs; lição aprovada | Atendido |
| C8 | 7 uploads maliciosos recusados sem gravar arquivo; 8 casos de CSV neutralizados | Atendido |
| C9 | 22 objetivos COBIT (105 mapeamentos, 52 citados no white paper ISACA) e 26 referências PMBOK 8 | Atendido |
| C10 | `check --deploy`: 1 aviso intencional (HSTS preload); `pip-audit`: 5 CVEs no DRF 3.16.1 → atualizado, 0 restantes; backup restaurado com contagens idênticas | Atendido (laboratório) |

### Defeitos reais encontrados e corrigidos pelos testes
1. Evento de negação apagado pelo rollback da transação (ADR-004).
2. Reenvio de solicitação de gate retornava erro em vez de ser idempotente (ordem das verificações).
3. Revalidação de gate bloqueava a si mesma ao reler o indicador do banco.
4. `SELECT … FOR UPDATE` com junção externa recusado pelo PostgreSQL ao revisar insight (bloqueio só da linha própria).
5. Dependência vulnerável (DRF 3.16.1).
6. Migração histórica quebraria em banco novo ao referenciar campo criado depois (corrigido antes do commit).

## Demonstração E2E (navegador real) — banco `govia_demo` com `seed_demo`

Script: `scripts/demo_e2e.js` (Playwright/Chromium). Log integral: `docs/evidencias/m8/roteiro-log.txt`; capturas
`docs/evidencias/m8/*.png`; CSV exportado `10-exportacao-projetos.csv`.

| Passo | Resultado observado |
|---|---|
| 1 | Projeto IA-2026-01 na fase 1 |
| 2 | Gate recusado: 5 requisitos pendentes, evidência F1-R1 ausente, risco crítico R-001 sem tratamento |
| 3 | Evidência aprovada pelo aprovador; 6/6 requisitos validados pela segurança (quem atendeu ≠ quem validou) |
| 4 | Gate ainda bloqueado só pelo risco crítico; tratamento registrado |
| 5 | Passagem solicitada pelo gerente e aprovada pelo aprovador; fase 2 iniciada |
| 6 | Custos: orçamento 850.000,00; realizado 165.000,00; execução 19,4% |
| 7 | K02 = 0,0% (0/11) após avanço — denominador reflete as fases correntes dos 2 projetos |
| 8 | Insight I02 ("2 riscos… R-001, R-003; limite 2") revisado pelo gerente, aprovado pelo patrocinador; lição aprovada pelo gestor de portfólio |
| 9 | 4 eventos de gate visíveis ao auditor |
| 10 | CSV com cabeçalho e 2 projetos da Alfa (sem projeto da Beta) |
| Isolamento | Usuário da Beta no projeto da Alfa → HTTP 404 |

Rodadas anteriores (M2: 44 testes; M3: 79; M4: 104; M5: 116; M6: 135) estão nos commits correspondentes.
