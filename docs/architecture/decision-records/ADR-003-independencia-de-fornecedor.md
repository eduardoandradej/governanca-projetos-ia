# ADR-003 — Arquitetura independente de fornecedor

- **Status:** aceito (M0, 2026-11-02)
- **Contexto:** projetos de IA podem usar infraestrutura local, nuvem privada, pública, híbrida ou borda,
  com tecnologias variadas (Kubernetes, OpenShift, serviços gerenciados, componentes open source).
- **Decisão:** a abordagem de implantação é um campo enumerado neutro; tecnologias/fornecedores são
  **metadados opcionais** (`Project.technology_metadata`, JSONB validado: até 20 pares texto→texto).
  Nenhuma regra de negócio depende de marca. Integrações futuras usarão interfaces/adaptadores com
  implementação `NoOp` explícita — sem simular integrações ativas.
- **Consequências:** o MVP é utilizável com qualquer pilha; indicadores podem ser filtrados por abordagem
  de implantação, mas não por fornecedor, de forma estruturada.
