"""Mixins de modelo reutilizados pelos módulos de domínio."""

import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    """Identificador externo UUID (evita enumeração sequencial em URLs)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class AuthoredModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="criado por",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel, AuthoredModel):
    class Meta:
        abstract = True
