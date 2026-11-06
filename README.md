# TrajetórIA — Plataforma Integrada de Governança e Gestão de Projetos de Inteligência Artificial

*Governança para orientar. Inteligência para transformar.*

O nome une **Trajetória** (o percurso governado de cada projeto, da prova de conceito à produção, fase a fase e
gate a gate) e **IA** (a inteligência artificial que é objeto desse percurso).

Identificação técnica: `APP_SHORT_NAME = "TrajetórIA"` (configurável por variável de ambiente, assim como
`APP_FULL_NAME` e `APP_TAGLINE`).

MVP acadêmico (IFRJ · Pós-Graduação em Gestão de Projetos e Negócios em TI; I Mostra de Gestão de Projetos,
Governança e Gerenciamento de Serviços de TI · 2026; eixo COBIT 2019, PMBOK e ágil) que coordena o **projeto de implantação**
de plataformas corporativas de IA, do caso de negócio ao aceite operacional e à melhoria contínua.
A aplicação **não** executa treinamento/inferência nem substitui Kubernetes, OpenShift, Ansible, GitLab ou
ferramentas de MLOps: é uma camada independente de fornecedor para responsabilidades, fases, riscos,
evidências, aprovações, decisões e conhecimento gerencial.

> Situação atual: incrementos M0–M8 concluídos em laboratório, com **142 testes automatizados aprovados em
> PostgreSQL** e roteiro de demonstração executado em navegador. Detalhes e pendências em
> [`docs/status-implementacao.md`](docs/status-implementacao.md).

Referenciais: COBIT 2019 (com o white paper ISACA, *Leveraging COBIT for Effective AI System Governance*, 2025) e PMI
PMBOK Guide 8ª ed. (2025), incluindo o Apêndice X3 (IA). Rastreabilidade em
[`docs/governanca/matriz-controles.md`](docs/governanca/matriz-controles.md).

## Autoria

Alunos: Eduardo Andrade de Jesus · Matheus Fernandes Cunha · Thais Gonçalves de Alencar  
Orientação: Prof. Dr. Ricardo Kneipp  
IFRJ · Pós-Graduação em Gestão de Projetos e Negócios em TI · I Mostra de Gestão de Projetos, Governança e
Gerenciamento de Serviços de TI · 2026

Título do trabalho: *Um modelo integrado de governança e gestão de projetos para implantação de plataformas
corporativas de IA*.

## Pilha

Python 3.12 · Django 5.2 LTS · PostgreSQL 16 · Django Templates + HTMX + Bootstrap 5 (arquivos locais, sem CDN)
· Django REST Framework (API, incremento M6) · pytest/pytest-django · ruff · Gunicorn + Nginx + systemd (deploy).

Arquitetura: monólito modular (`apps/`), serviços de domínio transacionais, RBAC com escopo de
organização/projeto e trilha de auditoria append-only. Ver [`docs/architecture/`](docs/architecture/).

## Instalação em máquina limpa (Ubuntu 24.04)

```bash
sudo apt install -y python3.12 python3.12-venv postgresql-16
```

```bash
git clone <url-do-repositorio> govia && cd govia
```

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.lock
```

```bash
cp .env.example .env && chmod 600 .env   # edite DJANGO_SECRET_KEY e DB_PASSWORD
```

```bash
set -a && . ./.env && set +a && ./scripts/setup_db.sh
```

```bash
.venv/bin/python manage.py migrate
```

```bash
.venv/bin/python manage.py createsuperuser   # administrador TÉCNICO da plataforma (senha digitada no prompt)
```

```bash
.venv/bin/python manage.py runserver
```

O administrador da plataforma **não** recebe acesso a projetos nem direito de aprovar gates: papéis de
negócio são concedidos por organização/projeto (tela *Organizações e papéis* ou `bootstrap_role`).

### Dados de demonstração (opcional, somente desenvolvimento)

```bash
.venv/bin/python manage.py seed_demo --confirm-demo
```

Cria organizações fictícias marcadas como demonstrativas, usuários `demo.*` com papéis distintos e projetos
sintéticos. A senha é gerada aleatoriamente e exibida uma única vez (ou defina `DEMO_PASSWORD` no ambiente).

## Testes

```bash
./scripts/test.sh
```

Executa `ruff`, `manage.py check`, verificação de migrações pendentes e `pytest` em um **PostgreSQL de teste
isolado** (`test_govia`), nunca SQLite. O usuário do banco precisa de `CREATEDB` no ambiente de desenvolvimento.

## Estrutura

```
apps/core           mixins, middleware de correlação, healthz, seed_demo
apps/accounts       usuário, login com limitação de tentativas, recuperação de senha
apps/organizations  organizações, vínculos, papéis com escopo, matriz RBAC
apps/auditlog       trilha append-only (modelo + gatilho PostgreSQL)
apps/projects       portfólios, projetos, histórico de status
apps/lifecycle      templates versionados, 7 fases, requisitos, validações, tarefas, equipes, RACI
apps/evidence       evidências versionadas, quarentena, revisão, download seguro
apps/governance     gates, decisões de gate, exceções, catálogo COBIT/PMBOK, uso responsável de IA
apps/risks          riscos 5×5, tratamentos, custos, decisões, ações
apps/analytics      catálogo/linhagem de dados, indicadores, insights, lições aprendidas
apps/api            API REST v1
apps/integrations   contratos de integração (NoOp)
deploy/             exemplos systemd e Nginx
docs/               arquitetura, requisitos, governança, dados, segurança, operação, demo, pesquisa, evidências
```

## Demonstração e operação

- Roteiro: [`docs/demo/roteiro-demonstracao.md`](docs/demo/roteiro-demonstracao.md) · Dinâmica com 7 situações: [`docs/demo/dinamica-cenarios.md`](docs/demo/dinamica-cenarios.md)
- Implantação: [`docs/operacao/deploy.md`](docs/operacao/deploy.md) · Backup: [`docs/operacao/backup-restore.md`](docs/operacao/backup-restore.md)
- API: [`docs/architecture/api.md`](docs/architecture/api.md)

## Limitações

MVP de laboratório com dados sintéticos. Não está pronto para produção sensível: MFA, varredura de
malware de anexos e avaliação de segurança independente ainda não foram realizados. Associações a COBIT
2019 e PMBOK são interpretação da equipe, não certificação de conformidade.
