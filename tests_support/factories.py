"""Fábricas de dados SINTÉTICOS para testes (nenhum dado pessoal real)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from decimal import Decimal

from django.contrib.auth import get_user_model

from apps.organizations.models import Membership, Organization, Role
from apps.organizations.services import bootstrap_role

_seq = itertools.count(1)
TEST_PASSWORD = "senha-de-teste-sintetica-123"  # noqa: S105 - apenas testes


def make_user(username: str, **extra):
    User = get_user_model()
    user = User.objects.create_user(
        username=username, password=TEST_PASSWORD, full_name=extra.pop("full_name", username.title()), **extra
    )
    return user


@dataclass
class OrgSetup:
    org: Organization
    users: dict[str, object] = field(default_factory=dict)

    def __getattr__(self, item):
        users = self.__dict__.get("users", {})
        if item in users:
            return users[item]
        raise AttributeError(item)

    def add_user(self, key: str, role: str | None = None, project=None):
        user = make_user(f"{self.org.slug}-{key}-{next(_seq)}")
        Membership.objects.get_or_create(organization=self.org, user=user)
        if role:
            bootstrap_role(organization=self.org, user=user, role=role, project=project, reason="teste")
        self.users[key] = user
        return user

    def create_project(self, code: str = "IA-01", **overrides):
        from apps.projects.services import create_project

        data = dict(
            code=code, name=f"Projeto sintético {code}", description="Implantação de plataforma de IA (fictício).",
            business_case="Caso de negócio sintético para testes.", platform_type="genai",
            deployment_approach="on_prem", sponsor=self.sponsor, manager=self.manager,
            planned_cost=Decimal("100000.00"),
        )
        data.update(overrides)
        return create_project(actor=self.manager, organization=self.org, **data)


def make_org_setup(name: str, prefix: str) -> OrgSetup:
    from django.utils.text import slugify

    org = Organization.objects.create(name=name, slug=slugify(name))
    setup = OrgSetup(org=org)
    setup.add_user("admin", Role.ORG_ADMIN)
    setup.add_user("manager", Role.PROJECT_MANAGER)
    setup.add_user("sponsor", Role.SPONSOR)
    setup.add_user("approver", Role.GATE_APPROVER)
    setup.add_user("executor", Role.TECH_EXECUTOR)
    setup.add_user("security", Role.SECURITY_COMPLIANCE)
    setup.add_user("auditor", Role.AUDITOR)
    setup.add_user("reader", Role.READER)
    setup.add_user("portfolio", Role.PORTFOLIO_MANAGER)
    setup.add_user("outsider")  # membro sem papel
    return setup


def txt_upload(name="evidencia.txt", content=b"Evidencia sintetica de teste.\n"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content, content_type="text/plain")


def approved_evidence(setup: OrgSetup, requirement, *, kind=None):
    """Evidência aprovada: executor envia, segurança inspeciona/libera, aprovador revisa (segregação)."""
    from apps.evidence import services as ev

    art = ev.create_evidence(
        actor=setup.executor, project=requirement.stage.project, requirement=requirement,
        kind=kind or requirement.evidence_kind or "other", title=f"Evidência {requirement.code}", uploaded=txt_upload(),
    )
    ev.inspect_version(art.pk, actor=setup.security, release=True, note="Inspecionado")
    return ev.review_evidence(art.pk, actor=setup.approver, decision="approved", comment="Conforme critério.")


def complete_stage_requirements(setup: OrgSetup, stage, *, skip=()):
    """Atende e valida todos os requisitos obrigatórios (com evidência aprovada quando exigida)."""
    from apps.lifecycle import services as lc

    for req in stage.requirements.filter(mandatory=True):
        if req.code in skip:
            continue
        if req.requires_evidence:
            approved_evidence(setup, req)
        lc.fulfill_requirement(req.pk, actor=setup.manager, note=f"Atendimento verificável de {req.code}.")
        lc.validate_requirement(req.pk, actor=setup.security, decision="approved", comment="Validado.")


def complete_responsible_ai(setup: OrgSetup, project):
    from apps.governance import services as gov
    from apps.governance.models import ResponsibleAIFactor

    for factor in ResponsibleAIFactor.values:
        gov.assess_responsible_ai(project, actor=setup.security, factor=factor, status="addressed",
                                  measures=f"Medidas sintéticas registradas para o fator {factor}.",
                                  accountable=setup.sponsor)


def pass_gate(setup: OrgSetup, stage):
    from apps.governance import services as gov

    if stage.requires_responsible_ai:
        complete_responsible_ai(setup, stage.project)
    complete_stage_requirements(setup, stage)
    gate = gov.request_gate(stage.pk, actor=setup.manager)
    return gov.approve_gate(stage.pk, actor=setup.approver, justification="Critérios atendidos.",
                            request_number=gate.request_number)
