"""Conteúdo do template padrão de 7 fases (versão 1).

As associações a objetivos COBIT 2019 e práticas PMBOK são INTERPRETAÇÃO DA EQUIPE, a validar em
fontes originais; não constituem texto normativo nem certificação. O conteúdo é instalado como
DADO (migration 0002) e pode ser versionado/configurado por organização — não é constante de
regra de negócio.
"""

TEMPLATE_CODE = "padrao-7-fases"
TEMPLATE_NAME = "Ciclo padrão de implantação de plataforma de IA (7 fases)"
SOURCE_REFERENCE = (
    "Interpretação da equipe: ISACA COBIT 2019 (objetivos EDM02, APO12, APO14, BAI06, BAI07, BAI11, DSS04, MEA01); "
    "PMI PMBOK Guide 8ª ed. (abordagem híbrida). Fontes a verificar no original."
)

# (código, título, critério, obrigatório, exige_evidência, tipo_evidência, exige_validação, legal, cobit)
STAGES = [
    {
        "order": 1, "code": "oportunidade", "name": "Oportunidade e justificativa",
        "objective": "Formalizar a oportunidade, o caso de negócio, os benefícios esperados e os responsáveis.",
        "cobit_refs": "EDM02, BAI11", "pmbok_refs": "Iniciação; caso de negócio; partes interessadas",
        "requirements": [
            ("F1-R1", "Caso de negócio documentado", "Problema, benefícios, custos estimados e alternativas.",
             True, True, "business_case", True, False, "EDM02"),
            ("F1-R2", "Patrocinador e gerente designados", "Responsáveis formalmente nomeados no projeto.",
             True, False, "", True, False, "BAI11"),
            ("F1-R3", "Objetivos e indicadores-alvo definidos", "Metas mensuráveis vinculadas ao benefício.",
             True, False, "", True, False, "EDM02"),
            ("F1-R4", "Classificação preliminar dos dados", "Tipos de dados e sensibilidade previstos.",
             True, False, "", True, False, "APO14"),
        ],
    },
    {
        "order": 2, "code": "viabilidade", "name": "Viabilidade, riscos e requisitos",
        "objective": "Avaliar viabilidade técnica, econômica e de dados; identificar riscos e requisitos.",
        "cobit_refs": "APO12, APO14, BAI11", "pmbok_refs": "Requisitos; riscos; viabilidade",
        "requirements": [
            ("F2-R1", "Análise de viabilidade técnica e de custo", "Inclui capacidade de GPU/armazenamento.",
             True, True, "risk_analysis", True, False, "BAI11"),
            ("F2-R2", "Registro inicial de riscos avaliado", "Riscos com probabilidade, impacto e proprietário.",
             True, False, "", True, False, "APO12"),
            ("F2-R3", "Requisitos funcionais e não funcionais aprovados", "Lista validada pelas partes.",
             True, False, "", True, False, "BAI11"),
            ("F2-R4", "Avaliação de privacidade (LGPD) quando houver dados pessoais",
             "Base legal, minimização e encarregado consultado.", True, False, "", True, True, "APO14"),
        ],
    },
    {
        "order": 3, "code": "planejamento", "name": "Planejamento da implantação",
        "objective": "Planejar escopo, cronograma, custos, arquitetura, responsabilidades e mudanças.",
        "cobit_refs": "BAI11, BAI06", "pmbok_refs": "Planejamento; cronograma; custos; responsabilidades",
        "requirements": [
            ("F3-R1", "Plano de implantação aprovado", "Escopo, cronograma, orçamento e marcos.",
             True, True, "plan", True, False, "BAI11"),
            ("F3-R2", "Arquitetura de referência registrada", "Independente de fornecedor; alternativas avaliadas.",
             True, True, "architecture", True, False, "BAI11"),
            ("F3-R3", "Matriz RACI dos entregáveis definida", "Responsável e aprovador por entregável.",
             True, False, "", True, False, "BAI11"),
            ("F3-R4", "Plano de gestão de mudanças", "Como mudanças serão solicitadas, avaliadas e aprovadas.",
             True, False, "", True, False, "BAI06"),
        ],
    },
    {
        "order": 4, "code": "preparacao", "name": "Preparação de dados e infraestrutura",
        "objective": "Provisionar infraestrutura e preparar dados com catálogo, qualidade, segurança e continuidade.",
        "cobit_refs": "APO14, BAI06, DSS04", "pmbok_refs": "Execução; qualidade",
        "requirements": [
            ("F4-R1", "Infraestrutura provisionada e verificada", "Capacidade computacional conferida.",
             True, False, "", True, False, "BAI06"),
            ("F4-R2", "Catálogo e linhagem dos dados registrados", "Ativos de dados com origem e classificação.",
             True, True, "data_validation", True, False, "APO14"),
            ("F4-R3", "Controles de segurança de base aplicados", "Acesso, rede, segredos e registros.",
             True, True, "security_report", True, False, "DSS04"),
            ("F4-R4", "Plano de backup e recuperação", "Escopo, frequência, RPO/RTO pretendidos.",
             True, True, "backup_recovery", True, False, "DSS04"),
        ],
    },
    {
        "order": 5, "code": "poc", "name": "Prova de conceito e validação",
        "objective": "Validar a solução em escopo controlado contra critérios de sucesso previamente definidos.",
        "cobit_refs": "BAI11, APO12", "pmbok_refs": "Entregas incrementais; validação",
        "requirements": [
            ("F5-R1", "Critérios de sucesso da PoC definidos antes da execução", "Métricas e limiares.",
             True, False, "", True, False, "BAI11"),
            ("F5-R2", "Resultado da PoC registrado", "Relatório com métricas observadas.",
             True, True, "test", True, False, "BAI11"),
            ("F5-R3", "Avaliação de qualidade e viés do modelo", "Testes de desempenho e equidade aplicáveis.",
             True, True, "test", True, False, "APO12"),
            ("F5-R4", "Riscos reavaliados após a PoC", "Atualização do registro de riscos.",
             True, False, "", True, False, "APO12"),
        ],
    },
    {
        "order": 6, "code": "homologacao", "name": "Homologação e entrada em produção",
        "objective": "Homologar, aprovar a mudança e obter aceite operacional para entrada em produção.",
        "cobit_refs": "BAI07, BAI06, DSS04", "pmbok_refs": "Transição; aceite; encerramento da entrega",
        "requirements": [
            ("F6-R1", "Testes de homologação aprovados", "Funcionais, desempenho e integração.",
             True, True, "test", True, False, "BAI07"),
            ("F6-R2", "Relatório de segurança aprovado", "Vulnerabilidades tratadas ou aceitas formalmente.",
             True, True, "security_report", True, False, "BAI07"),
            ("F6-R3", "Teste de recuperação executado", "Restauração validada em ambiente controlado.",
             True, True, "backup_recovery", True, False, "DSS04"),
            ("F6-R4", "Mudança de produção aprovada", "Janela, plano de retorno e comunicação.",
             True, False, "", True, False, "BAI06"),
            ("F6-R5", "Termo de aceite operacional", "Aceite formal pela operação e patrocinador.",
             True, True, "acceptance", True, False, "BAI07"),
        ],
    },
    {
        "order": 7, "code": "operacao", "name": "Operação e melhoria contínua",
        "objective": "Acompanhar continuamente desempenho, riscos, custos e lições aprendidas.",
        "cobit_refs": "MEA01, DSS04", "pmbok_refs": "Benefícios; melhoria contínua",
        "has_exit_gate": False,
        "requirements": [
            ("F7-R1", "Indicadores operacionais monitorados", "Ficha técnica e periodicidade definidas.",
             True, False, "", True, False, "MEA01"),
            ("F7-R2", "Revisão periódica de riscos", "Registro com data da última revisão.",
             False, False, "", True, False, "APO12"),
            ("F7-R3", "Lições aprendidas registradas", "Ao menos uma lição revisada.",
             False, False, "", True, False, "MEA01"),
        ],
    },
]


