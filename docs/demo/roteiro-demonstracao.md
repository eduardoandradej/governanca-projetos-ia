# Roteiro de demonstração (dados sintéticos)

Preparação (banco isolado de demonstração; nunca em produção):

```bash
createdb govia_demo
```

```bash
DB_NAME=govia_demo .venv/bin/python manage.py migrate
```

```bash
DB_NAME=govia_demo DEMO_PASSWORD='defina-localmente' .venv/bin/python manage.py seed_demo --confirm-demo
```

```bash
DB_NAME=govia_demo .venv/bin/python manage.py runserver
```

Execução automática do roteiro (Playwright; senha lida de arquivo local, não versionado):

```bash
NODE_PATH=$(npm root -g) node scripts/demo_e2e.js /caminho/senha.txt docs/evidencias/m8
```

| # | Usuário | Ação | Resultado esperado |
|---|---|---|---|
| 1 | demo.gerente | Abrir IA-2026-01, fase 1 | Fase 1 em andamento, 1/6 requisitos validados |
| 2 | demo.gerente | Solicitar passagem | Recusada, com a lista exata de bloqueios |
| 3 | demo.aprovador / demo.seguranca | Aprovar evidência; validar requisitos atendidos pelo gerente | 6/6 validados (segregação) |
| 4 | demo.gerente | Nova solicitação; tratar R-001 | Bloqueio por risco crítico; tratamento registrado |
| 5 | demo.gerente → demo.aprovador | Solicitar e aprovar | Fase 1 aprovada; fase 2 iniciada |
| 6 | demo.patrocinio | Aba Custos | Orçamento × realizado (Decimal) |
| 7 | demo.gerente | Visão geral, ficha K02 | KPIs do PostgreSQL com numerador/denominador |
| 8 | gerente → patrocínio → gestor de portfólio | Revisar e aprovar insight I02; registrar e aprovar lição | Conhecimento aprovado por humanos distintos |
| 9 | demo.auditor | Auditoria filtrada por "gate" | Eventos com ator, horário e resultado |
| 10 | demo.gerente | Exportar CSV | Arquivo neutralizado, registrado em ExportRecord |
| — | demo.beta.gerente | URL do projeto da Alfa | HTTP 404 |

Execução real registrada em `docs/evidencias/m8/roteiro-log.txt`.
