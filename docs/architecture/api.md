# API REST v1

Base: `/api/v1/`. Autenticação por sessão Django (mesma origem; escrita exige token CSRF). Paginação
`?page=` (25 itens). Limitação: 600 req/h por usuário autenticado, 30 req/h anônimo. Toda resposta é filtrada pelo
escopo do usuário (mesma política RBAC das telas); objeto fora do escopo → **404**.

| Método | Endpoint | Descrição | Filtros |
|---|---|---|---|
| GET | `/api/v1/projetos/` | Projetos visíveis | `status`, `implantacao`, `plataforma`, `ordering` (code, due_date, updated_at, com `-`) |
| GET | `/api/v1/projetos/{id}/` | Detalhe com fase corrente | — |
| GET | `/api/v1/projetos/{id}/stages/` | Sete fases e estados | — |
| GET/POST | `/api/v1/projetos/{id}/decisions/` | Lista/propõe decisão (exige `decision.record`) | — |
| GET | `/api/v1/decisoes/{id}/` | Decisão | — |
| POST | `/api/v1/decisoes/{id}/decide/` | Parecer `{"approve": true, "note": "..."}` (exige `decision.approve`; proponente não aprova) | — |
| GET | `/api/v1/riscos/` | Riscos | `nivel` |
| GET | `/api/v1/indicadores/` | 12 KPIs com numerador, denominador e linhagem | `organizacao`, `projeto` |

Erros: 401/403 (sem autenticação/permissão), 404 (fora do escopo), 400 (validação, corpo com mensagens).

Exemplo (sem segredos):

```bash
curl -b cookies.txt https://govia.exemplo.local/api/v1/indicadores/?organizacao=<uuid>
```

Exportações CSV (telas): `/inteligencia/exportar/projetos.csv` (`export.data`) e `/auditoria/exportar.csv`
(`audit.view`). Células iniciadas por `= + - @ | % TAB CR LF` são prefixadas com `'` (proteção contra injeção de fórmulas);
cada exportação gera `ExportRecord` e evento `export.csv`.
