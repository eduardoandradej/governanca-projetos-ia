"""Gates (Stage-Gates), decisões, exceções formais e catálogo de objetivos COBIT 2019 (F02/§4)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel


class GateStatus(models.TextChoices):
    OPEN = "open", "Aberto"
    REQUESTED = "requested", "Solicitado"
    APPROVED = "approved", "Aprovado"
    REJECTED = "rejected", "Rejeitado"
    CANCELLED = "cancelled", "Cancelado/revogado"


class Gate(BaseModel):
    """Gate de saída de uma fase. `request_number` cresce a cada solicitação (idempotência, RN-020)."""

    stage = models.OneToOneField("lifecycle.StageInstance", on_delete=models.PROTECT, related_name="gate")
    status = models.CharField(max_length=12, choices=GateStatus.choices, default=GateStatus.OPEN)
    request_number = models.PositiveIntegerField("número da solicitação", default=0)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    requested_at = models.DateTimeField(null=True, blank=True)
    request_note = models.TextField("observação da solicitação", blank=True)
    requirements_snapshot = models.JSONField(
        "conjunto de requisitos na solicitação", default=list, blank=True,
        help_text="Código, versão e status de cada requisito no momento da solicitação (RN-007).",
    )
    revalidation_required = models.BooleanField("revalidação pendente", default=False)
    revalidation_cause = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "gate"
        verbose_name_plural = "gates"
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"Gate da fase {self.stage}"


class GateDecisionType(models.TextChoices):
    APPROVED = "approved", "Aprovação"
    REJECTED = "rejected", "Rejeição (devolução)"
    CANCELLED = "cancelled", "Cancelamento da solicitação"
    REVALIDATED = "revalidated", "Revalidação"


class GateDecision(models.Model):
    gate = models.ForeignKey(Gate, on_delete=models.PROTECT, related_name="decisions")
    request_number = models.PositiveIntegerField()
    decision = models.CharField(max_length=12, choices=GateDecisionType.choices)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    justification = models.TextField("justificativa")
    requirements_snapshot = models.JSONField(default=list)
    exceptions_applied = models.JSONField("exceções consideradas", default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "parecer de gate"
        verbose_name_plural = "pareceres de gate"
        constraints = [
            # Uma única decisão final (aprovação/rejeição) por solicitação: impede duplicidade (RN-020, T-012).
            models.UniqueConstraint(
                fields=["gate", "request_number"],
                condition=Q(decision__in=["approved", "rejected", "cancelled"]),
                name="uniq_final_decision_per_request",
            ),
        ]


class ExceptionStatus(models.TextChoices):
    PENDING_SECURITY = "pending_security", "Aguardando ciência de segurança"
    ACTIVE = "active", "Ativa"
    REVOKED = "revoked", "Revogada"


class GateException(BaseModel):
    """Exceção formal e temporária a um requisito ou ao bloqueio por risco crítico (RN-009).

    Nunca se aplica a requisito legal; nunca apaga histórico; é exibida explicitamente no gate.
    """

    stage = models.ForeignKey("lifecycle.StageInstance", on_delete=models.PROTECT, related_name="exceptions")
    requirement = models.ForeignKey(
        "lifecycle.RequirementInstance", on_delete=models.PROTECT, null=True, blank=True, related_name="exceptions"
    )
    covers_critical_risks = models.BooleanField("dispensa bloqueio por risco crítico", default=False)
    justification = models.TextField("justificativa")
    residual_risk = models.TextField("risco residual aceito")
    valid_until = models.DateField("válida até")
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    requires_security_ack = models.BooleanField(default=False)
    security_ack_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    security_ack_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ExceptionStatus.choices, default=ExceptionStatus.ACTIVE)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "exceção formal"
        verbose_name_plural = "exceções formais"
        constraints = [
            models.CheckConstraint(
                condition=Q(requirement__isnull=False) | Q(covers_critical_risks=True), name="exception_has_target"
            ),
        ]

    def is_effective(self, on_date=None) -> bool:
        from django.utils import timezone

        today = on_date or timezone.localdate()
        return self.status == ExceptionStatus.ACTIVE and self.valid_until >= today


# ------------------------------------------------------------------ Catálogo de objetivos COBIT 2019


class Domain(models.TextChoices):
    EDM = "EDM", "Avaliar, Dirigir e Monitorar"
    APO = "APO", "Alinhar, Planejar e Organizar"
    BAI = "BAI", "Construir, Adquirir e Implementar"
    DSS = "DSS", "Entregar, Servir e Suportar"
    MEA = "MEA", "Monitorar, Avaliar e Analisar"


class GovernanceObjective(models.Model):
    """Objetivo COBIT 2019 referenciado pelo MVP. Apenas código e nome curto (sem reprodução do texto da ISACA)."""

    code = models.CharField(max_length=10, unique=True)
    domain = models.CharField(max_length=3, choices=Domain.choices)
    name = models.CharField("nome (oficial, em inglês)", max_length=120)
    name_pt = models.CharField("tradução livre", max_length=150)
    ai_lifecycle_phase = models.CharField(
        "fase do ciclo de vida de IA (ISACA 2025)", max_length=60, blank=True,
        help_text="Design (EDM), desenvolvimento (APO), implantação (BAI), operação (DSS), monitoramento (MEA).",
    )
    trustworthy_ai = models.CharField("elementos de IA confiável relacionados", max_length=200, blank=True)
    ai_relevance = models.TextField("relevância para IA (paráfrase da equipe)", blank=True)
    source = models.CharField("fonte", max_length=255)
    source_pages = models.CharField("páginas", max_length=30, blank=True)

    class Meta:
        ordering = ["domain", "code"]
        verbose_name = "objetivo de governança/gestão"
        verbose_name_plural = "objetivos de governança/gestão"

    def __str__(self):
        return f"{self.code} — {self.name}"


class MappingBasis(models.TextChoices):
    ISACA_AI_2025 = "isaca_ai_2025", "Citado no white paper ISACA (2025)"
    TEAM = "team", "Interpretação da equipe"


class ControlMapping(models.Model):
    """Rastreabilidade objetivo COBIT → requisito/fase/funcionalidade do sistema."""

    objective = models.ForeignKey(GovernanceObjective, on_delete=models.PROTECT, related_name="mappings")
    requirement_template = models.ForeignKey(
        "lifecycle.RequirementTemplate", on_delete=models.CASCADE, null=True, blank=True, related_name="mappings"
    )
    feature = models.CharField("funcionalidade do sistema", max_length=150, blank=True)
    basis = models.CharField(max_length=20, choices=MappingBasis.choices, default=MappingBasis.TEAM)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "mapeamento de controle"
        verbose_name_plural = "mapeamentos de controle"
        constraints = [
            models.CheckConstraint(
                condition=Q(requirement_template__isnull=False) | ~Q(feature=""), name="mapping_has_target"
            ),
        ]


# ------------------------------------------------------------------ Referências PMBOK 8 (separadas do COBIT)


class FrameworkReference(models.Model):
    """Referência a seção do PMI PMBOK Guide 8ª ed. (2025). Apenas título da seção e página; sem texto protegido.

    Mantida em tabela própria para não confundir conceitos PMBOK com objetivos COBIT (ex.: "Focus Areas" do
    PMBOK 8 ≠ "focus areas" do COBIT 2019).
    """

    framework = models.CharField(max_length=20, default="PMBOK8")
    code = models.CharField(max_length=20, unique=True)
    kind = models.CharField(max_length=20, choices=[
        ("domain", "Domínio de desempenho"), ("principle", "Princípio"), ("process", "Processo"),
        ("concept", "Conceito"), ("appendix", "Apêndice"), ("lifecycle", "Ciclo de vida/abordagem"),
    ])
    section = models.CharField("seção", max_length=20)
    title = models.CharField("título da seção (original)", max_length=150)
    title_pt = models.CharField("tradução livre", max_length=150)
    part = models.CharField("parte", max_length=30, help_text="The Standard ou PMBOK Guide (numeração própria).")
    pages = models.CharField("páginas", max_length=20)
    analysis = models.TextField("análise da equipe (texto original)", blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "referência PMBOK"

    def __str__(self):
        return f"{self.section} {self.title}"


class FrameworkMapping(models.Model):
    reference = models.ForeignKey(FrameworkReference, on_delete=models.PROTECT, related_name="mappings")
    requirement_template = models.ForeignKey(
        "lifecycle.RequirementTemplate", on_delete=models.CASCADE, null=True, blank=True, related_name="pmbok_mappings"
    )
    feature = models.CharField("funcionalidade do sistema", max_length=150, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(requirement_template__isnull=False) | ~Q(feature=""),
                                   name="pmbok_mapping_has_target"),
        ]


# ------------------------------------------------------------------ Uso responsável de IA (PMBOK 8 X3.3 + ISACA)


class ResponsibleAIFactor(models.TextChoices):
    """Fatores éticos de PMBOK 8, Apêndice X3.3 (p. 238 e 242), com elemento de IA confiável da ISACA (2025)."""

    BIAS = "bias", "Viés"
    PRIVACY = "privacy", "Privacidade"
    ACCOUNTABILITY = "accountability", "Responsabilização (humano responsável por cada decisão)"
    RELIABILITY = "reliability", "Confiabilidade das saídas"
    SAFETY = "safety", "Segurança (safety)"
    TRANSPARENCY = "transparency", "Transparência"
    COPYRIGHT = "copyright", "Direitos autorais"
    SUSTAINABILITY = "sustainability", "Sustentabilidade (energia, água, recursos)"


ISACA_ELEMENT_FOR_FACTOR = {
    "bias": "Ética e integridade", "privacy": "Segurança e privacidade", "accountability": "Transparência e honestidade",
    "reliability": "Qualidade", "safety": "Qualidade; Resiliência", "transparency": "Transparência e honestidade",
    "copyright": "Conformidade (MEA03)", "sustainability": "Ética e integridade (impacto ambiental, EDM01)",
}


class FactorStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    ADDRESSED = "addressed", "Tratado"
    NOT_APPLICABLE = "not_applicable", "Não aplicável (justificado)"


class ResponsibleAIAssessment(BaseModel):
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="responsible_ai")
    factor = models.CharField(max_length=20, choices=ResponsibleAIFactor.choices)
    status = models.CharField(max_length=15, choices=FactorStatus.choices, default=FactorStatus.PENDING)
    measures = models.TextField("medidas adotadas / justificativa", blank=True)
    accountable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="+", verbose_name="humano responsável")
    assessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="+")
    assessed_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["project", "factor"]
        verbose_name = "avaliação de uso responsável de IA"
        constraints = [models.UniqueConstraint(fields=["project", "factor"], name="uniq_rai_factor")]