# ---------------------------------------------------------------------------------------------- Versão 2
# Enriquecida com o white paper ISACA (2025) "Leveraging COBIT for Effective AI System Governance":
# elementos de IA confiável (p. 11–13), aplicação dos domínios ao ciclo de vida de IA (p. 13–14), categorias de
# risco de IA (fig. 5, p. 16) e práticas do caso de uso (EDM05.01, BAI03.06, MEA04.06, APO04.04; p. 14–15).
SOURCE_REFERENCE_V2 = (
    "Interpretação da equipe: COBIT 2019 e PMBOK 8ª ed.; v2 incorpora ISACA, Leveraging COBIT for Effective "
    "AI System Governance (2025), p. 11–16."
)

V2_ADDITIONS = {
    1: [("F1-R5", "Alinhamento ético e de valor da iniciativa de IA",
         "Impacto em partes interessadas, sociedade e ambiente avaliado; uso alinhado aos valores da organização.",
         True, False, "", True, False, "EDM01")],
    2: [("F2-R5", "Riscos de IA classificados nas cinco categorias ISACA",
         "Uso ético; política e governança; tecnologia e infraestrutura; operacional e organizacional; emergente "
         "e estratégico — com probabilidade e impacto considerando controles atuais.", True, False, "", True, False,
         "APO12")],
    3: [("F3-R5", "Estrutura de supervisão de IA definida",
         "Comitê ou fórum multidisciplinar (TI, dados, conformidade/privacidade, negócio) com papéis em RACI.",
         True, False, "", True, False, "EDM05"),
        ("F3-R6", "Política de transparência e registro de decisões do sistema de IA",
         "Como saídas serão explicadas, registradas e comunicadas aos usuários.", True, False, "", True, False,
         "EDM01")],
    4: [("F4-R5", "Critérios de qualidade de dados para IA definidos",
         "Critérios de exatidão, relevância e avaliação periódica de vieses nos dados.", True, False, "", True,
         False, "APO11"),
        ("F4-R6", "Ativos que hospedam a plataforma de IA inventariados e protegidos",
         "Inventário e proteção da infraestrutura de dados, treinamento e operação.", True, False, "", True, False,
         "BAI09")],
    5: [("F5-R5", "Explicabilidade das saídas documentada",
         "Técnicas e limites de explicação das decisões do modelo registrados.", True, False, "", True, False,
         "EDM01")],
    6: [("F6-R6", "Processo de atualização e retreinamento controlado do modelo",
         "Mudanças de modelo/algoritmo passam por gestão de mudanças antes da produção.", True, False, "", True,
         False, "BAI06")],
    7: [("F7-R4", "Auditoria periódica de qualidade e equidade dos dados de treinamento",
         "Avaliação recorrente com registro de resultados e ações.", False, False, "", True, False, "MEA04"),
        ("F7-R5", "Capacitação contínua das equipes em IA e governança",
         "Plano de atualização sobre tendências, requisitos de governança e ética.", False, False, "", True, False,
         "APO04")],
}


