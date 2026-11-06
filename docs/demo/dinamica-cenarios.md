# Dinâmica de avaliação: sete situações do mundo da IA

Roteiro para sessões com participantes (ou com a turma) em que um **fato plausível** acontece num projeto e a pessoa
resolve a situação no TrajetórIA. Serve à avaliação por tarefas da DSR: observar se o fluxo é compreensível e útil,
e não "provar" o produto.

**Dados:** todos sintéticos (`seed_demo --confirm-demo`). Organizações fictícias: *Organização Demonstrativa Alfa*
(setor privado) e *Secretaria Estadual Demonstrativa Gama* (setor público). Valores, pessoas e normas citados são
inventados.

**Onde executar:**
- **Sistema Django em execução** (banco `govia_demo`): as ações são gravadas, bloqueadas ou auditadas de verdade.
  É o modo indicado para a dinâmica.
- **Protótipo HTML estático**: serve só para **observar** a situação (formulários desativados). Útil para apresentar
  o cenário antes da sessão.

**Como conduzir cada situação (10 a 15 min):**
1. O facilitador lê o **fato**.
2. O participante, no perfil indicado, tenta resolver.
3. O observador registra:
   - se a tarefa foi concluída (sim, com ajuda, não);
   - onde a pessoa hesitou;
   - comentários espontâneos;
   - clareza de 1 a 5;
   - "isso aconteceria assim na sua organização?" (pergunta aberta).
4. **Não ajudar** antes de 2 minutos de tentativa.

Cada situação está ligada a um achado da 1ª rodada da pesquisa (ver `docs/pesquisa/evolucao-orientada-pela-pesquisa.md`).

---

## S1 · GOV-2026-01 — Aquisição de infraestrutura de GPUs (setor público)

- **Contexto:** contratação de servidores com GPUs para que as PoCs do órgão deixem de depender da nuvem. O projeto
  está na fase 2 (viabilidade).
- **Fato:** "O decreto de contingenciamento cortou o orçamento do exercício, e o fornecedor informou entrega em
  mais de 180 dias."
- **Perfil:** gerência de projeto; depois, patrocínio.
- **Tarefa:**
  1. Tentar solicitar o gate da fase 2.
  2. Identificar o que bloqueia.
  3. Registrar a fonte de financiamento (ou a falta dela).
  4. Encaminhar a decisão sobre capacidade provisória (nuvem por 6 meses × aguardar × parceria).
- **O que o sistema faz:**
  - o gate fica bloqueado por F2-R1 (exigência da v4: fonte de financiamento da capacidade de produção);
  - os riscos de custo e de fornecedor ficam visíveis;
  - a decisão fica *proposta*, à espera do patrocínio.
- **Achado relacionado:** A02, infraestrutura como obstáculo mais citado.
- **Telas:**
  - `gerente/projetos.html`, depois GOV-2026-01, fase 2;
  - `gerente/riscos.html`;
  - decisões do projeto.

## S2 · GOV-2026-02 — Assistente virtual ao cidadão com IA generativa e RAG (setor público)

- **Contexto:** chatbot sobre serviços do órgão, já na fase 5 (prova de conceito).
- **Fato:** "A segurança descobriu que os registros de conversa da PoC estão guardando o CPF dos cidadãos."
- **Perfil:** segurança e conformidade; depois, gerência.
- **Tarefa:**
  1. Localizar o risco.
  2. Registrar o tratamento (desativar o registro completo, anonimizar, prazo e responsável).
  3. Verificar se o gate da fase 5 continua bloqueado.
  4. Conferir a linhagem do dado pessoal.
- **O que o sistema faz:**
  - o risco crítico sem tratamento **bloqueia o gate**;
  - o catálogo de dados mostra a base com dados pessoais e a linhagem até o índice de busca.
- **Achado relacionado:** A06, privacidade e segurança como riscos dominantes.
- **Telas:**
  - `gerente/riscos.html`;
  - dados do projeto;
  - `aprovador/gates.html`.

## S3 · IA-2026-03 — Detecção de fraudes em transações (setor privado)

- **Contexto:** modelo que sinaliza transações suspeitas para análise humana, na fase 6 (homologação).
- **Fato:** "O teste de equidade mostrou falsos positivos duas vezes maiores em uma região. A diretoria quer entrar
  em produção mesmo assim na próxima semana."
- **Perfil:** aprovação de gates; depois, patrocínio.
- **Tarefa:**
  1. Examinar por que o gate da fase 6 não pode ser aprovado.
  2. Ler a decisão proposta ("adiar até nova rodada de testes").
  3. Decidir com justificativa.
- **O que o sistema faz:**
  - a avaliação de uso responsável de IA tem fatores pendentes (viés, transparência) e bloqueia o gate;
  - a autoaprovação é impedida;
  - a decisão fica registrada com alternativas e motivação.
- **Achado relacionado:** A06, uso ético com a percepção mais baixa, e A04, decisões sem registro.
- **Telas:**
  - `aprovador/gates.html`;
  - uso responsável de IA do projeto;
  - decisões do projeto.

## S4 · IA-2026-04 — Inspeção visual de qualidade com visão computacional (setor privado, borda)

- **Contexto:** modelo embarcado na linha de produção, já em operação (fase 7).
- **Fato:** "Depois da troca das luminárias da fábrica, a acurácia caiu de 96% para 88%, e peças com defeito estão
  passando."
