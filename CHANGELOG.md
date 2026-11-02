# Changelog

## [Não publicado]

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