def stages_v2():
    import copy

    stages = copy.deepcopy(STAGES)
    for st in stages:
        st["requirements"] = list(st["requirements"]) + V2_ADDITIONS.get(st["order"], [])
    return stages


def install(apps, *, organization=None, number=1, stages=None, source_reference=None, notes=""):
    """Instala o template padrão. Usa `apps.get_model` para ser seguro em migrations. Idempotente."""
    from django.utils import timezone

    LifecycleTemplate = apps.get_model("lifecycle", "LifecycleTemplate")
    LifecycleTemplateVersion = apps.get_model("lifecycle", "LifecycleTemplateVersion")
    StageTemplate = apps.get_model("lifecycle", "StageTemplate")
    RequirementTemplate = apps.get_model("lifecycle", "RequirementTemplate")

    template, _ = LifecycleTemplate.objects.get_or_create(
        organization=organization, code=TEMPLATE_CODE, defaults={"name": TEMPLATE_NAME}
    )
    version, created = LifecycleTemplateVersion.objects.get_or_create(
        template=template, number=number,
        defaults={"status": "published", "published_at": timezone.now(),
                  "source_reference": source_reference or SOURCE_REFERENCE, "notes": notes},
    )
    if not created:
        return version
    for st in stages or STAGES:
        extra = {}
        if st.get("requires_responsible_ai"):  # campo inexistente em estados históricos anteriores à v3
            extra["requires_responsible_ai"] = True
        stage = StageTemplate.objects.create(
            template_version=version, order=st["order"], code=st["code"], name=st["name"],
            objective=st["objective"], cobit_refs=st["cobit_refs"], pmbok_refs=st["pmbok_refs"],
            has_exit_gate=st.get("has_exit_gate", True), **extra,
        )
        for i, (code, title, desc, mand, ev, kind, val, legal, cobit) in enumerate(st["requirements"], start=1):
            RequirementTemplate.objects.create(
                stage_template=stage, order=i, code=code, title=title, description=desc, mandatory=mand,
                requires_evidence=ev, evidence_kind=kind, requires_validation=val, is_legal=legal, cobit_ref=cobit,
            )
    return version


