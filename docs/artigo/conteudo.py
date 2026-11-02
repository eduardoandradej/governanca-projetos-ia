# -*- coding: utf-8 -*-
"""Conteúdo do artigo (texto corrido). Marcação: **negrito** e _itálico_ (estrangeirismos)."""

TITULO = ("DA PROVA DE CONCEITO À PRODUÇÃO: NEXFASE, UM MODELO INTEGRADO DE GOVERNANÇA E GESTÃO "
          "DE PROJETOS DE IMPLANTAÇÃO DE PLATAFORMAS CORPORATIVAS DE INTELIGÊNCIA ARTIFICIAL")

AUTORES = [
    "Autor 1: Eduardo Andrade de Jesus — [Instituição/Curso/Programa/Setor] — eduardo.andradej@gmail.com",
    "Autor 2: Matheus Fernandes Cunha — [Instituição/Curso/Programa/Setor] — [E-mail]",
    "Autor 3: Thais Gonçalves de Alencar — [Instituição/Curso/Programa/Setor] — [E-mail]",
    "Professor 1: Ricardo Kneipp — [Instituição/Curso/Programa/Setor] — [E-mail]",
]

EIXO = "[Selecionar o eixo temático correspondente]"
MODALIDADE = "Solução/Inovação em TI."

RESUMO = (
    "Organizações desenvolvem provas de conceito de inteligência artificial (IA), mas têm dificuldade para levá-las à "
    "produção com segurança e responsabilização definida. Este trabalho desenvolveu e avaliou o NexFase, plataforma web "
    "de governança e gestão de projetos de implantação de IA, fundamentada no COBIT 2019, no _white paper_ da ISACA "
    "sobre governança de IA e no PMBOK® Guide, 8ª edição. Pela _Design Science Research_, o artefato foi desenvolvido "
    "em Python, Django e PostgreSQL e avaliado em cenário sintético. Ele implementa sete fases com portões de passagem "
    "verificados no servidor, segregação de funções, auditoria imutável e transformação de dados em conhecimento "
    "revisado. Os 139 testes automatizados e a demonstração atenderam aos dez critérios do protocolo, indicando que "
    "controles verificáveis sustentam a transição da experimentação à produção."
)

PALAVRAS_CHAVE = ("Governança de TI. Gerenciamento de projetos. Inteligência artificial. COBIT 2019. "
                  "Design Science Research.")

INTRODUCAO = [
    "A adoção de IA traz desafios como vieses, baixa transparência e ataques adversariais, que exigem governança "
    "específica (Isaca, 2025, p. 4-5). O difícil raramente é a prova de conceito, e sim transformá-la em serviço seguro "
    "e sustentável. O PMBOK® Guide, 8ª edição, reconhece esse contexto em apêndice sobre IA (Project Management "
    "Institute, 2025, p. 237). O trabalho integra governança e gerenciamento de projetos em um artefato avaliável e "
    "independente de fornecedor.",
]

PROBLEMA = [
    "Equipes de infraestrutura, dados, segurança e negócio usam ferramentas distintas, dispersando decisões e "
    "responsabilidades; a ISACA aponta essa falta de clareza como a lacuna mais crítica (Isaca, 2025, p. 7). Pergunta-se: "
    "como um sistema fundamentado no COBIT 2019 e no gerenciamento de projetos pode controlar as fases de implantação de "
    "plataformas de IA com rastreabilidade, responsabilidades, critérios de passagem e informação gerencial?",
]

OBJETIVO_GERAL = (
    "Desenvolver e avaliar preliminarmente um produto mínimo viável (MVP) web de governança e gestão de projetos de "
    "implantação de plataformas corporativas de IA."
)

OBJETIVOS_ESPECIFICOS = [
    "Modelar um ciclo de sete fases com critérios de passagem verificáveis.",
    "Implementar papéis com escopo, segregação de funções e auditoria íntegra.",
    "Transformar registros dos projetos em indicadores e conhecimento revisado.",
    "Avaliar o artefato por testes automatizados e demonstração com dados sintéticos.",
]

