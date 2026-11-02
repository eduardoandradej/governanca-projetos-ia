"""API v1, exportações e navegação (T-015, T-020, T-023, T-026, testes de interface)."""

import pytest
from django.urls import reverse

from apps.auditlog.models import AuditEvent, ExportRecord
from apps.core.exports import neutralize
from apps.integrations.ports import IntegrationDisabled, get_adapter
from apps.risks import services as rs
from apps.risks.models import DecisionRecord

pytestmark = pytest.mark.django_db


def test_T023_api_requires_authentication(client, project_a):
    for url in ("/api/v1/projetos/", "/api/v1/indicadores/", f"/api/v1/projetos/{project_a.pk}/"):
        assert client.get(url).status_code in (401, 403), url


def test_T023_api_scope_isolation(client, org_a, org_b, project_a):
    project_b = org_b.create_project(code="IA-B9")
    client.force_login(org_a.reader)
    data = client.get("/api/v1/projetos/").json()
    codes = [p["code"] for p in data["results"]]
    assert codes == ["IA-ALFA-01"] and data["count"] == 1
    assert client.get(f"/api/v1/projetos/{project_b.pk}/").status_code == 404
    assert client.get(f"/api/v1/projetos/{project_b.pk}/stages/").status_code == 404
    stages = client.get(f"/api/v1/projetos/{project_a.pk}/stages/").json()
    assert [s["order"] for s in stages] == [1, 2, 3, 4, 5, 6, 7]
    assert client.get(f"/api/v1/indicadores/?projeto={project_b.pk}").status_code == 404
    m = client.get("/api/v1/indicadores/").json()
    assert m["scope"]["projects"] == 1 and {x["code"] for x in m["metrics"]} >= {"K01", "K12"}


def test_api_risks_filtered_and_scoped(client, org_a, org_b, project_a):
    rs.create_risk(actor=org_a.manager, project=project_a, title="Viés", category="ethics", probability=5,
                   impact=5, owner=org_a.executor)
    pb = org_b.create_project(code="IA-B8")
    rs.create_risk(actor=org_b.manager, project=pb, title="Outro", category="data", probability=5, impact=5,
                   owner=org_b.executor)
    client.force_login(org_a.auditor)
    data = client.get("/api/v1/riscos/?nivel=critical").json()
    assert [r["title"] for r in data["results"]] == ["Viés"]


def test_T026_unauthorized_user_cannot_create_favorable_decision_via_api(client, org_a, project_a):
    client.force_login(org_a.executor)  # sem decision.record
    resp = client.post(f"/api/v1/projetos/{project_a.pk}/decisions/", {
        "agenda": "x", "alternatives": "a", "decision": "d", "rationale": "r"}, content_type="application/json")
    assert resp.status_code == 403
    client.force_login(org_a.manager)
    resp = client.post(f"/api/v1/projetos/{project_a.pk}/decisions/", {
        "agenda": "Adoção de LLM local", "alternatives": "nuvem; local", "decision": "local",
        "rationale": "Soberania de dados"}, content_type="application/json")
    assert resp.status_code == 201
    dec_id = resp.json()["id"]
    # proponente não aprova a própria decisão; executor sem papel também não
    for user in (org_a.manager, org_a.executor):
        client.force_login(user)
        r = client.post(f"/api/v1/decisoes/{dec_id}/decide/", {"approve": True, "note": "aprovado"},
                        content_type="application/json")
        assert r.status_code == 403
    assert DecisionRecord.objects.get(pk=dec_id).status == "proposed"
    client.force_login(org_a.sponsor)
    r = client.post(f"/api/v1/decisoes/{dec_id}/decide/", {"approve": True, "note": "Aprovado em comitê"},
                    content_type="application/json")
    assert r.status_code == 200 and r.json()["status"] == "approved"


def test_api_write_requires_csrf_for_session(org_a, project_a):
    from django.test import Client

    c = Client(enforce_csrf_checks=True)
    c.force_login(org_a.manager)
    resp = c.post(f"/api/v1/projetos/{project_a.pk}/decisions/", {"agenda": "x", "alternatives": "a",
                  "decision": "d", "rationale": "r"}, content_type="application/json")
    assert resp.status_code == 403


@pytest.mark.parametrize("value,expected", [
    ("=HYPERLINK(\"http://x\")", "'=HYPERLINK(\"http://x\")"), ("+1+1", "'+1+1"), ("-2", "'-2"), ("@SUM(A1)", "'@SUM(A1)"),
    ("\t=1", "'\t=1"), ("normal", "normal"), (None, ""), ("Projeto =x", "Projeto =x"),
])
def test_T020_csv_formula_neutralization(value, expected):
    assert neutralize(value) == expected


def test_T020_export_neutralizes_and_is_audited(client, org_a):
    org_a.create_project(code="IA-CSV", name="=cmd|' /C calc'!A0")
    client.force_login(org_a.manager)
    resp = client.get(reverse("analytics:export_projects"))
    body = resp.content.decode("utf-8-sig")
    assert resp.status_code == 200 and "attachment" in resp["Content-Disposition"]
    assert "\"'=cmd|' /C calc'!A0\"" in body
    assert ExportRecord.objects.filter(user=org_a.manager, report="projetos", row_count=1).exists()
    assert AuditEvent.objects.filter(action="export.csv", actor=org_a.manager).exists()


def test_T015_export_restricted_and_scoped(client, org_a, org_b, project_a):
    org_b.create_project(code="IA-BETA-X")
    client.force_login(org_a.reader)  # sem export.data
    assert client.get(reverse("analytics:export_projects")).status_code == 403
    client.force_login(org_a.manager)
    body = client.get(reverse("analytics:export_projects")).content.decode("utf-8-sig")
    assert "IA-ALFA-01" in body and "IA-BETA-X" not in body
    assert client.get(reverse("analytics:export_projects") + f"?organizacao={org_b.org.pk}").status_code == 404


def test_audit_export_only_for_auditors(client, org_a, project_a):
    client.force_login(org_a.manager)
    assert client.get(reverse("auditlog:export")).status_code == 403
    client.force_login(org_a.auditor)
    resp = client.get(reverse("auditlog:export"))
    assert resp.status_code == 200 and "project.create" in resp.content.decode("utf-8-sig")


def test_integrations_are_explicit_noop():
    with pytest.raises(IntegrationDisabled):
        get_adapter("cicd").get_job_status("123")


NAV_PAGES = [
    "core:dashboard", "projects:list", "organizations:list", "governance:queue", "governance:framework",
    "risks:list", "evidence:list", "analytics:home", "analytics:insights", "analytics:lessons",
]


def test_navigation_pages_render_for_each_role(client, org_a, project_a):
    for key in ("manager", "reader", "auditor", "sponsor", "approver", "security"):
        client.force_login(getattr(org_a, key))
        for name in NAV_PAGES:
            assert client.get(reverse(name)).status_code == 200, (key, name)
        for name in ("projects:detail", "lifecycle:tasks", "evidence:project", "risks:project", "risks:decisions",
                     "analytics:project_data", "analytics:project_knowledge", "governance:responsible_ai"):
            assert client.get(reverse(name, args=[project_a.pk])).status_code == 200, (key, name)


def test_responses_have_security_headers(client, org_a):
    client.force_login(org_a.manager)
    resp = client.get(reverse("core:dashboard"))
    assert resp["X-Frame-Options"] == "DENY" and resp["X-Content-Type-Options"] == "nosniff"
    assert resp["Referrer-Policy"] == "same-origin" and resp["X-Request-ID"]
