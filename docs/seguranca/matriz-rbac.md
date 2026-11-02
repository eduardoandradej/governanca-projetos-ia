# Matriz RBAC (gerada automaticamente)

Gerada por `python manage.py export_rbac_matrix` a partir de `apps/organizations/rbac.py`.
Escopo: papel atribuído à organização inteira ou a um projeto específico; exige vínculo ativo.
Segregação de funções (solicitante ≠ aprovador; quem atende ≠ quem valida) é aplicada nos serviços.

| Permissão | Administrador organizacional | Gestor de portfólio | Patrocinador | Gerente de projeto | Executor técnico | Responsável por segurança/conformidade | Aprovador de gate | Auditor | Leitor |
|---|---|---|---|---|---|---|---|---|---|
| `analytics.view` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `audit.view` | ✔ |  |  |  |  | ✔ |  | ✔ |  |
| `cost.manage` |  | ✔ |  | ✔ |  |  |  |  |  |
| `data.manage` |  |  |  | ✔ | ✔ |  |  |  |  |
| `decision.approve` |  | ✔ | ✔ |  |  |  |  |  |  |
| `decision.record` |  | ✔ | ✔ | ✔ |  |  |  |  |  |
| `evidence.download` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |
| `evidence.inspect` |  |  |  |  |  | ✔ |  |  |  |
| `evidence.review` |  |  |  | ✔ |  | ✔ | ✔ |  |  |
| `evidence.upload` |  |  |  | ✔ | ✔ | ✔ |  |  |  |
| `export.data` | ✔ | ✔ | ✔ | ✔ |  |  |  | ✔ |  |
| `gate.approve` |  |  | ✔ |  |  |  | ✔ |  |  |
| `gate.exception.grant` | ✔ |  | ✔ |  |  |  |  |  |  |
| `gate.exception.security_ack` |  |  |  |  |  | ✔ |  |  |  |
| `gate.request` |  |  |  | ✔ |  |  |  |  |  |
| `governance.manage` | ✔ |  |  |  |  |  |  |  |  |
| `insight.review` |  | ✔ | ✔ | ✔ |  |  |  |  |  |
| `lesson.approve` |  | ✔ | ✔ |  |  |  |  |  |  |
| `lesson.manage` |  | ✔ |  | ✔ |  |  |  |  |  |
| `lifecycle.template_manage` | ✔ |  |  |  |  |  |  |  |  |
| `org.manage` | ✔ |  |  |  |  |  |  |  |  |
| `org.view` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `portfolio.manage` | ✔ | ✔ |  |  |  |  |  |  |  |
| `project.close` | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `project.create` | ✔ | ✔ |  | ✔ |  |  |  |  |  |
| `project.edit` | ✔ | ✔ |  | ✔ |  |  |  |  |  |
| `project.reopen` | ✔ |  | ✔ |  |  |  |  |  |  |
| `project.view` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `project.view_sensitive` | ✔ | ✔ | ✔ | ✔ |  | ✔ |  | ✔ |  |
| `requirement.fulfill` |  |  |  | ✔ | ✔ | ✔ |  |  |  |
| `requirement.validate` |  |  |  | ✔ |  | ✔ | ✔ |  |  |
| `risk.accept_residual` |  |  | ✔ |  |  |  |  |  |  |
| `risk.manage` |  |  |  | ✔ | ✔ | ✔ |  |  |  |
| `roles.manage` | ✔ |  |  |  |  |  |  |  |  |
| `stage.start` |  |  |  | ✔ |  |  |  |  |  |
| `task.manage` |  |  |  | ✔ | ✔ |  |  |  |  |
| `team.manage` | ✔ |  |  | ✔ |  |  |  |  |  |

## Administrador da plataforma (superusuário técnico)

Possui apenas: `org.view`, `platform.membership_manage`, `platform.org_create`, `roles.manage`.
Não aprova gates nem decisões de negócio e não lê projetos sem papel atribuído.
