# Roadmap de integrações (nenhuma integração ativa no MVP)

O MVP **não** se conecta a GitLab/GitHub, Ansible, Kubernetes/OpenShift, observabilidade, S3/MinIO, data lake ou
serviços de IA. Existem apenas contratos (`apps/integrations/ports.py`) e o adaptador explícito `NoOpAdapter`, que
falha com `IntegrationDisabled` em vez de simular respostas. `IntegrationEndpoint` tem restrição de banco que impede
habilitação no MVP e guarda só a *referência* à credencial (nome de variável/cofre), nunca o segredo.

| Contrato | Uso futuro | Sistemas candidatos | Privilégio |
|---|---|---|---|
| `CiCdPort.get_job_status` | Registrar evidência de execução de pipeline e associar deployment a projeto | GitLab, GitHub Actions | leitura |
| `AutomationPort.get_run_status` | Evidência de provisionamento/configuração | Ansible Automation Platform, ansible-runner | leitura |
| `DeploymentPort.describe_deployment` | Confirmar entrada em produção (fase 6) | Kubernetes, Red Hat OpenShift | leitura |
| `CapacityCostPort.get_capacity_metrics` | Indicadores de capacidade de GPU e custo | Prometheus, billing de nuvem | leitura |
| (futuro) armazenamento | Anexos e catálogo em object storage | S3, MinIO | escrita restrita |

Regras para implementar um adaptador: somente leitura por padrão; credencial em cofre/variável protegida; timeouts e
tratamento de erro; toda chamada auditada; ações externas de escrita exigem aprovação explícita registrada.

## Data lake (extensão conceitual)

Ingestão (conectores) → zona bruta em S3/MinIO → qualidade e anonimização → catálogo e linhagem (já modelados em
`DataAsset`/`DataLineage`) → consumo por indicadores. Fora do escopo do MVP: nenhuma infraestrutura de data lake
ou pipeline de IA é implantada.
