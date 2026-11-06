# Evolução do artefato orientada pela pesquisa com profissionais

Documento da equipe de pesquisa (IFRJ — Pós-Graduação em Gestão de Negócios e Projetos de TI). Contém **apenas
resultados agregados**: nenhum dado identificável, resposta bruta ou trecho literal de participante é versionado
neste repositório. O arquivo de respostas permanece restrito à equipe.

## 1. Situação do artefato e da pesquisa

- O MVP deste repositório foi desenvolvido como **protótipo exploratório** (teste de viabilidade técnica, com apoio de
  ferramenta de IA generativa), a partir das hipóteses preliminares da equipe. Ele **não** foi derivado da pesquisa.
- A pesquisa (questionário acadêmico, 10 perguntas em 5 dimensões, versão 1.0) foi aplicada para **confrontar essas
  hipóteses**. A coleta continua aberta; os números abaixo são a **rodada 1** e serão atualizados.
- A partir desta rodada, alterações no artefato passam a exigir vínculo explícito com um achado (seção 4).

## 2. Amostra da rodada 1

- 11 respostas recebidas; **9 na análise principal**. Excluídas: 1 resposta de integrante da equipe de pesquisa
  (viés de autor) e 1 envio de teste, conforme decisão da equipe.
- Amostra por conveniência; 4 dos 9 relataram experiência direta em projetos de IA. Sem generalização nem inferência
  estatística.

## 3. Resultados agregados (n = 9; múltipla escolha soma mais de 100%)

| Dimensão | Resultado principal | Leitura |
|---|---|---|
| D1 Informação | Informações dispersas 5/9; falta de integração entre equipes 4/9; 2/9 sem dificuldades relevantes | Dispersão mesmo com ferramentas de gestão em uso (4/9) |
| D2 Decisões | Registro: atas 3/9, reuniões com registros parciais 2/9, sem procedimento 2/9; impacto da falta de registro: sim 3, não 3, não vivenciou 3 | Inconclusivo |
| D3 Riscos | Segurança 8/9, privacidade 7/9, resultados incorretos 5/9; riscos sem procedimento ou reativos 5/9 | Risco tratado de modo pouco estruturado |
| D3 Transição | Infraestrutura insuficiente 5/9; integração 4/9; procedimentos claros de implantação 2/9 | Obstáculos de capacidade e integração à frente da governança |
| D4 Governança | Responsabilidades "nem sempre documentadas" 4/9; percepção mais baixa em uso ético (3/8 ≤ 2) e transparência (3/8 ≤ 2) | Documentação, ética e transparência como lacunas |
| D4 Indicadores | Custo 5/9, cronograma 5/9, benefícios 4/9, qualidade dos modelos 4/9, adoção 3/9 | Indicadores de resultado da solução ausentes no MVP |
| D5 Prioridades | Segurança e conformidade 6/9; centralizar informações 5/9 (0 dos 4 com experiência direta); transição para produção 4/9; critérios para avançar entre fases 2/9 | Os gates não são a prioridade percebida |

## 4. Hipóteses e decisões

| Hipótese preliminar | Rodada 1 | Decisão sobre o artefato |
|---|---|---|
| Informações fragmentadas | Parcialmente corroborada | Manter evidências por referência externa (já existente) |
| Pouca rastreabilidade de decisões | Inconclusiva | Manter; testar nas sessões com usuários |
| Responsabilidades difusas | Fracamente corroborada (falta de documentação, não de definição) | Manter RACI; sem ampliação |
| Ausência de critérios de passagem como obstáculo central | **Contrariada** nesta rodada | Manter os gates sem ampliar; tratá-los como hipótese de design a avaliar |
| Riscos e privacidade pouco tratados | Parcialmente corroborada | **v4: F2-R6** — avaliação preliminar de uso responsável na fase 2 (A06) |
| (emergente) Infraestrutura e orçamento | Achado mais frequente sobre a transição | **v4: F2-R1** passa a exigir o financiamento da capacidade de produção (A02) |
| (emergente) Letramento em IA e definição da necessidade | Achado das respostas abertas | **v4: F1-R1** exige alternativas sem IA (A09) + recomendação de capacitação (não tecnológica) |
| (emergente) Indicadores de resultado e adoção | Valorizados e ausentes | Pendente: indicadores informados nas fases 5–7 (A08), após as sessões com usuários |
| (emergente) Fatores político-institucionais | Achado das respostas abertas | Sem requisito de software; registrado como limite da solução |

## 5. Verificação técnica dos ajustes

`apps/projects/tests/test_projects.py::test_template_v4_incorporates_research_round1_adjustments` verifica F1-R1,
F2-R1 e F2-R6 na v4 e a permanência da v3 (descontinuada) sem o novo requisito. Suíte completa: 140/140 (2026-11-06).

## 6. Próximo ciclo

Sessões de avaliação por tarefas (gerente, aprovador, auditor); atualização destes números ao encerrar a coleta;
decisão sobre A04, A07 e A08 com base nas sessões.
