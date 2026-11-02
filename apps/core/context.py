"""Contexto de requisição (correlation_id e IP) acessível a serviços de domínio e auditoria."""

import contextvars
import uuid

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)
_client_ip: contextvars.ContextVar[str | None] = contextvars.ContextVar("client_ip", default=None)


def get_correlation_id() -> str:
    value = _correlation_id.get()
    if not value:
        value = uuid.uuid4().hex
        _correlation_id.set(value)
    return value


def set_correlation_id(value: str | None):
    return _correlation_id.set(value)


def reset_correlation_id(token) -> None:
    _correlation_id.reset(token)


def get_client_ip() -> str | None:
    return _client_ip.get()


def set_client_ip(value: str | None):
    return _client_ip.set(value)


def reset_client_ip(token) -> None:
    _client_ip.reset(token)
