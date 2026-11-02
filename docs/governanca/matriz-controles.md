# Matriz de controles e rastreabilidade (gerada automaticamente)

Gerada por `python manage.py export_traceability`. Associações são **interpretação da equipe**, exceto as
marcadas como *ISACA 2025* (citadas em ISACA, *Leveraging COBIT for Effective AI System Governance*, 2025,
com página). Não constitui certificação de conformidade com COBIT 2019 ou PMBOK.

Template vigente: **Ciclo padrão de implantação de plataforma de IA (7 fases) v3** — Interpretação da equipe: COBIT 2019; ISACA (2025) p. 11–16; PMI PMBOK Guide 8ª ed. (2025): 2.1, 2.7, 4.2, X3.

## 1. Objetivos COBIT 2019

| Objetivo | Fase de IA (ISACA) | IA confiável | Fonte / páginas | Requisitos (template vigente) | Funcionalidades |
|---|---|---|---|---|---|
| APO01 Managed I&T Management Framework | Desenvolvimento | Ética e integridade | ISACA 2025 p. 12 | F1-R5 ¹ | — |
| APO03 Managed Enterprise Architecture | Desenvolvimento | Disponibilidade | ISACA 2025 p. 15 | F3-R2 ¹ | — |
| APO04 Managed Innovation | Desenvolvimento | Transversal (partes interessadas) | ISACA 2025 p. 13, 15 | F7-R5 ¹ | — |
| APO11 Managed Quality | Desenvolvimento | Qualidade | ISACA 2025 p. 12, 13 | F4-R5 ¹, F5-R3 ¹ | — |
| APO12 Managed Risk | Desenvolvimento | Transversal (risco) | ISACA 2025 p. 13 | F2-R2 ¹, F2-R5 ¹, F5-R3, F5-R4, F7-R2 | Registro de riscos 5×5 com categorias de risco de IA (ISACA fig. 5) |
| APO14 Managed Data | Desenvolvimento | Segurança e privacidade | ISACA 2025 p. 13 | F1-R4, F2-R4 ¹, F4-R2 ¹ | Catálogo e linhagem de ativos de dados |
| BAI03 Managed Solutions Identification and Build | Implantação | Qualidade | ISACA 2025 p. 12, 14 | F4-R5 ¹, F5-R2 ¹, F5-R3 ¹, F6-R1 ¹ | — |
| BAI04 Managed Availability and Capacity | Implantação | Disponibilidade | ISACA 2025 p. 15 | F4-R1 ¹ | — |
| BAI06 Managed IT Changes | Implantação | Resiliência | ISACA 2025 p. 12 | F3-R4, F4-R1, F6-R4 ¹, F6-R6 ¹ | Revalidação obrigatória de gate após mudança em requisito/evidência aprovada |
| BAI07 Managed IT Change Acceptance and Transitioning | Implantação | — | Interpretação da equipe p. 9 | F6-R1, F6-R2, F6-R5 | — |
| BAI09 Managed Assets | Implantação | Segurança e privacidade | ISACA 2025 p. 12 | F4-R6 ¹ | — |
| BAI11 Managed Projects | Implantação | — | Interpretação da equipe p. 9 | F1-R2, F1-R6, F2-R1, F2-R3, F3-R1, F3-R2, F3-R3, F5-R1, F5-R2 | Ciclo de vida de 7 fases com Stage-Gates e tarefas |
| DSS04 Managed Continuity | Operação | Resiliência; Disponibilidade | Interpretação da equipe p. 9, 14 | F4-R3, F4-R4, F6-R3 | — |
| DSS05 Managed Security Services | Operação | Segurança e privacidade | ISACA 2025 p. 12 | F4-R3 ¹, F4-R6 ¹, F6-R2 ¹ | — |
| EDM01 Ensured Governance Framework Setting and Maintenance | Design | Transparência e honestidade; Ética e integridade | ISACA 2025 p. 12 | F1-R2 ¹, F1-R5 ¹, F3-R5 ¹, F3-R6 ¹, F5-R5 ¹, F6-R7 | RBAC com escopo e segregação de funções |
| EDM02 Ensured Benefits Delivery | Design | Ética e integridade | ISACA 2025 p. 12 | F1-R1, F1-R3, F1-R5 ¹ | Caso de negócio, objetivos e métricas de benefício do projeto |
| EDM03 Ensured Risk Optimization | Design | Transversal (risco) | ISACA 2025 p. 13 | F2-R2 ¹, F2-R5 ¹ | Bloqueio de gate por risco crítico não tratado |
| EDM05 Ensured Stakeholder Engagement | Design | Transversal (partes interessadas) | ISACA 2025 p. 13, 15 | F3-R3 ¹, F3-R5 ¹ | — |
| MEA01 Managed Performance and Conformance Monitoring | Monitoramento | Transversal (monitoramento) | ISACA 2025 p. 13 | F7-R1 ¹, F7-R3 | Indicadores com ficha técnica calculados do PostgreSQL |
| MEA02 Managed System of Internal Control | Monitoramento | Transversal (monitoramento) | ISACA 2025 p. 13 | — | Trilha de auditoria append-only |
| MEA03 Managed Compliance With External Requirements | Monitoramento | Transversal (conformidade) | ISACA 2025 p. 13 | F2-R4 ¹ | — |
| MEA04 Managed Assurance | Monitoramento | Qualidade; Ética e integridade | ISACA 2025 p. 15 | F7-R4 ¹ | — |

