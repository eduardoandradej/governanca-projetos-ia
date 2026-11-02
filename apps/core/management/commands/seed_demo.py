"""Carga de dados SINTÉTICOS para desenvolvimento/demonstração (opt-in explícito).

Uso:  python manage.py seed_demo --confirm-demo

- Não cria senhas fixas: gera senha aleatória por execução e a exibe UMA vez no terminal
  (ou usa a variável DEMO_PASSWORD, se definida localmente).
- Recusa-se a rodar com DEBUG=False, salvo --allow-non-debug (ambiente de demonstração isolado).
- Organizações criadas recebem is_demo=True (RN-022): tudo que derivar delas é exibido como demonstrativo.
- Idempotente: se as organizações demonstrativas já existirem, não duplica dados.
"""

import os
import secrets
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.lifecycle import services as lifecycle  # noqa: I001
from apps.organizations.models import Membership, Organization, Role
from apps.organizations.services import bootstrap_role
from apps.projects.models import Portfolio
from apps.projects.services import create_project

DEMO_ORG = "Organização Demonstrativa Alfa"
DEMO_ORG_B = "Organização Demonstrativa Beta"

USERS = [
    # (username, nome fictício, papel org-wide)
    ("demo.admin", "Administração Demo", Role.ORG_ADMIN),
    ("demo.portfolio", "Gestão de Portfólio Demo", Role.PORTFOLIO_MANAGER),
    ("demo.patrocinio", "Patrocínio Demo", Role.SPONSOR),
    ("demo.gerente", "Gerência de Projeto Demo", Role.PROJECT_MANAGER),
    ("demo.tecnico", "Execução Técnica Demo", Role.TECH_EXECUTOR),
    ("demo.seguranca", "Segurança e Conformidade Demo", Role.SECURITY_COMPLIANCE),
    ("demo.aprovador", "Aprovação de Gates Demo", Role.GATE_APPROVER),
    ("demo.auditor", "Auditoria Demo", Role.AUDITOR),
    ("demo.leitor", "Leitura Demo", Role.READER),
]