- **Perfil:** gerência; depois, auditoria.
- **Tarefa:**
  1. Localizar o risco de qualidade e a tarefa de retreinamento.
  2. Consultar a lição aprendida aprovada.
  3. (Auditor) recuperar quem registrou e quem aprovou a lição.
- **O que o sistema faz:**
  - risco e tarefa ficam vinculados à fase de operação;
  - a lição aprovada fica visível à organização;
  - a trilha de auditoria mostra autor e aprovador.
- **Achado relacionado:** A07, preservar conhecimento, e A08, indicadores de resultado ausentes.
- **Limite a observar:** o MVP ainda não acompanha a acurácia do modelo. Anotar se o participante sente falta disso.
- **Telas:**
  - `gerente/inteligencia.html`;
  - `gerente/riscos.html`;
  - `auditor/auditoria.html`.

## S5 · IA-2026-01 — Plataforma corporativa de IA generativa on-premises (setor privado)

- **Contexto:** plataforma de LLM em GPUs próprias, na fase 1.
- **Fato:** "O patrocinador quer aprovar a passagem para a fase 2 hoje, mas o risco de exposição de dados pessoais
  no treinamento ainda não tem tratamento."
- **Perfil:** gerência; depois, aprovação.
- **Tarefa:**
  1. Solicitar o gate.
  2. Interpretar os bloqueios.
  3. Decidir entre tratar o risco ou pedir exceção formal, com justificativa, risco residual e validade.
- **O que o sistema faz:**
  - lista exata de bloqueios;
  - exceção só com justificativa e prazo, nunca para requisito legal;
  - tudo auditado.
- **Achado relacionado:** A03 (critérios de passagem pouco priorizados). Observar se o bloqueio é percebido como
  útil ou como burocracia.
- **Telas:**
  - `gerente/projetos.html`, depois IA-2026-01, fase 1;
  - `aprovador/gates.html`.

## S6 · IA-2026-02 — Plataforma de MLOps em nuvem híbrida (setor privado)

- **Contexto:** padronização de treinamento e implantação de modelos, na fase 1, sem decisões registradas.
- **Fato:** "Na reunião de ontem, decidiu-se usar a nuvem pública para treinar e o datacenter próprio para executar
  os modelos. Ninguém registrou a decisão nem as alternativas discutidas."
- **Perfil:** gerência; depois, auditoria.
- **Tarefa:**
  1. Registrar a decisão (pauta, alternativas, motivação, riscos considerados).
  2. Encaminhá-la ao patrocínio.
  3. (Auditor) localizar a decisão e o histórico.
- **O que o sistema faz:**
  - a decisão é versionada, com proponente e decisor distintos;
  - fica visível na trilha de auditoria.
- **Achado relacionado:** A04, registro de decisões e decisão personalista.
- **Telas:**
  - decisões do projeto;
  - `auditor/auditoria.html`.

## S7 · GOV-2026-03 — Controle de qualidade de laudos periciais com IA (setor público + universidade)

- **Origem:** cenário **inspirado em um projeto real** da equipe, **anonimizado**. Nomes de instituições, datas, metas
  estratégicas e sistemas foram retirados ou trocados por equivalentes fictícios.
- **Contexto:** parceria entre um órgão estadual de perícia e uma universidade pública. A ideia é usar modelos
  multimodais (texto, imagem e vídeo) como **copiloto do perito**, apontando lacunas, inconsistências e falta de
  padronização em laudos.
- **Situação na fase 2:** oito das dez tarefas de formalização estão concluídas:
  - manifestação de interesse e reunião de alinhamento;
  - minutas do termo de cooperação técnica e do plano de trabalho;
  - pareceres jurídicos das duas instituições, cada um com uma rodada de modificações;
  - plano de gestão de dados.

  Faltam a **assinatura** e a **publicação** do acordo.
- **Fato:** "A assinatura atrasou mais dois meses. A equipe da universidade propõe começar os testes com laudos reais
  'só para não perder tempo', e os servidores com GPU ainda não foram comprados."
- **Perfil:** patrocínio, que tenta conceder exceção ao requisito; depois, segurança e conformidade e, por fim,
  auditoria.
- **Tarefa:**
  1. Tentar avançar a fase ou conceder exceção ao requisito F2-R4 (avaliação de privacidade/LGPD).
  2. Consultar a decisão proposta ("usar só laudos sintéticos até a publicação").
  3. Verificar os riscos de atraso, de dados sensíveis e de GPU.
  4. (Auditor) localizar a tentativa negada.
- **O que o sistema faz:**
  - requisito **legal** não admite exceção: a tentativa é recusada e **registrada na auditoria**;
  - o gate continua bloqueado;
  - as tarefas mostram onde a formalização parou.
- **Achados relacionados:**
  - A10, fatores político-institucionais e burocracia;
  - A02, infraestrutura;
  - A06, privacidade.
- **O que observar:** o participante percebe a formalização como parte do projeto de IA ou como algo "fora" dele?
- **Telas:**
  - `gerente/projetos.html`, depois GOV-2026-03, Tarefas e Riscos;
  - `auditor/auditoria.html`.

---

## Registro das sessões (modelo)

| Sessão | Perfil do participante | Situação | Concluiu? | Hesitações | Clareza (1–5) | Utilidade percebida | Aconteceria assim na sua organização? | Sugestões |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

Não registre nome nem organização. Use códigos (S-01, S-02…). Os resultados das sessões alimentam a matriz
evidência → decisão → solução **separados** dos resultados do questionário.
