"""Catálogo de objetivos COBIT 2019 usados pelo MVP e mapeamentos para requisitos/funcionalidades.

Nomes oficiais curtos conforme a figura 2 (Core Model) reproduzida em ISACA (2025), p. 9. Colunas de
relevância para IA são PARÁFRASES da equipe; a coluna `basis` distingue o que o white paper cita
explicitamente do que é interpretação da equipe. Nada aqui constitui certificação de conformidade.
"""

WP = "ISACA. Leveraging COBIT for Effective AI System Governance. 2025."
TEAM = "Interpretação da equipe (COBIT 2019 Core Model, conforme fig. 2 de ISACA 2025, p. 9)."

# code, domain, name, name_pt, ai_phase, trustworthy, relevance (paráfrase), source, pages
OBJECTIVES = [
    ("EDM01", "EDM", "Ensured Governance Framework Setting and Maintenance", "Estrutura de governança definida e mantida",
     "Design", "Transparência e honestidade; Ética e integridade",
     "Papéis e responsabilização pela supervisão de IA visíveis entre as equipes; uso ético alinhado à direção da organização.",
     WP, "12"),
    ("EDM02", "EDM", "Ensured Benefits Delivery", "Entrega de benefícios assegurada", "Design", "Ética e integridade",
     "Valor da iniciativa e monitoramento de resultados frente a casos de uso éticos.", WP, "12"),
    ("EDM03", "EDM", "Ensured Risk Optimization", "Otimização de riscos assegurada", "Design", "Transversal (risco)",
     "Riscos de IA identificados, avaliados e mantidos dentro do apetite e da tolerância.", WP, "13"),
    ("EDM05", "EDM", "Ensured Stakeholder Engagement", "Engajamento das partes interessadas", "Design",
     "Transversal (partes interessadas)",
     "Iniciativas de IA alinhadas às expectativas das partes; comitê multidisciplinar de IA (EDM05.01).", WP, "13, 15"),
    ("APO01", "APO", "Managed I&T Management Framework", "Estrutura de gestão de I&T", "Desenvolvimento",
     "Ética e integridade", "Estratégias de tecnologia (inclusive IA) aderentes a padrões éticos.", WP, "12"),
    ("APO03", "APO", "Managed Enterprise Architecture", "Arquitetura corporativa", "Desenvolvimento", "Disponibilidade",
     "Infraestrutura que sustenta escala, segurança e desempenho (exemplo do caso de uso).", WP, "15"),
    ("APO04", "APO", "Managed Innovation", "Inovação", "Desenvolvimento", "Transversal (partes interessadas)",
     "Alinhamento a expectativas e capacitação contínua sobre IA e governança (APO04.04).", WP, "13, 15"),
    ("APO11", "APO", "Managed Quality", "Qualidade", "Desenvolvimento", "Qualidade",
     "Documentação de garantia de qualidade e segurança de sistemas de IA, inclusive aspectos de dados.", WP, "12, 13"),
    ("APO12", "APO", "Managed Risk", "Riscos", "Desenvolvimento", "Transversal (risco)",
     "Avaliações estruturadas de riscos de IA e estratégias de mitigação.", WP, "13"),
    ("APO14", "APO", "Managed Data", "Dados", "Desenvolvimento", "Segurança e privacidade",
     "Estratégia de gestão de dados com papéis de metadados e qualidade; proteção de dados sensíveis.", WP, "13"),
    ("BAI03", "BAI", "Managed Solutions Identification and Build", "Identificação e construção de soluções",
     "Implantação", "Qualidade",
     "Dados de construção de modelos de qualidade; teste e validação de saídas do modelo (BAI03.06).", WP, "12, 14"),
    ("BAI04", "BAI", "Managed Availability and Capacity", "Disponibilidade e capacidade", "Implantação",
     "Disponibilidade", "Capacidade e desempenho da infraestrutura de IA (exemplo do caso de uso).", WP, "15"),
    ("BAI06", "BAI", "Managed IT Changes", "Mudanças de TI", "Implantação", "Resiliência",
     "Mudanças frequentes de modelos e algoritmos coordenadas por gestão de mudanças.", WP, "12"),
    ("BAI07", "BAI", "Managed IT Change Acceptance and Transitioning", "Aceite e transição de mudanças",
     "Implantação", "", "Homologação, aceite operacional e transição para produção.", TEAM, "9"),
    ("BAI09", "BAI", "Managed Assets", "Ativos", "Implantação", "Segurança e privacidade",
     "Proteção da infraestrutura que hospeda os sistemas de IA.", WP, "12"),
    ("BAI11", "BAI", "Managed Projects", "Projetos", "Implantação", "",
     "Gerenciamento do projeto de implantação: plano, fases, responsáveis e gates.", TEAM, "9"),
    ("DSS04", "DSS", "Managed Continuity", "Continuidade", "Operação", "Resiliência; Disponibilidade",
     "Continuidade e recuperação da plataforma de IA em operação.", TEAM, "9, 14"),
    ("DSS05", "DSS", "Managed Security Services", "Serviços de segurança", "Operação", "Segurança e privacidade",
     "Protocolos de segurança contra violações de dados e ataques adversariais.", WP, "12"),
    ("MEA01", "MEA", "Managed Performance and Conformance Monitoring", "Monitoramento de desempenho e conformidade",
     "Monitoramento", "Transversal (monitoramento)", "Metas de monitoramento para o desempenho de IA.", WP, "13"),
    ("MEA02", "MEA", "Managed System of Internal Control", "Sistema de controle interno", "Monitoramento",
     "Transversal (monitoramento)", "Controles internos de segurança e conformidade embutidos.", WP, "13"),
    ("MEA03", "MEA", "Managed Compliance With External Requirements", "Conformidade com requisitos externos",
     "Monitoramento", "Transversal (conformidade)", "Aderência regulatória, qualidade de dados e privacidade.", WP,
     "13"),
    ("MEA04", "MEA", "Managed Assurance", "Asseguração", "Monitoramento", "Qualidade; Ética e integridade",
     "Auditoria regular de qualidade, exatidão e equidade dos dados de treinamento (MEA04.06).", WP, "15"),
]

