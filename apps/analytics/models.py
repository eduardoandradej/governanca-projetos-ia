"""Camadas D→I→K (F07).

D (dados): catálogo de ativos de dados/artefatos de IA e linhagem — metadados, sem ingerir datasets ou PII.
I (informação): definições de indicadores (ficha técnica) e snapshots recalculáveis.
K (conhecimento): insights por regras determinísticas e explicáveis, revisão humana e lições aprendidas.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel
from apps.projects.models import DataClassification

# ------------------------------------------------------------------------------------------- Dados (D)


class AssetKind(models.TextChoices):
    DATASET = "dataset", "Conjunto de dados"
    FEATURES = "features", "Conjunto de features"
    MODEL = "model", "Modelo de IA"
    PIPELINE = "pipeline", "Pipeline/transformação"
    REPORT = "report", "Relatório/saída"
    OTHER = "other", "Outro artefato"


class DeclaredQuality(models.TextChoices):
    UNKNOWN = "unknown", "Não avaliada"
    LOW = "low", "Baixa"
    MEDIUM = "medium", "Média"
    HIGH = "high", "Alta"


class DataAsset(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="data_assets")
    name = models.CharField("nome", max_length=150)
    kind = models.CharField("tipo", max_length=12, choices=AssetKind.choices)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
                              verbose_name="proprietário")
    purpose = models.CharField("finalidade", max_length=255)
    description = models.TextField("descrição", blank=True)
    source_system = models.CharField("origem/sistema fonte", max_length=150, blank=True)
    classification = models.CharField("classificação", max_length=15, choices=DataClassification.choices,
                                      default=DataClassification.INTERNAL)
    current_version = models.CharField("versão atual", max_length=30, default="1")
    locator = models.CharField("localizador/referência", max_length=500, blank=True,
                               help_text="URI ou referência externa; o MVP não armazena o conteúdo.")
    source_updated_at = models.DateField("atualização na origem", null=True, blank=True)
    declared_quality = models.CharField("qualidade declarada", max_length=10, choices=DeclaredQuality.choices,
                                        default=DeclaredQuality.UNKNOWN)
    retention = models.CharField("retenção", max_length=120, blank=True)
    usage_restriction = models.CharField("restrição de uso", max_length=255, blank=True)
    contains_personal_data = models.BooleanField("contém dados pessoais (declarado)", default=False)

    class Meta:
        ordering = ["project", "name"]
        verbose_name = "ativo de dados"
        verbose_name_plural = "ativos de dados"
        constraints = [models.UniqueConstraint(fields=["project", "name"], name="uniq_asset_project_name")]

    def __str__(self):
        return f"{self.name} ({self.get_kind_display()})"


class DataAssetVersion(models.Model):
    asset = models.ForeignKey(DataAsset, on_delete=models.PROTECT, related_name="versions")
    version = models.CharField(max_length=30)
    locator = models.CharField(max_length=500, blank=True)
    change_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["asset", "version"], name="uniq_asset_version")]


class DataLineage(BaseModel):
    """Aresta de linhagem: origem → (transformação) → saída."""

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    source = models.ForeignKey(DataAsset, on_delete=models.PROTECT, related_name="downstream")
    target = models.ForeignKey(DataAsset, on_delete=models.PROTECT, related_name="upstream")
    transformation = models.CharField("transformação", max_length=255)

    class Meta:
        verbose_name = "linhagem"
        constraints = [
            models.UniqueConstraint(fields=["source", "target"], name="uniq_lineage_edge"),
            models.CheckConstraint(condition=~Q(source=models.F("target")), name="lineage_not_self"),
        ]


# -------------------------------------------------------------------------------------- Informação (I)


class MetricDefinition(models.Model):
    """Ficha técnica do indicador. O cálculo vive em apps/analytics/metrics.py (mesmo `code`)."""

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField("nome", max_length=150)
    definition = models.TextField("definição")
    numerator = models.CharField("numerador", max_length=255, blank=True)
    denominator = models.CharField("denominador", max_length=255, blank=True)
    calculation = models.CharField("regra de cálculo", max_length=255)
    filters = models.CharField("filtros aplicáveis", max_length=255)
    source = models.CharField("fonte (tabelas)", max_length=255)
    periodicity = models.CharField("periodicidade", max_length=60)
    unit = models.CharField("unidade", max_length=20)
    limitations = models.TextField("limitações")
    cobit_ref = models.CharField(max_length=20, blank=True)
    indicator_type = models.CharField(
        "tipo de indicador", max_length=10,
        choices=[("leading", "De tendência (leading)"), ("lagging", "De resultado (lagging)")],
        default="lagging", help_text="PMBOK 8, Governance Performance Domain, 2.1.5.1–2.1.5.2 (p. 13).",
    )
    pmbok_ref = models.CharField("referência PMBOK 8", max_length=80, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "definição de indicador"

    def __str__(self):
        return f"{self.code} {self.name}"


class MetricSnapshot(models.Model):
    """Snapshot para série histórica e reprodutibilidade das entradas de insights."""

    metric = models.ForeignKey(MetricDefinition, on_delete=models.PROTECT, related_name="snapshots")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    computed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    value = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    numerator = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    denominator = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    is_demo = models.BooleanField(default=False)
    computed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+")

    class Meta:
        ordering = ["-computed_at"]
        indexes = [models.Index(fields=["metric", "organization", "computed_at"])]


# ------------------------------------------------------------------------------------- Conhecimento (K)


class InsightStatus(models.TextChoices):
    PROPOSED = "proposed", "Proposto (sugestão automática)"
    REVIEWED = "reviewed", "Revisado"
    APPROVED = "approved", "Aprovado como recomendação"
    DISCARDED = "discarded", "Descartado"


class Insight(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, null=True, blank=True,
                                related_name="insights")
    rule_code = models.CharField("regra disparadora", max_length=10)
    title = models.CharField("título", max_length=200)
    message = models.TextField("mensagem explicável")
    parameters = models.JSONField("parâmetros da regra", default=dict)
    supporting_data = models.JSONField("dados de sustentação", default=dict)
    fingerprint = models.CharField(max_length=200, db_index=True)
    computed_at = models.DateTimeField("calculado em", auto_now_add=True)
    status = models.CharField(max_length=10, choices=InsightStatus.choices, default=InsightStatus.PROPOSED)
    is_demo = models.BooleanField("derivado de dados demonstrativos", default=False)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="+")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="+")
    justification = models.TextField("justificativa da revisão", blank=True)
    action = models.ForeignKey("risks.ActionItem", on_delete=models.PROTECT, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["-computed_at"]
        verbose_name = "insight"
        constraints = [
            # Um único insight aberto por regra/alvo: recálculos não duplicam sugestões.
            models.UniqueConstraint(fields=["fingerprint"], condition=Q(status__in=["proposed", "reviewed"]),
                                    name="uniq_open_insight_fingerprint"),
        ]

    def __str__(self):
        return self.title


class InsightReview(models.Model):
    insight = models.ForeignKey(Insight, on_delete=models.PROTECT, related_name="reviews")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    from_status = models.CharField(max_length=10, choices=InsightStatus.choices)
    to_status = models.CharField(max_length=10, choices=InsightStatus.choices)
    note = models.TextField()

    class Meta:
        ordering = ["created_at"]


class LessonStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    APPROVED = "approved", "Aprovada"
    ARCHIVED = "archived", "Arquivada"


class LessonVisibility(models.TextChoices):
    PROJECT = "project", "Somente equipe do projeto"
    ORGANIZATION = "organization", "Toda a organização"


class LessonLearned(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="lessons")
    title = models.CharField("título", max_length=200)
    context = models.TextField("contexto")
    lesson = models.TextField("lição")
    recommendation = models.TextField("recomendação")
    # Taxonomia
    platform_type = models.CharField("tipo de projeto", max_length=20, blank=True)
    stage_order = models.PositiveSmallIntegerField("etapa", null=True, blank=True)
    risk_category = models.CharField("risco relacionado", max_length=20, blank=True)
    technology = models.CharField("tecnologia (metadado)", max_length=80, blank=True)
    knowledge_type = models.CharField(
        "tipo de conhecimento", max_length=10, choices=[("explicit", "Explícito"), ("tacit", "Tácito (tornado explícito)")],
        default="explicit", help_text="PMBOK 8, 2.1.6.6 Manage Project Knowledge (p. 23–25).",
    )
    classification = models.CharField(max_length=15, choices=DataClassification.choices,
                                      default=DataClassification.INTERNAL)
    visibility = models.CharField(max_length=15, choices=LessonVisibility.choices, default=LessonVisibility.PROJECT)
    disclosure_justification = models.TextField("justificativa de divulgação", blank=True)
    status = models.CharField(max_length=10, choices=LessonStatus.choices, default=LessonStatus.DRAFT)
    source_insight = models.ForeignKey(Insight, on_delete=models.PROTECT, null=True, blank=True, related_name="lessons")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="+")
    approved_at = models.DateTimeField(null=True, blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "lição aprendida"
        verbose_name_plural = "lições aprendidas"
        indexes = [models.Index(fields=["organization", "status", "visibility"])]

    def __str__(self):
        return self.title
