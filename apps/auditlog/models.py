"""Trilha de auditoria append-only (F09).

A aplicação nunca altera nem exclui eventos: o modelo bloqueia `save()` de registros
existentes e `delete()`, e a migration 0002 cria um gatilho PostgreSQL que rejeita
UPDATE/DELETE. Limitação documentada: um administrador do banco (superusuário PostgreSQL)
ainda pode desativar o gatilho; inviolabilidade forte exige armazenamento externo imutável.
"""

import uuid

from django.conf import settings
from django.db import models


class AuditResult(models.TextChoices):
    SUCCESS = "success", "Sucesso"
    DENIED = "denied", "Negado"
    FAILURE = "failure", "Falha"


class ActorType(models.TextChoices):
    USER = "user", "Usuário"
    SYSTEM = "system", "Sistema"
    ANONYMOUS = "anonymous", "Anônimo"


class AppendOnlyError(Exception):
    pass


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurred_at = models.DateTimeField("instante (UTC)", auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="ator",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor_type = models.CharField(max_length=16, choices=ActorType.choices, default=ActorType.USER)
    actor_repr = models.CharField("identificação do ator", max_length=150, blank=True)
    # Escopo armazenado como UUID (sem FK) para que a trilha sobreviva a arquivamentos
    # e não seja afetada por cascatas.
    organization_id = models.UUIDField("organização", null=True, blank=True, db_index=True)
    project_id = models.UUIDField("projeto", null=True, blank=True, db_index=True)
    action = models.CharField("ação", max_length=80, db_index=True)
    entity_type = models.CharField("entidade", max_length=80, blank=True)
    entity_id = models.CharField("identificador", max_length=64, blank=True, db_index=True)
    entity_version = models.CharField("versão", max_length=32, blank=True)
    before = models.JSONField("antes (sanitizado)", null=True, blank=True)
    after = models.JSONField("depois (sanitizado)", null=True, blank=True)
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)
    result = models.CharField("resultado", max_length=16, choices=AuditResult.choices)
    reason = models.TextField("justificativa/motivo", blank=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name = "evento de auditoria"
        verbose_name_plural = "eventos de auditoria"
        indexes = [
            models.Index(fields=["organization_id", "occurred_at"]),
            models.Index(fields=["project_id", "occurred_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AppendOnlyError("Eventos de auditoria não podem ser alterados.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyError("Eventos de auditoria não podem ser excluídos.")

    def __str__(self):
        return f"{self.occurred_at:%Y-%m-%d %H:%M:%S} {self.action} [{self.result}]"


class ExportRecord(models.Model):
    """Registro de exportações de dados (RN-014)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    organization_id = models.UUIDField(null=True, blank=True)
    report = models.CharField("relatório", max_length=80)
    filters = models.JSONField("filtros aplicados", default=dict, blank=True)
    row_count = models.PositiveIntegerField("linhas exportadas", default=0)
    file_format = models.CharField("formato", max_length=10, default="csv")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "registro de exportação"
        verbose_name_plural = "registros de exportação"
