"""Riscos (5×5), tratamentos, custos (Decimal), decisões versionadas e ações (F04).

Categorias de risco de IA conforme ISACA (2025), *Leveraging COBIT for Effective AI System Governance*, fig. 5
(p. 16). Limiares de classificação são configuráveis por organização (RiskPolicy) e NÃO afirmam alinhamento
automático a ISO/COBIT.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel


class RiskCategory(models.TextChoices):
    DATA = "data", "Dados"
    PRIVACY = "privacy", "Privacidade"
    SECURITY = "security", "Segurança"
    GPU = "gpu", "GPU/capacidade"
    VENDOR = "vendor", "Fornecedor"
    INTEGRATION = "integration", "Integração"
    COST = "cost", "Custo"
    SCHEDULE = "schedule", "Prazo"
    QUALITY = "quality", "Qualidade"
    OPERATION = "operation", "Operação"
    ETHICS = "ethics", "Ética"


class AIRiskCategory(models.TextChoices):
    """ISACA (2025), fig. 5 — AI Risk Categories."""

    ETHICAL = "ethical", "Uso ético (viés, consequências não intencionais)"
    POLICY = "policy", "Política e governança (responsabilização, conformidade)"
    TECHNOLOGY = "technology", "Tecnologia e infraestrutura (falhas algorítmicas, ataques adversariais)"
    OPERATIONAL = "operational", "Operacional e organizacional (dependência excessiva, desalinhamento)"
    EMERGING = "emerging", "Emergente e estratégico (mau uso de IA generativa, precedentes legais)"


class RiskLevel(models.TextChoices):
    LOW = "low", "Baixo"
    MEDIUM = "medium", "Médio"
    HIGH = "high", "Alto"
    CRITICAL = "critical", "Crítico"


class RiskPolicy(models.Model):
    """Limiares (pontuação = probabilidade × impacto, 1–25). Padrão documentado em docs/governanca/politica-riscos.md."""

    organization = models.OneToOneField("organizations.Organization", on_delete=models.CASCADE, related_name="risk_policy")
    critical_min = models.PositiveSmallIntegerField(default=20)
    high_min = models.PositiveSmallIntegerField(default=12)
    medium_min = models.PositiveSmallIntegerField(default=6)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(medium_min__gte=1) & Q(medium_min__lt=models.F("high_min"))
                & Q(high_min__lt=models.F("critical_min")) & Q(critical_min__lte=25),
                name="risk_policy_ordered_thresholds",
            )
        ]

    def classify(self, score: int) -> str:
        return classify(score, self.critical_min, self.high_min, self.medium_min)


DEFAULT_THRESHOLDS = (20, 12, 6)


def classify(score: int, critical_min=20, high_min=12, medium_min=6) -> str:
    if score >= critical_min:
        return RiskLevel.CRITICAL
    if score >= high_min:
        return RiskLevel.HIGH
    if score >= medium_min:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


class RiskStatus(models.TextChoices):
    IDENTIFIED = "identified", "Identificado"
    TREATING = "treating", "Em tratamento"
    MONITORED = "monitored", "Monitorado"
    ACCEPTED = "accepted", "Aceito (risco residual)"
    CLOSED = "closed", "Encerrado"


scale = [MinValueValidator(1), MaxValueValidator(5)]


class Risk(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="risks")
    stage = models.ForeignKey("lifecycle.StageInstance", on_delete=models.PROTECT, null=True, blank=True,
                              related_name="risks", verbose_name="fase")
    code = models.CharField("código", max_length=20)
    title = models.CharField("risco", max_length=200)
    category = models.CharField("categoria", max_length=20, choices=RiskCategory.choices)
    ai_category = models.CharField("categoria de risco de IA (ISACA 2025)", max_length=20,
                                   choices=AIRiskCategory.choices, blank=True)
    description = models.TextField("descrição", blank=True)
    cause = models.TextField("causa", blank=True)
    consequence = models.TextField("consequência", blank=True)
    probability = models.PositiveSmallIntegerField("probabilidade (1–5)", validators=scale)
    impact = models.PositiveSmallIntegerField("impacto (1–5)", validators=scale)
    score = models.PositiveSmallIntegerField("pontuação", editable=False, default=1)
    level = models.CharField("nível", max_length=10, choices=RiskLevel.choices, editable=False, default=RiskLevel.LOW)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
                              verbose_name="proprietário")
    status = models.CharField(max_length=12, choices=RiskStatus.choices, default=RiskStatus.IDENTIFIED)
    residual_probability = models.PositiveSmallIntegerField("probabilidade residual", validators=scale, null=True,
                                                            blank=True)
    residual_impact = models.PositiveSmallIntegerField("impacto residual", validators=scale, null=True, blank=True)
    residual_accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True,
                                             blank=True, related_name="+")
    residual_accepted_at = models.DateTimeField(null=True, blank=True)
    review_date = models.DateField("próxima revisão", null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-score", "code"]
        verbose_name = "risco"
        verbose_name_plural = "riscos"
        constraints = [
            models.UniqueConstraint(fields=["project", "code"], name="uniq_risk_code_project"),
            models.CheckConstraint(condition=Q(probability__gte=1, probability__lte=5), name="risk_probability_1_5"),
            models.CheckConstraint(condition=Q(impact__gte=1, impact__lte=5), name="risk_impact_1_5"),
        ]
        indexes = [models.Index(fields=["project", "level", "status"])]

    def __str__(self):
        return f"{self.code} {self.title} ({self.get_level_display()})"

    @property
    def residual_score(self):
        if self.residual_probability and self.residual_impact:
            return self.residual_probability * self.residual_impact
        return None


class TreatmentStrategy(models.TextChoices):
    MITIGATE = "mitigate", "Mitigar"
    TRANSFER = "transfer", "Transferir"
    AVOID = "avoid", "Evitar"
    ACCEPT = "accept", "Aceitar"


class TreatmentStatus(models.TextChoices):
    PLANNED = "planned", "Planejado"
    IN_PROGRESS = "in_progress", "Em execução"
    DONE = "done", "Concluído"
    CANCELLED = "cancelled", "Cancelado"


class RiskTreatment(BaseModel):
    risk = models.ForeignKey(Risk, on_delete=models.PROTECT, related_name="treatments")
    strategy = models.CharField("estratégia", max_length=10, choices=TreatmentStrategy.choices)
    description = models.TextField("medida de tratamento")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
                              verbose_name="responsável")
    due_date = models.DateField("prazo")
    status = models.CharField(max_length=12, choices=TreatmentStatus.choices, default=TreatmentStatus.PLANNED)

    class Meta:
        ordering = ["due_date"]
        verbose_name = "tratamento de risco"


class CostCategory(models.TextChoices):
    INFRA = "infra", "Infraestrutura"
    GPU = "gpu", "GPU"
    STORAGE = "storage", "Armazenamento"
    LICENSES = "licenses", "Licenças"
    SERVICES = "services", "Serviços"
    PEOPLE = "people", "Pessoas/outros"


class CostKind(models.TextChoices):
    PLANNED = "planned", "Previsto"
    ACTUAL = "actual", "Realizado"


class CostEntry(BaseModel):
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="cost_entries")
    stage = models.ForeignKey("lifecycle.StageInstance", on_delete=models.PROTECT, null=True, blank=True,
                              related_name="+")
    category = models.CharField("categoria", max_length=10, choices=CostCategory.choices)
    kind = models.CharField("tipo", max_length=8, choices=CostKind.choices)
    amount = models.DecimalField("valor", max_digits=14, decimal_places=2)
    currency = models.CharField("moeda", max_length=3)
    entry_date = models.DateField("data de competência")
    justification = models.CharField("justificativa", max_length=255)
    source_document = models.CharField("fonte documental", max_length=255, blank=True)

    class Meta:
        ordering = ["-entry_date"]
        verbose_name = "lançamento de custo"
        verbose_name_plural = "lançamentos de custo"
        constraints = [models.CheckConstraint(condition=Q(amount__gt=Decimal("0")), name="cost_amount_positive")]


class DecisionStatus(models.TextChoices):
    PROPOSED = "proposed", "Proposta"
    APPROVED = "approved", "Aprovada"
    REJECTED = "rejected", "Rejeitada"
    SUPERSEDED = "superseded", "Substituída por nova versão"


class DecisionTopic(models.TextChoices):
    GENERAL = "general", "Geral"
    SCOPE = "scope", "Escopo/mudança"
    ARCHITECTURE = "architecture", "Arquitetura/tecnologia"
    RISK = "risk", "Risco"
    REOPEN = "reopen", "Reabertura de projeto"


class DecisionRecord(BaseModel):
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="decisions")
    code = models.CharField("código", max_length=20)
    version = models.PositiveIntegerField("versão", default=1)
    topic = models.CharField("tema", max_length=15, choices=DecisionTopic.choices, default=DecisionTopic.GENERAL)
    agenda = models.CharField("pauta", max_length=255)
    alternatives = models.TextField("alternativas consideradas")
    decision = models.TextField("decisão")
    rationale = models.TextField("motivação")
    risks_considered = models.TextField("riscos considerados", blank=True)
    status = models.CharField(max_length=12, choices=DecisionStatus.choices, default=DecisionStatus.PROPOSED)
    proposed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name="+")
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField("parecer", blank=True)
    supersedes = models.OneToOneField("self", on_delete=models.PROTECT, null=True, blank=True,
                                      related_name="superseded_by")
    evidences = models.ManyToManyField("evidence.EvidenceArtifact", blank=True, related_name="decisions")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "registro de decisão"
        verbose_name_plural = "registros de decisão"
        constraints = [models.UniqueConstraint(fields=["project", "code", "version"], name="uniq_decision_version")]

    def __str__(self):
        return f"{self.code} v{self.version} — {self.agenda}"


class ActionStatus(models.TextChoices):
    OPEN = "open", "Aberta"
    DONE = "done", "Concluída"
    CANCELLED = "cancelled", "Cancelada"


class ActionItem(BaseModel):
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="action_items")
    title = models.CharField("ação", max_length=200)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=ActionStatus.choices, default=ActionStatus.OPEN)
    decision = models.ForeignKey(DecisionRecord, on_delete=models.PROTECT, null=True, blank=True,
                                 related_name="actions")
    origin = models.CharField("origem", max_length=120, blank=True, help_text="Ex.: insight, decisão, auditoria")

    class Meta:
        ordering = ["status", "due_date"]
        verbose_name = "ação"
        verbose_name_plural = "ações"
