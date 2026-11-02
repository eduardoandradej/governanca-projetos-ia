# ADR-002 — PostgreSQL 16 como banco principal e de testes

- **Status:** aceito (M0, 2026-11-02)
- **Contexto:** gates exigem integridade sob concorrência (`SELECT … FOR UPDATE`), restrições declarativas
  (`CHECK`, `UNIQUE` parcial) e trilha append-only protegida no banco.
- **Decisão:** PostgreSQL 16 em todos os ambientes, inclusive testes (banco `test_govia` criado pelo
  pytest-django). Um teste automático falha se a suíte rodar em outro motor. A trilha de auditoria é protegida por
  gatilho `BEFORE UPDATE OR DELETE` (migration `auditlog/0002`).
- **Consequências:** o usuário de banco de desenvolvimento precisa de `CREATEDB`. Em produção, recomenda-se
  revogar `TRUNCATE`/`DELETE` na tabela de auditoria para o usuário da aplicação. Limitação: um superusuário
  do PostgreSQL ainda pode desativar o gatilho; imutabilidade forte exige armazenamento externo WORM.