¹ mapeamento citado no white paper ISACA (2025); demais: interpretação da equipe.

## 2. PMI PMBOK Guide 8ª ed. (tabela separada)

| Seção | Título | Parte · páginas | Uso no sistema | Mapeamentos |
|---|---|---|---|---|
| 2.1 | Governance Performance Domain | PMBOK Guide · p. 9–34 | Base para gates, aprovações, responsabilização, indicadores e gestão do conhecimento no sistema. | F3-R1 |
| 2.1.6.8 | Assess and Implement Changes | PMBOK Guide · p. 27 | Revalidação obrigatória de gate após mudança em requisito/evidência aprovada; decisões versionadas. | F3-R4; F6-R4 |
| 2.1.6.9 | Close Project or Phase | PMBOK Guide · p. 30 | Aprovação de gate encerra a fase; encerramento de projeto com justificativa formal. | F6-R5 |
| 2.1.5.1–2.1.5.2 | Leading Indicators; Lagging Indicators | PMBOK Guide · p. 13 | Cada KPI do sistema é classificado como de tendência ou de resultado em sua ficha técnica. | F7-R1; Fichas técnicas de KPI com classificação tendência/resultado |
| 2.1.6.1 | Initiate Project or Phase | PMBOK Guide · p. 16 | Fase 1 (oportunidade e justificativa) e abertura formal de cada fase pelo gate anterior. | F1-R1 |
| 2.1.6.6 | Manage Project Knowledge | PMBOK Guide · p. 23–25 | Camada K: lições aprendidas (explícitas ou tácitas tornadas explícitas), reuso entre projetos. | Base de lições aprendidas com taxonomia e visibilidade controlada; F7-R3 |
| 2.1.6.7 | Monitor and Control Project Performance | PMBOK Guide · p. 25 | Painel de indicadores e insights de alerta precoce. | F7-R1; Insights determinísticos de alerta precoce com revisão humana |
| 2.1.6.5 | Manage Quality Assurance | PMBOK Guide · p. 22 | Revisão segregada de evidências e validação de requisitos. | F5-R2; F6-R1 |
| 2.1.5.3 | SMART Criteria | PMBOK Guide · p. 13 | Objetivos de negócio e metas de benefício (requisito F1-R3) devem ser mensuráveis e datados. | F1-R3 |
| 4.2 | Project Development Approaches | The Standard · p. 58–65 | Campo de abordagem no projeto; tarefas paralelas dentro da fase com passagem formal de estágio (híbrido). | F1-R6 |
| 4.5 | Project Management Focus Areas | The Standard · p. 68–72 | Não confundir com as focus areas do COBIT 2019; usado apenas como referência conceitual. | — |
| 3.6 | Be an Accountable Leader | The Standard · p. 45 | Autoria, justificativa e segregação de funções em toda decisão; trilha de auditoria. | F1-R2 |
| 3.8 | Build an Empowered Culture | The Standard · p. 52 | Capacitação contínua das equipes (F7-R5) e lições compartilhadas. | F7-R5 |
| 3.3 | Adopt a Holistic View | The Standard · p. 37 | Painel único integrando fases, riscos, custos, evidências e decisões. | Visão geral do portfólio |
| 3.5 | Embed Quality Into Processes and Deliverables | The Standard · p. 42 | Critérios de aceite por requisito e evidência revisada. | — |
| 3.7 | Integrate Sustainability Within All Project Areas | The Standard · p. 47 | Fator 'sustentabilidade' na avaliação de uso responsável de IA. | F6-R7 |
| 3.4 | Focus on Value | The Standard · p. 39 | Caso de negócio, objetivos e métricas de benefício obrigatórios no início. | F1-R1 |
| 2.6 | Resources Performance Domain | PMBOK Guide · p. 78–90 | Equipes, atribuição de tarefas restrita ao escopo e capacidade (GPU) como categoria de custo/risco. | F4-R1 |
| 2.7 | Risk Performance Domain | PMBOK Guide · p. 92–101 | Registro de riscos, análise P×I, respostas (tratamentos) e monitoramento. | F2-R2; F2-R5; F5-R4 |
| 2.5 | Stakeholders Performance Domain | PMBOK Guide · p. 66–77 | Patrocinador, comitê de supervisão de IA (F3-R5) e matriz RACI por entregável. | F1-R2; F3-R3; F3-R5 |
| 3 | Tailoring | PMBOK Guide · p. 102–111 | Templates de ciclo de vida versionados e configuráveis por organização em vez de regras fixas. | Templates de ciclo de vida versionados (v1, v2, v3) e por organização |
| X2 | Project Management Offices | PMBOK Guide · p. 232–235 | Visão de portfólio, indicadores agregados e lições entre projetos. | Painel multiorganização/portfólio filtrado por permissão |
| X3.3 | Responsible Use and Ethical Concerns | PMBOK Guide · p. 238, 242–243 | Avaliação de uso responsável de IA com oito fatores e humano responsável, exigida no gate 6 (v3). | Avaliação de uso responsável de IA (8 fatores) bloqueando o gate da fase 6; F6-R7 |
| X3.1.1 | Strategies for AI Adoption | PMBOK Guide · p. 237–238 | Campo de estratégia (automação/assistência/ampliação) no projeto; insights do sistema exigem revisão humana. | F1-R6 |
| X3.2 | Common Use Cases | PMBOK Guide · p. 238–242 | Relatórios automatizados, monitoramento contínuo e alerta precoce correspondem aos KPIs e regras de insight. | Relatórios e indicadores automatizados a partir do PostgreSQL |
| X4 | Procurement | PMBOK Guide · p. 244–251 | Risco de fornecedor e categoria de custo de licenças/serviços; contratação de GPU/nuvem. | F2-R1 |