FUNDAMENTACAO_INTRO = None

GESTAO_PROJETOS = [
    "O PMBOK® Guide, 8ª edição, organiza o gerenciamento em domínios de desempenho, admite abordagens preditivas, "
    "adaptativas e híbridas (Project Management Institute, 2025, p. 58), distingue indicadores de tendência e de "
    "resultado (p. 13) e trata o conhecimento do projeto (p. 23). Seu apêndice sobre IA classifica o uso em automação, "
    "assistência e ampliação e lista fatores éticos como viés, privacidade e responsabilização (p. 237-238, 242).",
]

SERVICOS_TI = [
    "O ITIL® (PeopleCert, 2026) orienta a entrega de valor por serviços; seus conceitos apoiaram as fases de "
    "homologação, entrada em produção e melhoria contínua.",
]

GOVERNANCA_TI = [
    "O COBIT 2019 organiza a governança em cinco domínios (EDM, APO, BAI, DSS e MEA) e 40 objetivos (Isaca, 2025, "
    "p. 7-9). A ISACA os aplica ao ciclo de IA: EDM no desenho, APO no desenvolvimento, BAI na implantação, DSS na "
    "operação e MEA no monitoramento (p. 13-14), e propõe cinco categorias de risco de IA (p. 16).",
]

NATUREZA = (
    "Pesquisa aplicada de desenvolvimento de solução, conduzida pela _Design Science Research_, cujas etapas vão da "
    "identificação do problema à avaliação e comunicação do artefato (Peffers et al., 2007)."
)

ABORDAGEM = (
    "Quali-quantitativa: qualitativa no mapeamento entre referenciais e funcionalidades; quantitativa na mensuração dos "
    "testes e indicadores."
)

PROCEDIMENTOS = (
    "Pesquisa bibliográfica e documental, prototipação em oito incrementos e análise de métricas dos testes."
)

CONTEXTO = (
    "Laboratório acadêmico, novembro de 2026, cenário sintético com duas organizações fictícias e onze usuários."
)

INSTRUMENTOS = (
    "_White paper_ da ISACA, capítulos do PMBOK® Guide, código versionado, 139 testes automatizados, roteiro de "
    "demonstração em navegador e protocolo com dez critérios."
)

ANALISE = (
    "Resultados comparados às metas definidas previamente; falhas registradas, corrigidas e reexecutadas."
)

CONTEXTO_ORG = (
    "Organizações que implantam plataformas de IA em infraestrutura local, nuvem ou modelo híbrido, com GPUs e dados "
    "sensíveis."
)

DIAGNOSTICO = (
    "Há responsabilização difusa (Isaca, 2025, p. 15), riscos como viés (p. 16) e a exigência de que um ser humano "
    "responda por cada decisão (Project Management Institute, 2025, p. 238)."
)

SOLUCAO = [
    "O NexFase é uma aplicação web modular em Django e PostgreSQL, com software livre. O projeto percorre sete fases, da "
    "oportunidade à operação. Cada passagem exige requisitos validados, evidências aprovadas e riscos críticos tratados, "
    "verificados no servidor; quem solicita não aprova, e mudanças posteriores exigem revalidação. A auditoria é protegida "
    "também no banco de dados. Há matriz de riscos 5×5, custos, decisões versionadas e avaliação de uso responsável de "
    "IA. Doze indicadores com ficha técnica e seis regras de alerta transformam dados em conhecimento, convertido em "
    "recomendação somente após revisão humana.",
]

APLICACAO_REF = "O Quadro 1 sintetiza como cada referencial foi incorporado ao artefato."

QUADRO1_TITULO = "Quadro 1 — Aplicação dos referenciais no NexFase"
QUADRO1 = [
    ("Gestão de Projetos", "PMBOK® Guide — 8ª edição",
     "Fases com portões; abordagem e estratégia de adoção de IA; indicadores de tendência e resultado; lições aprendidas."),
    ("Serviços de TI", "ITIL® Version 5", "Transição e operação nas fases 6 e 7."),
    ("Governança de TI", "COBIT® 2019", "22 objetivos em 105 associações, 52 citadas pela ISACA; riscos de IA; auditoria."),
]

