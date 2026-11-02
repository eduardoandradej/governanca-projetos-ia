"""Catálogo de evidências versionadas, com revisão e quarentena de anexos (F05).

Arquivos ficam em PRIVATE_MEDIA_ROOT (fora de diretórios servidos), com nome interno aleatório; o caminho
nunca é exposto. Download apenas por view autenticada com verificação de escopo e liberação da quarentena.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel
from apps.lifecycle.models import EvidenceKind
from apps.projects.models import DataClassification


class EvidenceStatus(models.TextChoices):
    IN_REVIEW = "in_review", "Em revisão"
    APPROVED = "approved", "Aprovada"
    REJECTED = "rejected", "Rejeitada"
    ARCHIVED = "archived", "Arquivada"


class ScanStatus(models.TextChoices):
    NOT_APPLICABLE = "n/a", "Sem arquivo (referência externa)"
    QUARANTINED = "quarantined", "Em quarentena (aguarda inspeção)"
    RELEASED = "released", "Liberado após inspeção"
    BLOCKED = "blocked", "Bloqueado"


class EvidenceArtifact(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="evidences")
    stage = models.ForeignKey(
        "lifecycle.StageInstance", on_delete=models.PROTECT, null=True, blank=True, related_name="evidences",
        verbose_name="fase",
    )
    requirement = models.ForeignKey(
        "lifecycle.RequirementInstance", on_delete=models.PROTECT, null=True, blank=True, related_name="evidences",
        verbose_name="requisito",
    )
    task = models.ForeignKey(
        "lifecycle.Task", on_delete=models.PROTECT, null=True, blank=True, related_name="evidences", verbose_name="tarefa"
    )
    kind = models.CharField("tipo", max_length=20, choices=EvidenceKind.choices)
    title = models.CharField("título", max_length=200)
    description = models.TextField("descrição", blank=True)
    origin = models.CharField("origem", max_length=200, blank=True, help_text="Sistema, reunião ou documento de origem.")
    classification = models.CharField(
        "classificação", max_length=15, choices=DataClassification.choices, default=DataClassification.INTERNAL
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", verbose_name="responsável"
    )
    status = models.CharField(max_length=12, choices=EvidenceStatus.choices, default=EvidenceStatus.IN_REVIEW)
    current_version = models.PositiveIntegerField("versão atual", default=0)
    retention_until = models.DateField("reter até", null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "evidência"
        verbose_name_plural = "evidências"
        indexes = [models.Index(fields=["project", "status"]), models.Index(fields=["requirement", "status"])]

    def __str__(self):
        return f"{self.title} (v{self.current_version})"

    @property
    def latest(self):
        return self.versions.order_by("-number").first()


class EvidenceVersion(models.Model):
    artifact = models.ForeignKey(EvidenceArtifact, on_delete=models.PROTECT, related_name="versions")
    number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    change_note = models.CharField("nota da versão", max_length=255, blank=True)
    storage_name = models.CharField(max_length=120, blank=True)  # nome interno; nunca exibido
    original_name = models.CharField("nome original", max_length=200, blank=True)
    content_type = models.CharField(max_length=60, blank=True)
    size = models.PositiveIntegerField(default=0)
    sha256 = models.CharField("SHA-256", max_length=64, blank=True)
    external_reference = models.CharField(
        "referência externa", max_length=500, blank=True, help_text="Localizador quando a evidência não é arquivo."
    )
    scan_status = models.CharField(max_length=12, choices=ScanStatus.choices, default=ScanStatus.NOT_APPLICABLE)
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    inspected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["artifact", "-number"]
        constraints = [
            models.UniqueConstraint(fields=["artifact", "number"], name="uniq_evidence_version"),
            models.CheckConstraint(
                condition=~Q(storage_name="") | ~Q(external_reference=""), name="evidence_version_has_content"
            ),
        ]

    def __str__(self):
        return f"{self.artifact.title} v{self.number}"


class ReviewDecision(models.TextChoices):
    APPROVED = "approved", "Aprovada"
    REJECTED = "rejected", "Rejeitada"


class EvidenceReview(models.Model):
    artifact = models.ForeignKey(EvidenceArtifact, on_delete=models.PROTECT, related_name="reviews")
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    decision = models.CharField(max_length=10, choices=ReviewDecision.choices)
    comment = models.TextField("parecer")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["artifact", "version_number", "reviewer"], name="uniq_review_per_version")
        ]