# Mapeamentos adicionais requisito → objetivos (além do `cobit_ref` principal de cada requisito).
REQUIREMENT_MAPPINGS = {
    "F1-R1": [("EDM02", "team")], "F1-R2": [("BAI11", "team"), ("EDM01", "isaca_ai_2025")],
    "F1-R5": [("EDM01", "isaca_ai_2025"), ("EDM02", "isaca_ai_2025"), ("APO01", "isaca_ai_2025")],
    "F2-R2": [("APO12", "isaca_ai_2025"), ("EDM03", "isaca_ai_2025")],
    "F2-R4": [("APO14", "isaca_ai_2025"), ("MEA03", "isaca_ai_2025")],
    "F2-R5": [("APO12", "isaca_ai_2025"), ("EDM03", "isaca_ai_2025")],
    "F3-R2": [("APO03", "isaca_ai_2025")], "F3-R3": [("EDM05", "isaca_ai_2025")],
    "F3-R5": [("EDM05", "isaca_ai_2025"), ("EDM01", "isaca_ai_2025")], "F3-R6": [("EDM01", "isaca_ai_2025")],
    "F4-R1": [("BAI04", "isaca_ai_2025")], "F4-R2": [("APO14", "isaca_ai_2025")],
    "F4-R3": [("DSS05", "isaca_ai_2025")], "F4-R5": [("APO11", "isaca_ai_2025"), ("BAI03", "isaca_ai_2025")],
    "F4-R6": [("BAI09", "isaca_ai_2025"), ("DSS05", "isaca_ai_2025")],
    "F5-R2": [("BAI03", "isaca_ai_2025")], "F5-R3": [("BAI03", "isaca_ai_2025"), ("APO11", "isaca_ai_2025")],
    "F5-R5": [("EDM01", "isaca_ai_2025")],
    "F6-R1": [("BAI07", "team"), ("BAI03", "isaca_ai_2025")], "F6-R2": [("DSS05", "isaca_ai_2025")],
    "F6-R4": [("BAI06", "isaca_ai_2025")], "F6-R6": [("BAI06", "isaca_ai_2025")],
    "F7-R1": [("MEA01", "isaca_ai_2025")], "F7-R4": [("MEA04", "isaca_ai_2025")], "F7-R5": [("APO04", "isaca_ai_2025")],
}

FEATURE_MAPPINGS = [
    ("EDM01", "RBAC com escopo e segregação de funções", "team"),
    ("EDM02", "Caso de negócio, objetivos e métricas de benefício do projeto", "team"),
    ("EDM03", "Bloqueio de gate por risco crítico não tratado", "team"),
    ("APO12", "Registro de riscos 5×5 com categorias de risco de IA (ISACA fig. 5)", "isaca_ai_2025"),
    ("APO14", "Catálogo e linhagem de ativos de dados", "isaca_ai_2025"),
    ("BAI06", "Revalidação obrigatória de gate após mudança em requisito/evidência aprovada", "team"),
    ("BAI11", "Ciclo de vida de 7 fases com Stage-Gates e tarefas", "team"),
    ("MEA01", "Indicadores com ficha técnica calculados do PostgreSQL", "team"),
    ("MEA02", "Trilha de auditoria append-only", "team"),
]


def install(apps):
    GovernanceObjective = apps.get_model("governance", "GovernanceObjective")
    ControlMapping = apps.get_model("governance", "ControlMapping")
    RequirementTemplate = apps.get_model("lifecycle", "RequirementTemplate")
    objs = {}
    for code, domain, name, name_pt, phase, trust, relevance, source, pages in OBJECTIVES:
        obj, _ = GovernanceObjective.objects.update_or_create(
            code=code,
            defaults=dict(domain=domain, name=name, name_pt=name_pt, ai_lifecycle_phase=phase, trustworthy_ai=trust,
                          ai_relevance=relevance, source=source, source_pages=pages),
        )
        objs[code] = obj
    for rt in RequirementTemplate.objects.filter(stage_template__template_version__template__organization__isnull=True):
        bases: dict[str, str] = {}
        if rt.cobit_ref in objs:
            bases[rt.cobit_ref] = "team"
        for code, basis in REQUIREMENT_MAPPINGS.get(rt.code, []):
            if basis == "isaca_ai_2025" or code not in bases:  # citação do white paper prevalece
                bases[code] = basis
        for code, basis in bases.items():
            ControlMapping.objects.update_or_create(
                objective=objs[code], requirement_template=rt, defaults={"basis": basis}
            )
    for code, feature, basis in FEATURE_MAPPINGS:
        ControlMapping.objects.get_or_create(objective=objs[code], feature=feature, defaults={"basis": basis})
