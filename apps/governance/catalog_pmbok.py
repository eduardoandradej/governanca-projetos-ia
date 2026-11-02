"""Referências ao PMI PMBOK Guide 8ª ed. (2025) usadas pelo MVP — títulos de seção e páginas apenas.

Fonte consultada: cópia licenciada do usuário (uso pessoal), lida em 2026-11-02. Nenhum texto, figura ou tabela
do PMI é reproduzido aqui; a coluna `analysis` é redação original da equipe. Numeração de páginas: "The Standard"
e "PMBOK Guide" têm paginação própria.
"""

S, G = "The Standard", "PMBOK Guide"

# code, kind, section, title, title_pt, part, pages, analysis
REFERENCES = [
    ("PMB-GOV", "domain", "2.1", "Governance Performance Domain", "Domínio de desempenho Governança", G, "9–34",
     "Base para gates, aprovações, responsabilização, indicadores e gestão do conhecimento no sistema."),
    ("PMB-GOV-IND", "concept", "2.1.5.1–2.1.5.2", "Leading Indicators; Lagging Indicators",
     "Indicadores de tendência e de resultado", G, "13",
     "Cada KPI do sistema é classificado como de tendência ou de resultado em sua ficha técnica."),
    ("PMB-GOV-SMART", "concept", "2.1.5.3", "SMART Criteria", "Critérios SMART", G, "13",
     "Objetivos de negócio e metas de benefício (requisito F1-R3) devem ser mensuráveis e datados."),
    ("PMB-GOV-INIT", "process", "2.1.6.1", "Initiate Project or Phase", "Iniciar projeto ou fase", G, "16",
     "Fase 1 (oportunidade e justificativa) e abertura formal de cada fase pelo gate anterior."),
    ("PMB-GOV-QA", "process", "2.1.6.5", "Manage Quality Assurance", "Gerenciar a garantia da qualidade", G, "22",
     "Revisão segregada de evidências e validação de requisitos."),
    ("PMB-GOV-KM", "process", "2.1.6.6", "Manage Project Knowledge", "Gerenciar o conhecimento do projeto", G, "23–25",
     "Camada K: lições aprendidas (explícitas ou tácitas tornadas explícitas), reuso entre projetos."),
    ("PMB-GOV-MC", "process", "2.1.6.7", "Monitor and Control Project Performance",
     "Monitorar e controlar o desempenho", G, "25", "Painel de indicadores e insights de alerta precoce."),
    ("PMB-GOV-CHG", "process", "2.1.6.8", "Assess and Implement Changes", "Avaliar e implementar mudanças", G, "27",
     "Revalidação obrigatória de gate após mudança em requisito/evidência aprovada; decisões versionadas."),
    ("PMB-GOV-CLOSE", "process", "2.1.6.9", "Close Project or Phase", "Encerrar projeto ou fase", G, "30",
     "Aprovação de gate encerra a fase; encerramento de projeto com justificativa formal."),
    ("PMB-STK", "domain", "2.5", "Stakeholders Performance Domain", "Domínio Partes interessadas", G, "66–77",
     "Patrocinador, comitê de supervisão de IA (F3-R5) e matriz RACI por entregável."),
    ("PMB-RES", "domain", "2.6", "Resources Performance Domain", "Domínio Recursos", G, "78–90",
     "Equipes, atribuição de tarefas restrita ao escopo e capacidade (GPU) como categoria de custo/risco."),
    ("PMB-RISK", "domain", "2.7", "Risk Performance Domain", "Domínio Riscos", G, "92–101",
     "Registro de riscos, análise P×I, respostas (tratamentos) e monitoramento."),
    ("PMB-TAILOR", "concept", "3", "Tailoring", "Adaptação (tailoring)", G, "102–111",
     "Templates de ciclo de vida versionados e configuráveis por organização em vez de regras fixas."),
    ("PMB-P-HOLISTIC", "principle", "3.3", "Adopt a Holistic View", "Adotar uma visão holística", S, "37",
     "Painel único integrando fases, riscos, custos, evidências e decisões."),
    ("PMB-P-VALUE", "principle", "3.4", "Focus on Value", "Foco em valor", S, "39",
     "Caso de negócio, objetivos e métricas de benefício obrigatórios no início."),
    ("PMB-P-QUALITY", "principle", "3.5", "Embed Quality Into Processes and Deliverables",
     "Incorporar qualidade a processos e entregas", S, "42", "Critérios de aceite por requisito e evidência revisada."),
    ("PMB-P-ACCOUNT", "principle", "3.6", "Be an Accountable Leader", "Ser um líder responsável", S, "45",
     "Autoria, justificativa e segregação de funções em toda decisão; trilha de auditoria."),
    ("PMB-P-SUST", "principle", "3.7", "Integrate Sustainability Within All Project Areas",
     "Integrar a sustentabilidade em todas as áreas", S, "47",
     "Fator 'sustentabilidade' na avaliação de uso responsável de IA."),
    ("PMB-P-CULTURE", "principle", "3.8", "Build an Empowered Culture", "Construir uma cultura de autonomia", S, "52",
     "Capacitação contínua das equipes (F7-R5) e lições compartilhadas."),
    ("PMB-LC-APPROACH", "lifecycle", "4.2", "Project Development Approaches",
     "Abordagens de desenvolvimento (preditiva, adaptativa, híbrida)", S, "58–65",
     "Campo de abordagem no projeto; tarefas paralelas dentro da fase com passagem formal de estágio (híbrido)."),
    ("PMB-LC-FOCUS", "lifecycle", "4.5", "Project Management Focus Areas", "Áreas de foco do gerenciamento", S, "68–72",
     "Não confundir com as focus areas do COBIT 2019; usado apenas como referência conceitual."),
    ("PMB-X2", "appendix", "X2", "Project Management Offices", "Escritórios de projetos (PMO)", G, "232–235",
     "Visão de portfólio, indicadores agregados e lições entre projetos."),
    ("PMB-X3-STRAT", "appendix", "X3.1.1", "Strategies for AI Adoption", "Estratégias de adoção de IA", G, "237–238",
     "Campo de estratégia (automação/assistência/ampliação) no projeto; insights do sistema exigem revisão humana."),
    ("PMB-X3-USE", "appendix", "X3.2", "Common Use Cases", "Casos de uso comuns (tabela X3-1)", G, "238–242",
     "Relatórios automatizados, monitoramento contínuo e alerta precoce correspondem aos KPIs e regras de insight."),
    ("PMB-X3-ETHICS", "appendix", "X3.3", "Responsible Use and Ethical Concerns", "Uso responsável e questões éticas",
     G, "238, 242–243", "Avaliação de uso responsável de IA com oito fatores e humano responsável, exigida no gate 6 (v3)."),
    ("PMB-X4", "appendix", "X4", "Procurement", "Aquisições", G, "244–251",
     "Risco de fornecedor e categoria de custo de licenças/serviços; contratação de GPU/nuvem."),
]

