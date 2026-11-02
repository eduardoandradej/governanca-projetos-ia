# Visão geral da arquitetura

## Contexto

```mermaid
flowchart LR
  U[Usuários: gerente, patrocinador, aprovador, segurança, auditor] -->|HTTPS| N[Nginx]
  N --> G[Gunicorn + Django 5.2]
  G --> P[(PostgreSQL 16)]
  G --> F[/Armazenamento privado de anexos/]
  G -. futuro, NoOp .-> X[GitLab · Ansible · Kubernetes/OpenShift · S3/MinIO · Observabilidade]
```

## Módulos (monólito modular)

| Módulo | Responsabilidade |
|---|---|
| core | mixins de modelo, correlação de requisições, healthz, carregamento com escopo (anti-IDOR), seed |
| accounts | usuário, autenticação, limitação de tentativas, senha |
| organizations | organizações, vínculos, papéis com escopo, matriz RBAC |
| auditlog | trilha append-only e serviço `record`; `atomic_service` |
| projects | portfólios, projetos, objetivos, histórico de status |
| lifecycle | templates versionados, fases, requisitos, validações, tarefas, equipes, RACI |

Regras críticas residem em `services.py` de cada módulo; views/APIs apenas validam entrada e chamam serviços.

## Modelo de dados (M1–M2)

```mermaid
erDiagram
  Organization ||--o{ Membership : possui
  User ||--o{ Membership : participa
  Organization ||--o{ RoleAssignment : concede
  User ||--o{ RoleAssignment : recebe
  Project |o--o{ RoleAssignment : "escopo opcional"
  Organization ||--o{ Portfolio : agrupa
  Organization ||--o{ Project : contém
  Portfolio |o--o{ Project : inclui
  Project ||--o{ ProjectStatusHistory : registra
  Project ||--o{ BusinessGoal : persegue
  LifecycleTemplate ||--o{ LifecycleTemplateVersion : versiona
  LifecycleTemplateVersion ||--o{ StageTemplate : define
  StageTemplate ||--o{ RequirementTemplate : exige
  LifecycleTemplateVersion ||--o{ Project : "instancia"
  Project ||--o{ StageInstance : "7 fases (snapshot)"
  StageInstance ||--o{ RequirementInstance : "requisitos (snapshot)"
  RequirementInstance ||--o{ RequirementValidation : validado
  RequirementInstance ||--o{ RaciAssignment : RACI
  StageInstance ||--o{ StageStatusHistory : registra
  StageInstance ||--o{ Task : contém
  Task ||--o{ TaskDependency : depende
  Organization ||--o{ Team : mantém
  AuditEvent }o..|| Organization : "organization_id (sem FK)"
```

## Máquina de estados da fase

```mermaid
stateDiagram-v2
  [*] --> not_started
  not_started --> in_progress
  in_progress --> submitted: gate solicitado
  submitted --> approved: gate aprovado
  submitted --> returned: gate rejeitado
  submitted --> in_progress: solicitação cancelada
  returned --> in_progress: retrabalho
  returned --> submitted: nova solicitação
  approved --> completed
  in_progress --> completed: fase 7 ao encerrar projeto
```
