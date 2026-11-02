"""Portfólios, projetos, objetivos de negócio e histórico de status (F01)."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel


class Portfolio(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT, related_name="portfolios", verbose_name="organização"
    )
    name = models.CharField("nome", max_length=150)
    description = models.TextField("descrição", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name="gestor do portfólio",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "portfólio"
        verbose_name_plural = "portfólios"
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="uniq_portfolio_org_name")]

    def __str__(self):
        return self.name


class PlatformType(models.TextChoices):
    GENAI = "genai", "Plataforma de IA generativa / LLM"
    MLOPS = "mlops", "Plataforma de MLOps / ciclo de modelos"
    ANALYTICS = "analytics", "Analytics avançado / ciência de dados"
    VISION = "vision", "Visão computacional"
    DATA = "data", "Plataforma de dados para IA"
    OTHER = "other", "Outro"


class DeploymentApproach(models.TextChoices):
    ON_PREM = "on_prem", "Infraestrutura local (on-premises)"
    PRIVATE_CLOUD = "private_cloud", "Nuvem privada"
    PUBLIC_CLOUD = "public_cloud", "Nuvem pública"
    HYBRID = "hybrid", "Híbrida"
    EDGE = "edge", "Borda (edge)"


class Level(models.TextChoices):
    LOW = "low", "Baixa"
    MEDIUM = "medium", "Média"
    HIGH = "high", "Alta"
    CRITICAL = "critical", "Crítica"


class DataClassification(models.TextChoices):
    PUBLIC = "public", "Pública"
    INTERNAL = "internal", "Interna"
    CONFIDENTIAL = "confidential", "Confidencial"
    RESTRICTED = "restricted", "Restrita"


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Em andamento"
    ON_HOLD = "on_hold", "Suspenso"
    CLOSED = "closed", "Encerrado"
    CANCELLED = "cancelled", "Cancelado"
    ARCHIVED = "archived", "Arquivado"


TERMINAL_STATUSES = {ProjectStatus.CLOSED, ProjectStatus.CANCELLED, ProjectStatus.ARCHIVED}

code_validator = RegexValidator(r"^[A-Z0-9][A-Z0-9\-]{1,29}$", "Use letras maiúsculas, números e hífen (2–30).")


def validate_technology_metadata(value):
    """Metadados de tecnologia/fornecedor são OPCIONAIS e descritivos: nenhuma regra depende de marca."""
    if value in (None, ""):
        return
    if not isinstance(value, dict):
        raise ValidationError("Metadados devem ser um objeto chave → valor.")
    if len(value) > 20:
        raise ValidationError("Máximo de 20 itens de metadados.")
    for k, v in value.items():
        if not isinstance(k, str) or not isinstance(v, str) or len(k) > 60 or len(v) > 200:
            raise ValidationError("Chaves (até 60) e valores (até 200) devem ser textos.")


class Project(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT, related_name="projects", verbose_name="organização"
    )
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.PROTECT, null=True, blank=True, related_name="projects", verbose_name="portfólio"
    )
    code = models.CharField("código", max_length=30, validators=[code_validator])
    name = models.CharField("nome", max_length=200)
    description = models.TextField("descrição")
    business_case = models.TextField("justificativa / caso de negócio")
    business_objectives = models.TextField("objetivos de negócio", blank=True)
    target_indicators = models.TextField("indicadores-alvo", blank=True)
    platform_type = models.CharField("tipo de plataforma", max_length=20, choices=PlatformType.choices)
    deployment_approach = models.CharField(
        "abordagem de implantação", max_length=20, choices=DeploymentApproach.choices
    )
    technology_metadata = models.JSONField(
        "tecnologias/fornecedores (opcional)", default=dict, blank=True, validators=[validate_technology_metadata]
    )
    sponsor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sponsored_projects", verbose_name="patrocinador"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="managed_projects",
        verbose_name="gerente do projeto",
    )
    technical_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tech_led_projects", null=True, blank=True,
        verbose_name="responsável técnico",
    )
    priority = models.CharField("prioridade", max_length=10, choices=Level.choices, default=Level.MEDIUM)
    criticality = models.CharField("criticidade", max_length=10, choices=Level.choices, default=Level.MEDIUM)
    data_classification = models.CharField(
        "classificação de dados", max_length=15, choices=DataClassification.choices, default=DataClassification.INTERNAL
    )
    start_date = models.DateField("início previsto", null=True, blank=True)
    due_date = models.DateField("prazo final", null=True, blank=True)
    planned_cost = models.DecimalField(
        "custo planejado", max_digits=14, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    currency = models.CharField("moeda", max_length=3, default="BRL")
    status = models.CharField("status", max_length=12, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE)
    lifecycle_version = models.ForeignKey(
        "lifecycle.LifecycleTemplateVersion", on_delete=models.PROTECT, null=True, blank=True,
        related_name="projects", verbose_name="versão do ciclo de vida",
    )
    version = models.PositiveIntegerField("versão do registro", default=1)

    class Meta:
        ordering = ["code"]
        verbose_name = "projeto"
        verbose_name_plural = "projetos"
        constraints = [
            models.UniqueConstraint(fields=["organization", "code"], name="uniq_project_org_code"),
            models.CheckConstraint(condition=Q(planned_cost__gte=0), name="project_planned_cost_nonneg"),
            models.CheckConstraint(
                condition=Q(due_date__isnull=True) | Q(start_date__isnull=True) | Q(due_date__gte=models.F("start_date")),
                name="project_due_after_start",
            ),
        ]
        indexes = [models.Index(fields=["organization", "status"])]

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def current_stage(self):
        from apps.lifecycle.models import StageStatus

        stages = list(self.stages.all())
        open_stages = [s for s in stages if s.status not in (StageStatus.APPROVED, StageStatus.COMPLETED)]
        if open_stages:
            return min(open_stages, key=lambda s: s.order)
        return max(stages, key=lambda s: s.order) if stages else None


class BusinessGoal(BaseModel):
    """Objetivo de negócio com métrica de benefício (EDM02) — unifica BusinessGoal e BenefitMetric do desenho."""

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="goals")
    description = models.CharField("objetivo", max_length=255)
    metric_name = models.CharField("métrica de benefício", max_length=150, blank=True)
    baseline_value = models.DecimalField("linha de base", max_digits=14, decimal_places=2, null=True, blank=True)
    target_value = models.DecimalField("meta", max_digits=14, decimal_places=2, null=True, blank=True)
    unit = models.CharField("unidade", max_length=30, blank=True)

    class Meta:
        verbose_name = "objetivo de negócio"
        verbose_name_plural = "objetivos de negócio"

    def __str__(self):
        return self.description


class ProjectStatusHistory(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="status_history")
    created_at = models.DateTimeField(auto_now_add=True)
    from_status = models.CharField(max_length=12, choices=ProjectStatus.choices, blank=True)
    to_status = models.CharField(max_length=12, choices=ProjectStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", null=True)
    reason = models.TextField("motivo/decisão formal", blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "histórico de status do projeto"
        verbose_name_plural = "históricos de status do projeto"
