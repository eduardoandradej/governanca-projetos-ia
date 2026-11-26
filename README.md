<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/marca/trajetoria-nome-negativo.svg">
    <img alt="TrajetórIA" src="docs/marca/trajetoria-nome.svg" width="320">
  </picture>
</p>

# TrajetórIA — Plataforma Integrada de Governança e Gestão de Projetos de Inteligência Artificial

<p align="left">
  <img alt="IFRJ: Pós-Graduação em Gestão de Projetos e Negócios em TI" src="https://img.shields.io/badge/IFRJ-P%C3%B3s--Gradua%C3%A7%C3%A3o_em_Gest%C3%A3o_de_Projetos_e_Neg%C3%B3cios_em_TI-0B1F3A?style=for-the-badge"> <img alt="I Mostra: 2026" src="https://img.shields.io/badge/I_Mostra-2026-1F5FA8?style=for-the-badge"> <img alt="Eixo: Governança de TI e Gestão de Projetos" src="https://img.shields.io/badge/Eixo-Governan%C3%A7a_de_TI_e_Gest%C3%A3o_de_Projetos-5F6B7A?style=for-the-badge"><br>
  <img alt="Python: 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"> <img alt="Django: 5.2 LTS" src="https://img.shields.io/badge/Django-5.2_LTS-0B1F3A?style=for-the-badge&logo=django&logoColor=white"> <img alt="PostgreSQL: 16" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"> <img alt="HTMX: 2" src="https://img.shields.io/badge/HTMX-2-3366CC?style=for-the-badge&logo=htmx&logoColor=white"> <img alt="Bootstrap: 5" src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white"><br>
  <img alt="testes: 142 aprovados" src="https://img.shields.io/badge/testes-142_aprovados-1F5FA8?style=for-the-badge&logo=pytest&logoColor=white"> <img alt="lint: ruff" src="https://img.shields.io/badge/lint-ruff-111418?style=for-the-badge&logo=ruff&logoColor=white"> <img alt="deploy: AWS EC2 · Ubuntu" src="https://img.shields.io/badge/deploy-AWS_EC2_%C2%B7_Ubuntu-8A5A00?style=for-the-badge&logo=ubuntu&logoColor=white"> <img alt="licença: Apache 2.0" src="https://img.shields.io/badge/licen%C3%A7a-Apache_2.0-B42318?style=for-the-badge&logo=apache&logoColor=white"><br>
  <img alt="COBIT: 2019" src="https://img.shields.io/badge/COBIT-2019-0B1F3A?style=for-the-badge"> <img alt="PMBOK: 8ª ed." src="https://img.shields.io/badge/PMBOK-8%C2%AA_ed.-1F5FA8?style=for-the-badge"> <img alt="método: Design Science Research" src="https://img.shields.io/badge/m%C3%A9todo-Design_Science_Research-5F6B7A?style=for-the-badge"> <img alt="IA: responsável" src="https://img.shields.io/badge/IA-respons%C3%A1vel-6E3FA3?style=for-the-badge"><br>
</p>

*Governança para orientar. Inteligência para transformar.*

O nome une **Trajetória** (o percurso governado de cada projeto, da prova de conceito à produção, fase a fase e
gate a gate) e **IA** (a inteligência artificial que é objeto desse percurso).

Identificação técnica: `APP_SHORT_NAME = "TrajetórIA"` (configurável por variável de ambiente, assim como
`APP_FULL_NAME` e `APP_TAGLINE`).

MVP acadêmico (IFRJ · Pós-Graduação em Gestão de Projetos e Negócios em TI; I Mostra de Gestão de Projetos,
Governança e Gerenciamento de Serviços de TI · 2026; eixo Governança de TI e Gestão de Projetos) que coordena o **projeto de implantação**
de plataformas corporativas de IA, do caso de negócio ao aceite operacional e à melhoria contínua.
A aplicação **não** executa treinamento/inferência nem substitui Kubernetes, OpenShift, Ansible, GitLab ou
ferramentas de MLOps: é uma camada independente de fornecedor para responsabilidades, fases, riscos,
evidências, aprovações, decisões e conhecimento gerencial.

> Situação atual: MVP funcional, com **142 testes automatizados aprovados em PostgreSQL** e uma instância de
> demonstração no ar (AWS EC2, Ubuntu 24.04).

Referenciais: COBIT 2019 (com o white paper ISACA, *Leveraging COBIT for Effective AI System Governance*, 2025) e PMI
PMBOK Guide 8ª ed. (2025), incluindo o Apêndice X3 (IA). A matriz de rastreabilidade pode ser gerada com
`manage.py export_traceability`.

## Demonstração online

Endereço: **https://18-226-188-222.sslip.io** (dados fictícios; ambiente de demonstração).

| Usuário | Perfil |
|---|---|
| `demo.gerente` | Gerente de projeto |
| `demo.aprovador` | Aprovador de gate |
| `demo.seguranca` | Segurança e conformidade |
| `demo.patrocinio` | Patrocinador |
| `demo.portfolio` | Gestor de portfólio |
| `demo.tecnico` | Executor técnico |
| `demo.auditor` | Auditor |
| `demo.leitor` | Leitor |
| `demo.admin` | Administrador organizacional |
| `demo.beta.gerente` | Gerente em outra organização (mostra o isolamento entre organizações) |

A senha de demonstração é fornecida pela equipe aos avaliadores e não fica publicada aqui, porque o repositório é
público. O roteiro com o que mostrar em cada perfil está em
[`docs/demonstracao/roteiro-de-acesso.pdf`](docs/demonstracao/roteiro-de-acesso.pdf).

## Documentação

- [Manual do Usuário](docs/manuais/manual-do-usuario.pdf): conceitos, perfis e passo a passo ilustrado de cada funcionalidade.
- [Manual de Administração e Suporte](docs/manuais/manual-de-administracao-e-suporte.pdf): usuários e papéis, configuração, backup, monitoramento e atendimento.
- [Manual de Implementação](docs/manuais/manual-de-implementacao.pdf): arquitetura, código, testes, instalação, extensão e plano de implantação.
- [Guia de implantação na AWS](docs/operacao/guia-implantacao-aws-ubuntu-24.04.pdf): passo a passo para EC2 com Ubuntu 24.04.

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
organização/projeto e trilha de auditoria append-only.

## Instalação em máquina limpa (Ubuntu 24.04)

```bash
sudo apt install -y python3.12 python3.12-venv postgresql-16
```

```bash
git clone https://github.com/eduardoandradej/governanca-projetos-ia.git govia && cd govia
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
scripts/            banco, testes, backup e verificação de restauração
docs/operacao/      implantação, backup/restauração e solução de problemas
```

## Operação

- Implantação (Ubuntu + Nginx + Gunicorn + systemd): [`docs/operacao/deploy.md`](docs/operacao/deploy.md)
- Backup e restauração: [`docs/operacao/backup-restore.md`](docs/operacao/backup-restore.md)
- Solução de problemas: [`docs/operacao/troubleshooting.md`](docs/operacao/troubleshooting.md)
- API REST: `/api/v1/` (autenticação por sessão; mesmas permissões das telas).
- Dados de demonstração (`seed_demo`): 3 organizações fictícias e 9 projetos, oito deles parados em situações da
  dinâmica de avaliação (inclusive dois casos inspirados em projetos reais e anonimizados). Nunca usar em produção.

## Limitações

MVP de laboratório com dados sintéticos. Não está pronto para produção sensível: MFA, varredura de
malware de anexos e avaliação de segurança independente ainda não foram realizados. Associações a COBIT
2019 e PMBOK são interpretação da equipe, não certificação de conformidade.
