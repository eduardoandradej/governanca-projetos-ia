"""Serviço único de gravação de eventos de auditoria."""

from __future__ import annotations

import contextvars
import functools
import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import transaction

from apps.core import context

from .models import ActorType, AuditEvent, AuditResult

logger = logging.getLogger("govia.audit")

SENSITIVE_KEYS = ("password", "senha", "token", "secret", "segredo", "key", "chave", "cookie", "session")
MAX_VALUE_LEN = 500

# Eventos de negação/falha emitidos dentro de um serviço transacional são enfileirados e gravados
# DEPOIS do rollback; do contrário, a própria negação seria desfeita junto com a transação.
_pending: contextvars.ContextVar[list | None] = contextvars.ContextVar("audit_pending", default=None)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize(value)
    if isinstance(value, list | tuple):
        return [_sanitize_value(v) for v in value][:50]
    if isinstance(value, UUID | Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, str) and len(value) > MAX_VALUE_LEN:
        return value[:MAX_VALUE_LEN] + "…"
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)[:MAX_VALUE_LEN]


def sanitize(data: dict | None) -> dict | None:
    """Remove chaves sensíveis e limita tamanho; nunca registra senhas, tokens ou conteúdo de documentos."""
    if data is None:
        return None
    clean = {}
    for key, value in data.items():
        if any(s in str(key).lower() for s in SENSITIVE_KEYS):
            clean[key] = "[REMOVIDO]"
        else:
            clean[key] = _sanitize_value(value)
    return clean


def record(
    action: str,
    *,
    actor=None,
    result: str = AuditResult.SUCCESS,
    organization_id: UUID | str | None = None,
    project_id: UUID | str | None = None,
    entity=None,
    entity_type: str = "",
    entity_id: str = "",
    entity_version: str | int = "",
    before: dict | None = None,
    after: dict | None = None,
    reason: str = "",
    actor_repr: str = "",
    system: bool = False,
) -> AuditEvent | None:
    if result != AuditResult.SUCCESS and _pending.get() is not None:
        _pending.get().append(
            dict(
                action=action, actor=actor, result=result, organization_id=organization_id, project_id=project_id,
                entity=entity, entity_type=entity_type, entity_id=entity_id, entity_version=entity_version,
                before=before, after=after, reason=reason, actor_repr=actor_repr, system=system,
            )
        )
        return None
    if entity is not None:
        entity_type = entity_type or entity._meta.label
        entity_id = entity_id or str(entity.pk)
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None
    if system:
        actor_type = ActorType.SYSTEM
    elif actor is None:
        actor_type = ActorType.ANONYMOUS
    else:
        actor_type = ActorType.USER
    event = AuditEvent.objects.create(
        actor=actor,
        actor_type=actor_type,
        actor_repr=(actor_repr or (actor.get_username() if actor else ""))[:150],
        organization_id=organization_id,
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id)[:64],
        entity_version=str(entity_version)[:32],
        before=sanitize(before),
        after=sanitize(after),
        ip_address=context.get_client_ip(),
        correlation_id=context.get_correlation_id(),
        result=result,
        reason=reason,
    )
    logger.info("audit action=%s result=%s entity=%s:%s", action, result, entity_type, entity_id)
    return event


def atomic_service(func):
    """`transaction.atomic` para serviços de domínio, preservando eventos de negação/falha após rollback."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if _pending.get() is not None:  # serviço aninhado: o mais externo grava a fila
            with transaction.atomic():
                return func(*args, **kwargs)
        queue: list[dict] = []
        token = _pending.set(queue)
        try:
            with transaction.atomic():
                result = func(*args, **kwargs)
        finally:
            _pending.reset(token)
            for item in queue:
                record(**item)
        return result

    return wrapper