FONTE = "Fonte: elaborado pelos autores (2026)."

RESULTADOS = (
    "Os dez critérios do protocolo foram atendidos. Os testes revelaram e permitiram corrigir seis defeitos reais, como a "
    "perda do registro de auditoria de uma negação após o desfazimento da transação (Quadro 2)."
)

QUADRO2_TITULO = "Quadro 2 — Critérios de avaliação e resultados observados"
QUADRO2_CABECALHO = ("Critério", "Meta do protocolo", "Resultado observado", "Situação")
QUADRO2 = [
    ("Fluxo das fases", "Fases 1 a 7 via portões", "6 portões aprovados; fase 7 iniciada", "Atendido"),
    ("Bloqueios", "Bloquear sem requisito, evidência ou risco tratado", "100% dos cenários bloqueados", "Atendido"),
    ("Segregação e concorrência", "Uma decisão por solicitação", "2 aprovações simultâneas: 1 decisão", "Atendido"),
    ("Isolamento", "Nenhum acesso fora do escopo", "Recusa em telas, API e exportações", "Atendido"),
    ("Dados → conhecimento", "Indicador correto; alerta rastreável", "16,7% (1 de 6); lição aprovada", "Atendido"),
    ("Qualidade", "Suíte sem falhas", "139 de 139 testes; 5 vulnerabilidades corrigidas", "Atendido"),
]

DISCUSSAO = [
    "O artefato coordena as fases com critérios verificáveis e responsabilidades explícitas. O ciclo de IA da ISACA "
    "(2025) mostrou-se operacionalizável como requisitos por fase, e a revisão humana dos alertas segue a estratégia de "
    "assistência do PMBOK® Guide (Project Management Institute, 2025, p. 238).",
]

CONTRIB_ACAD = (
    "Operacionalização conjunta do COBIT 2019, da ISACA e do PMBOK® Guide, com rastreabilidade reutilizável no ensino."
)

CONTRIB_PROF = (
    "Camada única, independente de fornecedor e implantável em uma máquina virtual."
)

CONSIDERACOES = (
    "Portões verificáveis, segregação, auditoria íntegra e conhecimento revisado sustentam projetos de IA até a produção."
)

LIMITACOES = (
    "Avaliação sintética, sem usuários reais; mapeamentos interpretativos; faltam autenticação multifator e teste de intrusão."
)

TRABALHOS_FUTUROS = (
    "Avaliação com gestores, implantação em nuvem, integrações de entrega contínua e estudos de caso reais."
)

REFERENCIAS = [
    "ISACA. **Leveraging COBIT for effective AI system governance**. Schaumburg, IL: ISACA, 2025. Disponível em: "
    "https://www.isaca.org/resources/white-papers/2025/leveraging-cobit-for-effective-ai-system-governance. "
    "Acesso em: 2 nov. 2026.",
    "PEFFERS, K.; TUUNANEN, T.; ROTHENBERGER, M. A.; CHATTERJEE, S. A design science research methodology for "
    "information systems research. **Journal of Management Information Systems**, [s. l.], v. 24, n. 3, p. 45-77, 2007.",
    "PEOPLECERT. **ITIL Foundation (Version 5)**. [S. l.]: PeopleCert, 2026. Disponível em: "
    "https://www.peoplecert.org/browse-certifications/it-governance-and-service-management/ITIL-1/"
    "itil-5-foundation-version-50-4154. Acesso em: 1 set. 2026.",
    "PROJECT MANAGEMENT INSTITUTE. **A guide to the project management body of knowledge (PMBOK® Guide) and The "
    "Standard for Project Management**. 8. ed. Newtown Square, PA: Project Management Institute, 2025.",
]