REQUIREMENT_MAPPINGS = {
    "F1-R1": ["PMB-P-VALUE", "PMB-GOV-INIT"], "F1-R2": ["PMB-STK", "PMB-P-ACCOUNT"], "F1-R3": ["PMB-GOV-SMART"],
    "F1-R6": ["PMB-LC-APPROACH", "PMB-X3-STRAT"], "F2-R1": ["PMB-X4"], "F2-R2": ["PMB-RISK"], "F2-R5": ["PMB-RISK"],
    "F3-R1": ["PMB-GOV"], "F3-R3": ["PMB-STK"], "F3-R4": ["PMB-GOV-CHG"], "F3-R5": ["PMB-STK"],
    "F4-R1": ["PMB-RES"], "F5-R2": ["PMB-GOV-QA"], "F5-R4": ["PMB-RISK"], "F6-R1": ["PMB-GOV-QA"],
    "F6-R4": ["PMB-GOV-CHG"], "F6-R5": ["PMB-GOV-CLOSE"], "F6-R7": ["PMB-X3-ETHICS", "PMB-P-SUST"],
    "F7-R1": ["PMB-GOV-MC", "PMB-GOV-IND"], "F7-R3": ["PMB-GOV-KM"], "F7-R5": ["PMB-P-CULTURE"],
}

FEATURE_MAPPINGS = [
    ("PMB-GOV-IND", "Fichas técnicas de KPI com classificação tendência/resultado"),
    ("PMB-GOV-KM", "Base de lições aprendidas com taxonomia e visibilidade controlada"),
    ("PMB-GOV-MC", "Insights determinísticos de alerta precoce com revisão humana"),
    ("PMB-TAILOR", "Templates de ciclo de vida versionados (v1, v2, v3) e por organização"),
    ("PMB-P-HOLISTIC", "Visão geral do portfólio"),
    ("PMB-X2", "Painel multiorganização/portfólio filtrado por permissão"),
    ("PMB-X3-USE", "Relatórios e indicadores automatizados a partir do PostgreSQL"),
    ("PMB-X3-ETHICS", "Avaliação de uso responsável de IA (8 fatores) bloqueando o gate da fase 6"),
]


def install(apps):
    Ref = apps.get_model("governance", "FrameworkReference")
    Map = apps.get_model("governance", "FrameworkMapping")
    RequirementTemplate = apps.get_model("lifecycle", "RequirementTemplate")
    refs = {}
    for code, kind, section, title, title_pt, part, pages, analysis in REFERENCES:
        refs[code], _ = Ref.objects.update_or_create(
            code=code, defaults=dict(kind=kind, section=section, title=title, title_pt=title_pt, part=part,
                                     pages=pages, analysis=analysis),
        )
    for rt in RequirementTemplate.objects.filter(stage_template__template_version__template__organization__isnull=True):
        for code in REQUIREMENT_MAPPINGS.get(rt.code, []):
            Map.objects.get_or_create(reference=refs[code], requirement_template=rt)
    for code, feature in FEATURE_MAPPINGS:
        Map.objects.get_or_create(reference=refs[code], feature=feature)