class Command(BaseCommand):
    help = "Cria dados sintéticos de demonstração (exige --confirm-demo)."

    def add_arguments(self, parser):
        parser.add_argument("--confirm-demo", action="store_true", help="Confirma a criação de dados demonstrativos.")
        parser.add_argument("--allow-non-debug", action="store_true", help="Permite rodar com DEBUG=False.")

    def handle(self, *args, **opts):
        if not opts["confirm_demo"]:
            raise CommandError("Operação demonstrativa: informe --confirm-demo para prosseguir.")
        if not settings.DEBUG and not opts["allow_non_debug"]:
            raise CommandError("DEBUG=False: use --allow-non-debug somente em ambiente de demonstração isolado.")
        if Organization.objects.filter(name=DEMO_ORG).exists():
            self.stdout.write(self.style.WARNING("Dados demonstrativos já existem; nada foi alterado."))
            return
        password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(12)
        with transaction.atomic():
            users = self._create_users(password)
            org = Organization.objects.create(
                name=DEMO_ORG, slug="demo-alfa", is_demo=True,
                description="Organização fictícia para demonstração do MVP (dados sintéticos).",
            )
            for user, role in users.values():
                Membership.objects.create(organization=org, user=user, job_title=user.full_name)
                bootstrap_role(organization=org, user=user, role=role, reason="seed_demo")
            self._create_projects(org, users)
            # Segunda organização para demonstrar isolamento entre organizações.
            org_b = Organization.objects.create(
                name=DEMO_ORG_B, slug="demo-beta", is_demo=True, description="Organização fictícia para teste de isolamento."
            )
            outsider = get_user_model().objects.create_user(
                username="demo.beta.gerente", password=password, full_name="Gerência Beta Demo"
            )
            sponsor_b = get_user_model().objects.create_user(
                username="demo.beta.patrocinio", password=password, full_name="Patrocínio Beta Demo"
            )
            for u, r in ((outsider, Role.PROJECT_MANAGER), (sponsor_b, Role.SPONSOR)):
                Membership.objects.create(organization=org_b, user=u)
                bootstrap_role(organization=org_b, user=u, role=r, reason="seed_demo")
            create_project(
                actor=outsider, organization=org_b, code="BETA-01", name="Projeto confidencial da Beta (fictício)",
                description="Não deve ser visível para usuários da Alfa.", business_case="Demonstração de isolamento.",
                platform_type="mlops", deployment_approach="public_cloud", sponsor=sponsor_b, manager=outsider,
            )
        self.stdout.write(self.style.SUCCESS("Dados demonstrativos criados."))
        self.stdout.write("Usuários: " + ", ".join(u for u, *_ in USERS) + ", demo.beta.gerente, demo.beta.patrocinio")
        if os.environ.get("DEMO_PASSWORD"):
            self.stdout.write("Senha: a definida em DEMO_PASSWORD.")
        else:
            self.stdout.write(self.style.WARNING(f"Senha gerada (exibida apenas agora): {password}"))

    def _create_users(self, password):
        User = get_user_model()
        result = {}
        for username, name, role in USERS:
            user = User.objects.create_user(username=username, password=password, full_name=name)
            result[username] = (user, role)
        return result

    def _create_projects(self, org, users):
        u = {k: v[0] for k, v in users.items()}
        portfolio = Portfolio.objects.create(
            organization=org, name="Portfólio de IA corporativa", owner=u["demo.portfolio"],
            description="Iniciativas fictícias de plataformas de IA.",
        )
        today = date.today()
        p1 = create_project(
            actor=u["demo.gerente"], organization=org, portfolio=portfolio, code="IA-2026-01",
            name="Plataforma corporativa de IA generativa (on-premises)",
            description="Implantação fictícia de plataforma de LLM em infraestrutura local com GPUs.",
            business_case="Reduzir o tempo entre prova de conceito e produção, com governança e controle de custos.",
            business_objectives="Disponibilizar assistentes internos; padronizar MLOps; reduzir custos de nuvem.",
            target_indicators="Tempo PoC→produção ≤ 6 meses; disponibilidade ≥ 99,5%.",
            platform_type="genai", deployment_approach="on_prem",
            technology_metadata={"Orquestração": "Kubernetes (ex.)", "Automação": "Ansible (ex.)"},
            sponsor=u["demo.patrocinio"], manager=u["demo.gerente"], technical_lead=u["demo.tecnico"],
            priority="high", criticality="high", data_classification="confidential",
            start_date=today - timedelta(days=60), due_date=today + timedelta(days=240),
            planned_cost=Decimal("850000.00"),
        )
        create_project(
            actor=u["demo.gerente"], organization=org, portfolio=portfolio, code="IA-2026-02",
            name="Plataforma de MLOps em nuvem híbrida",
            description="Projeto fictício para padronizar treinamento e implantação de modelos.",
            business_case="Reprodutibilidade e rastreabilidade de modelos entre ambientes.",
            platform_type="mlops", deployment_approach="hybrid", sponsor=u["demo.patrocinio"],
            manager=u["demo.gerente"], priority="medium", criticality="medium",
            start_date=today - timedelta(days=20), due_date=today + timedelta(days=300),
            planned_cost=Decimal("420000.00"),
        )
        stage1 = p1.stages.get(order=1)
        for title, assignee, days, status in [
            ("Levantar casos de uso prioritários", u["demo.gerente"], -10, "done"),
            ("Estimar capacidade de GPU e armazenamento", u["demo.tecnico"], -3, "doing"),
            ("Mapear dados pessoais envolvidos", u["demo.seguranca"], 5, "todo"),
        ]:
            task = lifecycle.create_task(
                actor=u["demo.gerente"], project=p1, stage=stage1, title=title, assignee=assignee,
                due_date=today + timedelta(days=days),
            )
            if status != "todo":
                lifecycle.update_task_status(task.pk, actor=u["demo.gerente"], status=status)
        req = stage1.requirements.get(code="F1-R2")
        lifecycle.fulfill_requirement(
            req.pk, actor=u["demo.gerente"], note="Patrocínio e gerência nomeados no termo de abertura (fictício)."
        )
        lifecycle.validate_requirement(req.pk, actor=u["demo.seguranca"], decision="approved", comment="Conferido no termo.")
        self._create_governance_data(p1, u, today)

    def _create_governance_data(self, p1, u, today):
        """Riscos, custos, evidência, decisão, catálogo de dados e insights — todos sintéticos."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.analytics import services as analytics
        from apps.evidence import services as evidence
        from apps.risks import services as risks

        risks.create_risk(actor=u["demo.gerente"], project=p1, title="Exposição de dados pessoais no treinamento",
                          category="privacy", ai_category="policy", probability=5, impact=5, owner=u["demo.seguranca"],
                          cause="Bases de atendimento com dados pessoais", consequence="Sanção e dano reputacional")
        r2 = risks.create_risk(actor=u["demo.gerente"], project=p1, title="Capacidade de GPU insuficiente",
                               category="gpu", ai_category="technology", probability=4, impact=3, owner=u["demo.tecnico"])
        risks.add_treatment(r2.pk, actor=u["demo.gerente"], strategy="mitigate",
                            description="Reserva de capacidade e fila de priorização de jobs", owner=u["demo.tecnico"],
                            due_date=today + timedelta(days=20))
        risks.create_risk(actor=u["demo.gerente"], project=p1, title="Viés nas respostas do assistente",
                          category="ethics", ai_category="ethical", probability=3, impact=4, owner=u["demo.tecnico"])
        for cat, kind, amount, just in [("gpu", "planned", "300000.00", "Plano de capacidade (sintético)"),
                                        ("gpu", "actual", "120000.00", "Nota fiscal sintética 001"),
                                        ("services", "actual", "45000.00", "Consultoria sintética")]:
            risks.add_cost(actor=u["demo.gerente"], project=p1, category=cat, kind=kind, amount=Decimal(amount),
                           entry_date=today - timedelta(days=10), justification=just)
        req = p1.stages.get(order=1).requirements.get(code="F1-R1")
        art = evidence.create_evidence(
            actor=u["demo.tecnico"], project=p1, requirement=req, kind="business_case",
            title="Caso de negócio v1 (sintético)",
            uploaded=SimpleUploadedFile("caso-de-negocio.txt", "Caso de negócio sintético para demonstração.\n".encode()),
        )
        evidence.inspect_version(art.pk, actor=u["demo.seguranca"], release=True, note="Inspeção manual (demo)")
        risks.propose_decision(actor=u["demo.gerente"], project=p1, topic="architecture",
                               agenda="Hospedagem da plataforma de IA", alternatives="Nuvem pública; on-premises; híbrida",
                               decision="On-premises com GPUs próprias", rationale="Soberania de dados e custo recorrente")
        raw = analytics.create_asset(actor=u["demo.gerente"], project=p1, name="Base de chamados (sintética)",
                                     kind="dataset", purpose="Ajuste fino do assistente", owner=u["demo.tecnico"],
                                     source_system="Sistema de atendimento (fictício)", contains_personal_data=True,
                                     classification="confidential")
        model = analytics.create_asset(actor=u["demo.gerente"], project=p1, name="Assistente de triagem v0",
                                       kind="model", purpose="Classificar chamados", owner=u["demo.tecnico"])
        analytics.add_lineage(actor=u["demo.gerente"], source=raw, target=model,
                              transformation="Anonimização e ajuste fino")
        org = p1.organization
        analytics.capture_snapshots(actor=u["demo.portfolio"], organization=org)
        analytics.generate_insights(actor=u["demo.portfolio"], organization=org)
