# Protocolo de avaliação

Os critérios abaixo foram fixados **antes** da execução da avaliação, a partir do superprompt de especificação
(indicador de êxito e cenários T-001 a T-028). Um critério só é considerado atendido com teste executado e saída
observável.

| Critério | Objetivo | Evidência exigida | Limiar de sucesso |
|---|---|---|---|
| C1 Fluxo completo fase 1 → 7 | O1 | teste automatizado + roteiro E2E | fluxo concluído com gates aprovados |
| C2 Bloqueio sem requisito/evidência/risco tratado | O1 | T-004, T-005, T-010 | 100% dos cenários bloqueiam |
| C3 Segregação e autoridade | O2 | T-006, T-007, T-026 | nenhuma autoaprovação aceita |
| C4 Concorrência e idempotência | O1/O2 | T-012, T-025 | exatamente uma decisão e um avanço |
| C5 Isolamento e IDOR | O3 | T-002, T-015, T-023 + E2E | 0 acessos fora do escopo |
| C6 Auditoria íntegra | O2 | T-013, T-014, T-022 | UPDATE/DELETE recusados pelo banco |
| C7 D→I→K | O4 | T-018, T-019, T-028 | KPI correto, insight rastreável, lição aprovada |
| C8 Segurança de entrada/saída | O3 | T-020, T-021 | 100% dos casos maliciosos recusados/neutralizados |
| C9 Rastreabilidade COBIT/PMBOK | O5 | catálogo + página de rastreabilidade | cada requisito do template mapeado |
| C10 Instalação e operação | O6 | `check --deploy`, `pip-audit`, backup/restauração | sem erro bloqueante; restauração confere |

Procedimento: (1) `./scripts/test.sh` em PostgreSQL 16 de teste isolado; (2) teste de concorrência repetido 5 vezes;
(3) `seed_demo` em banco limpo `govia_demo` + `scripts/demo_e2e.js`; (4) verificações de M7. Resultados em
`resultados-testes.md`.
