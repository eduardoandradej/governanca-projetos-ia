"""T-012: duas aprovações concorrentes não duplicam avanço, decisão nem auditoria (PostgreSQL real, conexões distintas)."""

import threading

import pytest
from django.db import connection

from apps.auditlog.models import AuditEvent
from apps.governance import services as gov
from apps.governance.models import GateDecision
from apps.lifecycle.models import StageStatus, StageStatusHistory
from tests_support.factories import complete_stage_requirements


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_T012_concurrent_approvals_single_advance(org_a, project_a):
    stage = project_a.stages.get(order=1)
    complete_stage_requirements(org_a, stage)
    gov.request_gate(stage.pk, actor=org_a.manager)
    approvers = [org_a.approver, org_a.sponsor]  # dois aprovadores habilitados distintos
    barrier = threading.Barrier(len(approvers))
    results: list[str] = []

    def approve(user):
        try:
            barrier.wait(timeout=5)
            gov.approve_gate(stage.pk, actor=user, justification=f"Aprovação concorrente {user}", request_number=1)
            results.append("ok")
        except Exception as exc:  # noqa: BLE001
            results.append(type(exc).__name__)
        finally:
            connection.close()

    threads = [threading.Thread(target=approve, args=(u,)) for u in approvers]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=20)
    assert sorted(results) == ["DomainError", "ok"], results
    assert GateDecision.objects.filter(gate__stage=stage, decision="approved").count() == 1
    assert StageStatusHistory.objects.filter(stage=stage, to_status=StageStatus.APPROVED).count() == 1
    stage2 = project_a.stages.get(order=2)
    assert StageStatusHistory.objects.filter(stage=stage2, to_status=StageStatus.IN_PROGRESS).count() == 1
    assert AuditEvent.objects.filter(action="gate.approve", result="success").count() == 1
