"""Organizações, vínculos (membership) e atribuições de papéis com escopo (F01/F08)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField("nome", max_length=150, unique=True)
    slug = models.SlugField("identificador curto", max_length=60, unique=True)
    description = models.TextField("descrição", blank=True)
    is_active = models.BooleanField("ativa", default=True)
    is_demo = models.BooleanField(
        "dados demonstrativos",
        default=False,
        help_text="Marcada pelo comando seed_demo; todo dado derivado deve ser exibido como demonstrativo (RN-022).",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "organização"
        verbose_name_plural = "organizações"

    def __str__(self):
        return self.name


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Ativo"
    SUSPENDED = "suspended", "Suspenso"


class Membership(BaseModel):
    """Vínculo de um usuário a uma organização. Pré-requisito para qualquer papel nela."""

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="memberships")
    status = models.CharField(max_length=16, choices=MembershipStatus.choices, default=MembershipStatus.ACTIVE)
    job_title = models.CharField("cargo/função", max_length=120, blank=True)

    class Meta:
        verbose_name = "vínculo"
        verbose_name_plural = "vínculos"
        constraints = [
            models.UniqueConstraint(fields=["organization", "user"], name="uniq_membership_org_user"),
        ]

    def __str__(self):
        return f"{self.user} @ {self.organization}"


class Role(models.TextChoices):
    """Papéis de autorização (não confundir com papéis RACI de entregáveis)."""

    ORG_ADMIN = "org_admin", "Administrador organizacional"
    PORTFOLIO_MANAGER = "portfolio_manager", "Gestor de portfólio"
    SPONSOR = "sponsor", "Patrocinador"
    PROJECT_MANAGER = "project_manager", "Gerente de projeto"
    TECH_EXECUTOR = "tech_executor", "Executor técnico"
    SECURITY_COMPLIANCE = "security_compliance", "Responsável por segurança/conformidade"
    GATE_APPROVER = "gate_approver", "Aprovador de gate"
    AUDITOR = "auditor", "Auditor"
    READER = "reader", "Leitor"


class RoleAssignment(BaseModel):
    """Concessão de papel. `project` nulo = escopo de toda a organização; preenchido = só o projeto.

    Revogação é lógica (`revoked_at`) para preservar o histórico de concessões (RN-015).
    """

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="role_assignments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="role_assignments")
    role = models.CharField("papel", max_length=32, choices=Role.choices)
    # Referência ao projeto por string evita dependência circular de import; FK real.
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="role_assignments",
        verbose_name="projeto (escopo)",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    reason = models.CharField("motivo da concessão", max_length=255, blank=True)
    revoked_at = models.DateTimeField("revogado em", null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )

    class Meta:
        verbose_name = "atribuição de papel"
        verbose_name_plural = "atribuições de papéis"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user", "role"],
                condition=Q(project__isnull=True, revoked_at__isnull=True),
                name="uniq_active_org_role",
            ),
            models.UniqueConstraint(
                fields=["organization", "user", "role", "project"],
                condition=Q(project__isnull=False, revoked_at__isnull=True),
                name="uniq_active_project_role",
            ),
        ]
        indexes = [models.Index(fields=["user", "organization"])]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def __str__(self):
        scope = self.project.code if self.project_id else "organização"
        return f"{self.user} — {self.get_role_display()} ({scope})"