## 3. Requisitos do template vigente

| Fase | Código | Requisito | Obrig. | Evidência | Legal | COBIT |
|---|---|---|---|---|---|---|
| 1 | F1-R1 | Caso de negócio documentado | sim | Caso de negócio | não | EDM02 |
| 1 | F1-R2 | Patrocinador e gerente designados | sim | — | não | BAI11 |
| 1 | F1-R3 | Objetivos e indicadores-alvo definidos | sim | — | não | EDM02 |
| 1 | F1-R4 | Classificação preliminar dos dados | sim | — | não | APO14 |
| 1 | F1-R5 | Alinhamento ético e de valor da iniciativa de IA | sim | — | não | EDM01 |
| 1 | F1-R6 | Abordagem de desenvolvimento e estratégia de adoção de IA definidas | sim | — | não | BAI11 |
| 2 | F2-R1 | Análise de viabilidade técnica e de custo | sim | Análise de risco | não | BAI11 |
| 2 | F2-R2 | Registro inicial de riscos avaliado | sim | — | não | APO12 |
| 2 | F2-R3 | Requisitos funcionais e não funcionais aprovados | sim | — | não | BAI11 |
| 2 | F2-R4 | Avaliação de privacidade (LGPD) quando houver dados pessoais | sim | — | sim | APO14 |
| 2 | F2-R5 | Riscos de IA classificados nas cinco categorias ISACA | sim | — | não | APO12 |
| 3 | F3-R1 | Plano de implantação aprovado | sim | Plano | não | BAI11 |
| 3 | F3-R2 | Arquitetura de referência registrada | sim | Arquitetura | não | BAI11 |
| 3 | F3-R3 | Matriz RACI dos entregáveis definida | sim | — | não | BAI11 |
| 3 | F3-R4 | Plano de gestão de mudanças | sim | — | não | BAI06 |
| 3 | F3-R5 | Estrutura de supervisão de IA definida | sim | — | não | EDM05 |
| 3 | F3-R6 | Política de transparência e registro de decisões do sistema de IA | sim | — | não | EDM01 |
| 4 | F4-R1 | Infraestrutura provisionada e verificada | sim | — | não | BAI06 |
| 4 | F4-R2 | Catálogo e linhagem dos dados registrados | sim | Validação de dados | não | APO14 |
| 4 | F4-R3 | Controles de segurança de base aplicados | sim | Relatório de segurança | não | DSS04 |
| 4 | F4-R4 | Plano de backup e recuperação | sim | Backup/recuperação | não | DSS04 |
| 4 | F4-R5 | Critérios de qualidade de dados para IA definidos | sim | — | não | APO11 |
| 4 | F4-R6 | Ativos que hospedam a plataforma de IA inventariados e protegidos | sim | — | não | BAI09 |
| 5 | F5-R1 | Critérios de sucesso da PoC definidos antes da execução | sim | — | não | BAI11 |
| 5 | F5-R2 | Resultado da PoC registrado | sim | Teste | não | BAI11 |
| 5 | F5-R3 | Avaliação de qualidade e viés do modelo | sim | Teste | não | APO12 |
| 5 | F5-R4 | Riscos reavaliados após a PoC | sim | — | não | APO12 |
| 5 | F5-R5 | Explicabilidade das saídas documentada | sim | — | não | EDM01 |
| 6 | F6-R1 | Testes de homologação aprovados | sim | Teste | não | BAI07 |
| 6 | F6-R2 | Relatório de segurança aprovado | sim | Relatório de segurança | não | BAI07 |
| 6 | F6-R3 | Teste de recuperação executado | sim | Backup/recuperação | não | DSS04 |
| 6 | F6-R4 | Mudança de produção aprovada | sim | — | não | BAI06 |
| 6 | F6-R5 | Termo de aceite operacional | sim | Termo de aceite | não | BAI07 |
| 6 | F6-R6 | Processo de atualização e retreinamento controlado do modelo | sim | — | não | BAI06 |
| 6 | F6-R7 | Avaliação de uso responsável de IA concluída | sim | — | não | EDM01 |
| 7 | F7-R1 | Indicadores operacionais monitorados | sim | — | não | MEA01 |
| 7 | F7-R2 | Revisão periódica de riscos | não | — | não | APO12 |
| 7 | F7-R3 | Lições aprendidas registradas | não | — | não | MEA01 |
| 7 | F7-R4 | Auditoria periódica de qualidade e equidade dos dados de treinamento | não | — | não | MEA04 |
| 7 | F7-R5 | Capacitação contínua das equipes em IA e governança | não | — | não | APO04 |
