# Evolução do artefato orientada pela pesquisa com profissionais

Documento da equipe de pesquisa (IFRJ · Pós-Graduação em Gestão de Projetos e Negócios em TI). Contém **apenas
resultados agregados**: nenhum dado identificável, resposta bruta ou trecho literal de participante é versionado
neste repositório. O arquivo de respostas permanece restrito à equipe.

## 1. Situação do artefato e da pesquisa

- O MVP deste repositório foi desenvolvido como **protótipo exploratório** (teste de viabilidade técnica, com apoio de
  ferramenta de IA generativa), a partir das hipóteses preliminares da equipe. Ele **não** foi derivado da pesquisa.
- A pesquisa (questionário acadêmico, 10 perguntas em 5 dimensões, versão 1.0) foi aplicada para **confrontar essas
  hipóteses**. A coleta vai de 04/11 a 11/11/2026; os números abaixo são um corte parcial e serão atualizados.
- A partir desta rodada, alterações no artefato passam a exigir vínculo explícito com um achado (seção 4).

## 2. Coleta e amostra

- Coleta: **04/11/2026 a 11/11/2026**. Os números abaixo são um **corte parcial em 06/11/2026** (rodada 2) e serão
  atualizados no encerramento.
- 13 envios registrados; **12 respostas analisadas**. O primeiro envio foi um teste de funcionamento do formulário e
  não compõe a amostra.
- Amostra por conveniência; 7 dos 12 relataram experiência direta em projetos de IA. Sem generalização nem inferência
  estatística.

## 3. Resultados agregados (rodada 2, n = 12; múltipla escolha soma mais de 100%)

| Dimensão | Resultado principal | Rodada 1 (n = 9) | Leitura |
|---|---|---|---|
| D1 Informação | Informações dispersas 6/12; falta de integração 4/12; sem histórico de alterações 3/12 | 5/9; 4/9 | Dispersão mesmo com ferramentas de gestão em uso |
| D2 Decisões | Impacto da falta de registro: sim 4, não 3, não vivenciou 4, não sabe 1 | 3 / 3 / 3 | Continua inconclusivo |
| D3 Riscos | Privacidade 10/12, segurança 10/12, resultados incorretos 7/12; sem procedimento ou reativo 6/12 | 7, 8, 5; 5/9 | Risco tratado de modo pouco estruturado |
| D3 Transição | Infraestrutura 7/12; integração 5/12; segurança e privacidade 4/12; desempenho 4/12; procedimentos 3/12 | 5/9; 4/9; 2/9 | Capacidade e integração à frente da governança |
| D4 Governança | Responsabilidades "nem sempre documentadas" 4/12; uso ético e transparência com 3/11 respostas válidas ≤ 2 | 4/9; 3/8 | Documentação, ética e transparência como lacunas |
| D4 Indicadores | Benefícios 7/12 (6 dos 7 com experiência direta), cronograma 7/12, qualidade dos modelos 6/12, custo 5/12, adoção 4/12 | 4/9; 5/9; 4/9 | Indicadores de resultado ganham peso |
| D5 Prioridades | Centralizar informações 7/12; segurança e conformidade 6/12; transição 5/12; preservar conhecimento 5/12; critérios entre fases 3/12 | 5; 6; 4; 3; 2 | Os gates seguem atrás das demais prioridades |

**Tema novo na rodada 2 (respostas abertas):** operação de soluções com LLM: custo de *tokens*, permissões de acesso a
ferramentas (*tools*), limites contra alucinações, testes estruturados e registro de uso.

## 4. Hipóteses e decisões

| Hipótese preliminar | Rodada 2 | Decisão sobre o artefato |
|---|---|---|
| Informações fragmentadas | Parcialmente corroborada (6/12) | Manter evidências por referência externa (já existente) |
| Pouca rastreabilidade de decisões | Inconclusiva | Manter; testar nas sessões com usuários |
| Responsabilidades difusas | Fracamente corroborada (falta de documentação, não de definição) | Manter RACI; sem ampliação |
| Ausência de critérios de passagem como obstáculo central | **Contrariada** (infraestrutura 7/12; critérios 3/12) | Manter os gates sem ampliar; tratá-los como hipótese de design a avaliar |
| Riscos e privacidade pouco tratados | Parcialmente corroborada | **v4: F2-R6** — avaliação preliminar de uso responsável na fase 2 (A06) |
| (emergente) Infraestrutura e orçamento | Obstáculo mais frequente na transição | **v4: F2-R1** exige o financiamento da capacidade de produção (A02) |
| (emergente) Letramento em IA e definição da necessidade | Respostas abertas | **v4: F1-R1** exige alternativas sem IA (A09) + capacitação (não tecnológica) |
| (emergente) Indicadores de resultado, adoção e custo de uso de LLMs | Reforçado na rodada 2 | Pendente: indicadores informados nas fases 5–7 (A08), incluindo custo de uso de LLMs, após as sessões |
| (emergente) Fatores político-institucionais | Respostas abertas | Sem requisito de software; registrado como limite da solução |

## 5. Verificação técnica dos ajustes

`apps/projects/tests/test_projects.py::test_template_v4_incorporates_research_round1_adjustments` verifica F1-R1,
F2-R1 e F2-R6 na v4 e a permanência da v3 (descontinuada) sem o novo requisito. Suíte completa: 142/142 (2026-11-06).

## 6. Próximo ciclo

Sessões de avaliação por tarefas (gerente, aprovador, auditor); atualização destes números ao encerrar a coleta;
decisão sobre A04, A07 e A08 com base nas sessões.
