"""Cenários SINTÉTICOS da dinâmica de avaliação (sete situações; roteiro em PDF no material do trabalho).

Cada projeto fictício fica parado num ponto em que um "fato" plausível do mundo da IA exige uma ação no sistema.
Os situações foram escolhidas a partir dos achados da 1ª rodada da pesquisa (infraestrutura e orçamento,
privacidade e segurança, viés e uso ético, degradação em operação, decisões sem registro).
Nenhum dado real: organizações, pessoas e valores são fictícios.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

DEMO_ORG_PUBLIC = "Secretaria Estadual Demonstrativa Gama"


def _evidence(u, req, title):
    from apps.evidence import services as ev

    art = ev.create_evidence(
        actor=u["demo.tecnico"], project=req.stage.project, requirement=req, kind=req.evidence_kind or "other",
        title=title, uploaded=SimpleUploadedFile("evidencia.txt", f"{title} (sintética).\n".encode()),
    )
    ev.inspect_version(art.pk, actor=u["demo.seguranca"], release=True, note="Inspeção manual (demo)")
    ev.review_evidence(art.pk, actor=u["demo.aprovador"], decision="approved", comment="Conforme critério (demo).")


def _complete(u, stage, *, skip=()):
    from apps.lifecycle import services as lc

    for req in stage.requirements.filter(mandatory=True):
        if req.code in skip:
            continue
        if req.requires_evidence:
            _evidence(u, req, f"{req.code} — {req.title}")
        lc.fulfill_requirement(req.pk, actor=u["demo.gerente"], note=f"Atendimento registrado de {req.code} (demo).")
        lc.validate_requirement(req.pk, actor=u["demo.seguranca"], decision="approved", comment="Validado (demo).")


def _responsible_ai(u, project, *, pending=()):
    from apps.governance import services as gov
    from apps.governance.models import ResponsibleAIFactor

    for factor in ResponsibleAIFactor.values:
        if factor in pending:
            continue
        gov.assess_responsible_ai(project, actor=u["demo.seguranca"], factor=factor, status="addressed",
                                  measures=f"Medidas registradas para o fator {factor} (demo).",
                                  accountable=u["demo.patrocinio"])


def _advance(u, project, until_order):
    """Aprova os gates das fases 1..until_order-1, respeitando segregação (quem atende ≠ quem valida ≠ quem aprova)."""
    from apps.governance import services as gov

    for order in range(1, until_order):
        stage = project.stages.get(order=order)
        if stage.requires_responsible_ai:
            _responsible_ai(u, project)
        _complete(u, stage)
        gate = gov.request_gate(stage.pk, actor=u["demo.gerente"])
        gov.approve_gate(stage.pk, actor=u["demo.aprovador"], justification="Critérios atendidos (demo).",
                         request_number=gate.request_number)
    project.refresh_from_db()
    return project.stages.get(order=until_order)


def create_public_org(users):
    from apps.organizations.models import Membership, Organization
    from apps.organizations.services import bootstrap_role

    org = Organization.objects.create(
        name=DEMO_ORG_PUBLIC, slug="demo-gama", is_demo=True,
        description="Órgão público fictício para demonstração (dados sintéticos).",
    )
    for user, role in users.values():
        Membership.objects.create(organization=org, user=user, job_title=user.full_name)
        bootstrap_role(organization=org, user=user, role=role, reason="seed_demo (cenários)")
    return org


def create_scenarios(org_private, org_public, u, today):
    from apps.analytics import services as analytics
    from apps.lifecycle import services as lc
    from apps.projects.models import Portfolio
    from apps.projects.services import create_project
    from apps.risks import services as risks

    pf_priv = Portfolio.objects.get(organization=org_private)
    pf_pub = Portfolio.objects.create(organization=org_public, name="Programa de IA no serviço público",
                                      owner=u["demo.portfolio"], description="Iniciativas fictícias do órgão.")
    common = dict(sponsor=u["demo.patrocinio"], manager=u["demo.gerente"], technical_lead=u["demo.tecnico"])

    # C1 — Aquisição de infraestrutura de GPUs (setor público): financiamento e prazo de entrega.
    gpu = create_project(
        actor=u["demo.gerente"], organization=org_public, portfolio=pf_pub, code="GOV-2026-01",
        name="Aquisição de infraestrutura de GPUs para processamento de modelos de IA",
        description="Contratação e implantação de servidores com GPUs para treinar e executar modelos no datacenter do órgão.",
        business_case="Hoje as PoCs dependem de nuvem pública e não avançam por custo recorrente e restrições de dados.",
        business_objectives="Capacidade própria para inferência de modelos de linguagem e de visão.",
        target_indicators="Capacidade instalada ≥ 8 GPUs; ocupação média ≥ 60% no 1º ano.",
        platform_type="data", deployment_approach="on_prem", development_approach="predictive",
        priority="high", criticality="high", data_classification="internal",
        start_date=today - timedelta(days=45), due_date=today + timedelta(days=330),
        planned_cost=Decimal("2400000.00"), **common,
    )
    st2 = _advance(u, gpu, 2)
    _complete(u, st2, skip=("F2-R1",))  # F2-R1 (v4) exige a fonte de financiamento: fica pendente
    risks.create_risk(actor=u["demo.gerente"], project=gpu, title="Contingenciamento do orçamento do exercício",
                      category="cost", ai_category="operational", probability=4, impact=5, owner=u["demo.patrocinio"],
                      cause="Decreto de contingenciamento (fictício)", consequence="Aquisição adiada para o próximo exercício")
    risks.create_risk(actor=u["demo.gerente"], project=gpu, title="Prazo de entrega das GPUs superior a 180 dias",
                      category="vendor", ai_category="technology", probability=4, impact=3, owner=u["demo.tecnico"])
    risks.add_cost(actor=u["demo.gerente"], project=gpu, category="gpu", kind="planned", amount=Decimal("1900000.00"),
                   entry_date=today - timedelta(days=30), justification="Estimativa de mercado (sintética)")
    risks.add_cost(actor=u["demo.gerente"], project=gpu, category="infra", kind="planned", amount=Decimal("500000.00"),
                   entry_date=today - timedelta(days=30), justification="Energia, refrigeração e rede (sintética)")
    risks.propose_decision(actor=u["demo.gerente"], project=gpu, topic="architecture",
                           agenda="Capacidade provisória enquanto a aquisição não é concluída",
                           alternatives="Aguardar a entrega; nuvem pública por 6 meses; parceria com outro órgão",
                           decision="Contratar nuvem pública por 6 meses apenas para dados públicos",
                           rationale="Evitar a paralisação das PoCs sem expor dados restritos",
                           risks_considered="Custo recorrente; dependência de fornecedor")

    # C2 — Assistente virtual ao cidadão com IA generativa e RAG (setor público): dado pessoal encontrado na PoC.
    cid = create_project(
        actor=u["demo.gerente"], organization=org_public, portfolio=pf_pub, code="GOV-2026-02",
        name="Assistente virtual de atendimento ao cidadão (IA generativa com RAG)",
        description="Chatbot que responde dúvidas sobre serviços com base em normas e cartas de serviço do órgão.",
        business_case="Reduzir filas do atendimento presencial e padronizar respostas.",
        target_indicators="Resolução no 1º contato ≥ 60%; respostas com fonte citada = 100%.",
        platform_type="genai", deployment_approach="hybrid", development_approach="adaptive",
        ai_adoption_strategy="assistance", priority="high", criticality="high", data_classification="confidential",
        start_date=today - timedelta(days=150), due_date=today + timedelta(days=120),
        planned_cost=Decimal("680000.00"), **common,
    )
    _advance(u, cid, 5)
    base = analytics.create_asset(actor=u["demo.gerente"], project=cid, name="Histórico de atendimentos (sintético)",
                                  kind="dataset", purpose="Avaliar respostas do assistente", owner=u["demo.tecnico"],
                                  source_system="Central de atendimento (fictícia)", contains_personal_data=True,
                                  classification="confidential")
    rag = analytics.create_asset(actor=u["demo.gerente"], project=cid, name="Índice de busca das cartas de serviço",
                                 kind="model", purpose="Recuperação de trechos para as respostas", owner=u["demo.tecnico"])
    analytics.add_lineage(actor=u["demo.gerente"], source=base, target=rag, transformation="Seleção de perguntas frequentes")
    risks.create_risk(actor=u["demo.gerente"], project=cid, title="CPF de cidadãos gravado nos registros de conversa",
                      category="privacy", ai_category="policy", probability=5, impact=5, owner=u["demo.seguranca"],
                      cause="Registros completos ativados durante a PoC", consequence="Violação da LGPD")
    risks.create_risk(actor=u["demo.gerente"], project=cid, title="Resposta inventada sobre prazo de benefício",
                      category="quality", ai_category="emerging", probability=3, impact=4, owner=u["demo.tecnico"])

    # C3 — Detecção de fraudes em transações (setor privado): viés identificado na homologação.
    fraude = create_project(
        actor=u["demo.gerente"], organization=org_private, portfolio=pf_priv, code="IA-2026-03",
        name="Detecção de fraudes em transações com aprendizado de máquina",
        description="Modelo de classificação que sinaliza transações suspeitas para análise humana.",
        business_case="Reduzir perdas com fraude sem bloquear clientes legítimos.",
        target_indicators="Precisão ≥ 90%; diferença de falsos positivos entre regiões ≤ 10%.",
        platform_type="mlops", deployment_approach="private_cloud", development_approach="hybrid",
        ai_adoption_strategy="assistance", priority="critical", criticality="high", data_classification="restricted",
        start_date=today - timedelta(days=240), due_date=today + timedelta(days=45),
        planned_cost=Decimal("1250000.00"), **common,
    )
    st6 = _advance(u, fraude, 6)
    _responsible_ai(u, fraude, pending=("bias", "transparency"))
    _complete(u, st6, skip=("F6-R7",))
    r_bias = risks.create_risk(actor=u["demo.gerente"], project=fraude,
                               title="Falsos positivos duas vezes maiores em uma região",
                               category="ethics", ai_category="ethical", probability=4, impact=4, owner=u["demo.tecnico"],
                               cause="Desbalanceamento regional nos dados de treino", consequence="Bloqueio indevido de clientes")
    risks.add_treatment(r_bias.pk, actor=u["demo.gerente"], strategy="mitigate",
                        description="Rebalancear a base e definir limiar por região, com revisão humana obrigatória",
                        owner=u["demo.tecnico"], due_date=today + timedelta(days=15))
    risks.propose_decision(actor=u["demo.gerente"], project=fraude, topic="risk",
                           agenda="Entrar em produção com o viés identificado?",
                           alternatives="Adiar até corrigir; entrar só com revisão humana de todos os alertas; cancelar",
                           decision="Adiar a entrada em produção até nova rodada de testes de equidade",
                           rationale="O impacto em clientes legítimos supera o ganho de antecipar a implantação")

    # C4 — Inspeção visual de qualidade na indústria (setor privado, borda): degradação em operação.
    visao = create_project(
        actor=u["demo.gerente"], organization=org_private, portfolio=pf_priv, code="IA-2026-04",
        name="Inspeção visual de qualidade com visão computacional (borda)",
        description="Câmeras e modelo embarcado identificam defeitos de peças na linha de produção.",
        business_case="Reduzir refugo e inspeção manual repetitiva.",
        target_indicators="Acurácia ≥ 95%; refugo -20% em 6 meses.",
        platform_type="vision", deployment_approach="edge", development_approach="hybrid",
        ai_adoption_strategy="automation", priority="medium", criticality="medium", data_classification="internal",
        start_date=today - timedelta(days=400), due_date=today - timedelta(days=30),
        planned_cost=Decimal("380000.00"), **common,
    )
    st7 = _advance(u, visao, 7)
    risks.create_risk(actor=u["demo.gerente"], project=visao, title="Queda de acurácia após troca da iluminação da linha",
                      category="quality", ai_category="technology", probability=4, impact=3, owner=u["demo.tecnico"],
                      cause="Mudança no ambiente não comunicada ao time de IA", consequence="Peças defeituosas aprovadas")
    task = lc.create_task(actor=u["demo.gerente"], project=visao, stage=st7,
                          title="Coletar novas imagens e retreinar o modelo", assignee=u["demo.tecnico"],
                          due_date=today + timedelta(days=10))
    lc.update_task_status(task.pk, actor=u["demo.gerente"], status="doing")
    lesson = analytics.create_lesson(
        actor=u["demo.gerente"], project=visao, title="Mudanças no ambiente físico afetam modelos de visão",
        context="Acurácia caiu de 96% para 88% após a troca de luminárias (dados sintéticos).",
        lesson="Alterações de iluminação, câmera ou layout precisam passar pela gestão de mudanças do projeto de IA.",
        recommendation="Incluir o time de IA no fluxo de mudanças da manutenção e monitorar a acurácia semanalmente.",
    )
    analytics.approve_lesson(lesson.pk, actor=u["demo.portfolio"], visibility="organization")

    # C7 — Controle de qualidade de laudos periciais com IA (setor público + universidade): formalização da parceria.
    # Cenário INSPIRADO em caso real, anonimizado: nomes de instituições, datas e metas foram retirados ou trocados.
    laudo = create_project(
        actor=u["demo.gerente"], organization=org_public, portfolio=pf_pub, code="GOV-2026-03",
        name="Controle de qualidade de laudos periciais com IA (parceria com universidade pública)",
        description="Modelos multimodais (texto, imagem e vídeo) como copiloto do perito para apontar lacunas, "
                    "inconsistências e falta de padronização em laudos, integrados ao sistema policial (fictício).",
        business_case="Fortalecer a qualidade e a confiabilidade da prova pericial, alinhado ao procedimento operacional "
                      "padrão do órgão e ao objetivo estratégico de controle de qualidade do laudo (fictício).",
        business_objectives="Padronizar laudos; reduzir omissões; apoiar a revisão sem substituir o perito.",
        target_indicators="Laudos com checklist do procedimento atendido ≥ 90%; tempo de revisão -30%.",
        platform_type="genai", deployment_approach="on_prem", development_approach="hybrid",
        ai_adoption_strategy="assistance", priority="high", criticality="high", data_classification="restricted",
        start_date=today - timedelta(days=300), due_date=today + timedelta(days=420),
        planned_cost=Decimal("1600000.00"), **common,
    )
    st_l2 = _advance(u, laudo, 2)
    _complete(u, st_l2, skip=("F2-R4",))  # avaliação LGPD depende do acordo assinado: requisito LEGAL, sem exceção
    for i, (title, status) in enumerate([
        ("Manifestação de interesse da universidade", "done"), ("Reunião de alinhamento", "done"),
        ("Minutas do termo de cooperação técnica e do plano de trabalho", "done"),
        ("Parecer do jurídico da universidade", "done"), ("Elaborar modificações requisitadas (universidade)", "done"),
        ("Parecer da assessoria jurídica do órgão", "done"), ("Elaborar o plano de gestão de dados", "done"),
        ("Elaborar modificações requisitadas (órgão)", "done"), ("Assinatura do acordo", "todo"),
        ("Publicação do acordo", "todo"),
    ]):
        t = lc.create_task(actor=u["demo.gerente"], project=laudo, stage=st_l2, title=title, assignee=u["demo.gerente"],
                           due_date=today + timedelta(days=-90 + 12 * i))
        if status == "done":
            lc.update_task_status(t.pk, actor=u["demo.gerente"], status="done")
    risks.create_risk(actor=u["demo.gerente"], project=laudo, title="Atraso na assinatura do acordo de cooperação",
                      category="schedule", ai_category="operational", probability=4, impact=4, owner=u["demo.patrocinio"],
                      cause="Rodadas sucessivas de pareceres jurídicos",
                      consequence="Equipe da universidade sem acesso aos dados")
    r_dados = risks.create_risk(actor=u["demo.gerente"], project=laudo,
                                title="Laudos de crimes contra a vida com dados pessoais sensíveis",
                                category="privacy", ai_category="policy", probability=4, impact=5,
                                owner=u["demo.seguranca"], cause="Vítimas, testemunhas e imagens nos documentos",
                                consequence="Exposição de dados sensíveis e nulidade de provas")
    risks.add_treatment(r_dados.pk, actor=u["demo.gerente"], strategy="mitigate",
                        description="Plano de gestão de dados com anonimização, ambiente isolado e acesso nominal",
                        owner=u["demo.seguranca"], due_date=today + timedelta(days=30))
    risks.create_risk(actor=u["demo.gerente"], project=laudo, title="Servidores com GPU ainda não adquiridos",
                      category="gpu", ai_category="technology", probability=4, impact=3, owner=u["demo.tecnico"])
    analytics.create_asset(actor=u["demo.gerente"], project=laudo, name="Acervo de laudos periciais (anonimizado, fictício)",
                           kind="dataset", purpose="Avaliar completude e consistência dos laudos", owner=u["demo.tecnico"],
                           source_system="Sistema policial (fictício)", contains_personal_data=True,
                           classification="restricted")
    risks.propose_decision(actor=u["demo.gerente"], project=laudo, topic="scope",
                           agenda="Iniciar testes com laudos antes da assinatura do acordo?",
                           alternatives="Aguardar a assinatura; usar só laudos sintéticos até a assinatura",
                           decision="Usar apenas laudos sintéticos até a publicação do acordo",
                           rationale="Sem instrumento jurídico não há base legal para compartilhar dados reais")

    # Situações nos dois projetos originais (C5 e C6) ficam nos estados criados por seed_demo:
    # IA-2026-01 com risco crítico sem tratamento na fase 1; IA-2026-02 parado na fase 1 sem registro de decisões.
    for org in (org_private, org_public):
        analytics.capture_snapshots(actor=u["demo.portfolio"], organization=org)
        analytics.generate_insights(actor=u["demo.portfolio"], organization=org)