# ---------------------------------------------------------------------------------------------- Versão 3
# Incorpora PMI PMBOK Guide 8ª ed. (2025): Apêndice X3 (IA) — avaliação de uso responsável exigida no gate de
# homologação (fase 6); Governance Performance Domain 2.1.6.6 (Manage Project Knowledge) — lições na fase 7.
SOURCE_REFERENCE_V3 = (
    "Interpretação da equipe: COBIT 2019; ISACA (2025) p. 11–16; PMI PMBOK Guide 8ª ed. (2025): 2.1, 2.7, 4.2, X3."
)


def stages_v3():
    stages = stages_v2()
    for st in stages:
        if st["order"] == 6:
            st["requires_responsible_ai"] = True
            st["requirements"] = list(st["requirements"]) + [
                ("F6-R7", "Avaliação de uso responsável de IA concluída",
                 "Viés, privacidade, responsabilização, confiabilidade, segurança, transparência, direitos autorais e "
                 "sustentabilidade tratados ou justificados como não aplicáveis, com humano responsável definido.",
                 True, False, "", True, False, "EDM01"),
            ]
        if st["order"] == 1:
            st["requirements"] = list(st["requirements"]) + [
                ("F1-R6", "Abordagem de desenvolvimento e estratégia de adoção de IA definidas",
                 "Abordagem preditiva, adaptativa ou híbrida e nível de supervisão humana (automação, assistência "
                 "ou ampliação) registrados no projeto.", True, False, "", True, False, "BAI11"),
            ]
    return stages


# ---------------------------------------------------------------------------------------------- Versão 4
# Ajustes orientados pela 1ª rodada do questionário acadêmico com profissionais (n = 9 na análise principal; ver
# docs/pesquisa/evolucao-orientada-pela-pesquisa.md). Só texto e configuração: nenhuma regra nova de negócio.
#   A02 — infraestrutura foi o obstáculo PoC→produção mais citado: F2-R1 passa a exigir o financiamento previsto.
#   A06 — privacidade/segurança como riscos dominantes e uso ético pior avaliado: avaliação preliminar na fase 2.
#   A09 — letramento e definição da necessidade: F1-R1 exige alternativas sem IA e justificativa para usar IA.
SOURCE_REFERENCE_V4 = SOURCE_REFERENCE_V3 + " v4: ajustes derivados da pesquisa com profissionais (rodada 1)."

V4_DESCRIPTIONS = {
    "F1-R1": "Problema, benefícios, custos estimados e alternativas avaliadas, inclusive soluções sem IA, com a "
             "justificativa para o uso de IA.",
    "F2-R1": "Inclui a capacidade de GPU/armazenamento necessária à operação em produção e a fonte de "
             "financiamento prevista para adquiri-la e mantê-la.",
}
V4_ADDITIONS = {
    2: [("F2-R6", "Avaliação preliminar de uso responsável de IA",
         "Riscos de privacidade, segurança, viés e transparência identificados desde a viabilidade, com humano "
         "responsável definido; a avaliação completa continua exigida no gate de homologação.",
         True, False, "", True, False, "EDM01")],
}


def stages_v4():
    stages = stages_v3()
    for st in stages:
        reqs = []
        for req in st["requirements"]:
            if req[0] in V4_DESCRIPTIONS:
                req = (req[0], req[1], V4_DESCRIPTIONS[req[0]], *req[3:])
            reqs.append(req)
        st["requirements"] = reqs + V4_ADDITIONS.get(st["order"], [])
    return stages
