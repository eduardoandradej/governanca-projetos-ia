"""Contratos (portas) para integrações futuras — NENHUMA integração ativa no MVP.

Princípios: menor privilégio, somente leitura por padrão, credenciais em cofre/variáveis protegidas (nunca no
banco em texto claro), aprovação explícita para qualquer ação externa. Implementações reais (GitLab/GitHub,
Ansible Automation Platform/ansible-runner, Kubernetes/OpenShift, observabilidade, S3/MinIO) ficam fora do MVP.
Integrações reais ficam para versões futuras.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class JobStatus:
    external_id: str
    state: str  # queued | running | succeeded | failed | unknown
    url: str = ""


class CiCdPort(Protocol):
    def get_job_status(self, external_id: str) -> JobStatus: ...


class AutomationPort(Protocol):
    def get_run_status(self, external_id: str) -> JobStatus: ...


class DeploymentPort(Protocol):
    def describe_deployment(self, namespace: str, name: str) -> dict: ...


class CapacityCostPort(Protocol):
    def get_capacity_metrics(self, scope: str) -> dict: ...


class IntegrationDisabled(RuntimeError):
    pass


class NoOpAdapter:
    """Adaptador explícito: deixa claro que não há integração configurada (sem simular respostas)."""

    name = "noop"

    def _fail(self, *args, **kwargs):
        raise IntegrationDisabled("Integração não configurada neste ambiente (adaptador NoOp).")

    get_job_status = get_run_status = describe_deployment = get_capacity_metrics = _fail


def get_adapter(kind: str):
    """Ponto único de resolução. No MVP, sempre NoOp."""
    return NoOpAdapter()
