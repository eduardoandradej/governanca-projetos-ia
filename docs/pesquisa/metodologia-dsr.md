# Metodologia — Design Science Research

Pesquisa aplicada, de desenvolvimento de solução, conduzida segundo as seis atividades de Peffers et al. (2007)
(referência a verificar no original antes de citar):

| Atividade DSR | Como foi realizada | Artefatos |
|---|---|---|
| 1. Problema e motivação | Contexto do trabalho acadêmico e literatura de referência (ISACA 2025; PMBOK 8 X3) | `problema-objetivos.md` |
| 2. Objetivos da solução | O1–O6 e critérios de sucesso definidos antes da avaliação | `protocolo-avaliacao.md` |
| 3. Projeto e desenvolvimento | Incrementos M0–M8 (monólito Django/PostgreSQL), cada um com modelo, migração, regra, tela/API, autorização, auditoria, testes e documentação | código, ADRs, `status-implementacao.md` |
| 4. Demonstração | Roteiro reprodutível com dados sintéticos executado em navegador real (Playwright/Chromium) | `docs/demo/`, `docs/evidencias/m8/` |
| 5. Avaliação | Testes automatizados (140 em 06/11/2026) em PostgreSQL + roteiro E2E + verificações de segurança/operação | `resultados-testes.md` |
| 6. Comunicação | Subsídios para artigo de 5 páginas | `subsidios-artigo.md` |

**Natureza da avaliação.** Funcional, em cenário **sintético e controlado** (laboratório). Não é estudo de caso em
organização real, não é experimento com usuários e não mede ganho de produtividade. Efetividade organizacional
permanece para pesquisa futura.
