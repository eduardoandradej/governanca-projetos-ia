# Changelog

## [Não publicado]

### Cenários da dinâmica de avaliação — 2026-11-06
- `seed_demo` cria um órgão público fictício (Secretaria Estadual Demonstrativa Gama) e 4 novos projetos (total de 6
  visíveis aos perfis demo): aquisição de GPUs, assistente ao cidadão com RAG, detecção de fraudes e visão
  computacional na borda, cada um parado numa situação descrita em `docs/demo/dinamica-cenarios.md`.
- Cenário GOV-2026-03 (controle de qualidade de laudos periciais com IA), inspirado em projeto real e anonimizado:
  formalização da parceria retida na assinatura do acordo; exceção a requisito legal recusada e auditada.
- Correção: valores monetários exibidos com separador de milhar (detalhe do projeto e custos). 142 testes.

### Pesquisa com profissionais, rodada 1 — 2026-11-06
- Template de ciclo de vida **v4** (migração `governance/0005`), com ajustes derivados da rodada 1 do questionário
  (n = 9 na análise principal): F1-R1 exige alternativas sem IA e justificativa para usar IA (A09); F2-R1 exige a
  fonte de financiamento da infraestrutura de produção (A02); novo F2-R6, avaliação preliminar de uso responsável de
  IA na fase 2 (A06). Projetos existentes permanecem na versão em que foram criados; v1–v3 descontinuadas.
- `docs/pesquisa/evolucao-orientada-pela-pesquisa.md`: resultados agregados, hipóteses e decisões de evolução.
- Identidade do produto: TrajetórIA. 140 testes.
- Rollback: `migrate governance 0004` não remove a v4 (RunPython sem reversão); para desfazer, reverter este commit
  em banco novo, ou marcar a v4 como `retired` e a v3 como `published`.

### M3–M8 + incrementos ISACA/PMBOK — 2026-11-02
- M3: evidências versionadas com quarentena e revisão segregada; Stage-Gates com bloqueios no servidor, segregação,
  exceções formais, revalidação e controle de concorrência; catálogo COBIT com base em ISACA (2025); template v2.
- M4: riscos 5×5 com categorias de risco de IA (ISACA fig. 5), custos Decimal, decisões versionadas; reabertura exige decisão.
- M5: catálogo/linhagem de dados, 12 KPIs com ficha técnica, 6 regras de insight com revisão humana, lições aprendidas.
- PMBOK 8: referências por seção/página, abordagem de desenvolvimento, estratégia de adoção de IA, avaliação de uso
  responsável de IA no gate 6 (template v3), KPIs tendência/resultado.
- M6: API v1, exportações CSV seguras e auditadas, integrações NoOp.
- M7: pip-audit (DRF 3.16.1 → 3.18.3), check --deploy, backup/restauração verificados, docs de implantação e segurança.
- M8: documentação DSR, protocolo, resultados e roteiro E2E executado em navegador; 138 testes.

### M0–M2 — 2026-11-02
- Base de segurança do repositório (.gitignore, SECURITY.md, CODEOWNERS, gitleaks).
- Projeto Django 5.2 + PostgreSQL 16; configurações por ambiente (dev/test/prod) via `.env`.
- Usuário próprio (UUID), login com limitação de tentativas, recuperação/alteração de senha, política de senha (≥ 12).
- Organizações, vínculos, papéis com escopo de organização/projeto, matriz RBAC explícita e exportável.
- Trilha de auditoria append-only (modelo + gatilho PostgreSQL), correlation_id, sanitização de dados sensíveis.
- Portfólios e projetos com histórico de status, versão otimista e metadados de tecnologia neutros.
- Template versionado de 7 fases (28 requisitos) instalado como dado; snapshot nas instâncias.
- Requisitos com atendimento verificável e validação segregada; máquina de estados das fases.
- Tarefas com dependências, Kanban/lista com HTMX, equipes e RACI (modelo).
- `seed_demo --confirm-demo`; 44 testes automatizados em PostgreSQL.
