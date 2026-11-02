"""Fixtures compartilhadas. Todos os testes rodam no PostgreSQL de teste isolado (test_govia)."""

import pytest
from django.db import connection

from apps.organizations.models import Role
from tests_support.factories import OrgSetup, make_org_setup


@pytest.fixture(autouse=True)
def _ensure_postgresql(db):
    assert connection.vendor == "postgresql", "Os testes devem executar em PostgreSQL (regra do projeto)."


@pytest.fixture
def org_a(db) -> OrgSetup:
    return make_org_setup("Organização Alfa", prefix="a")


@pytest.fixture
def org_b(db) -> OrgSetup:
    return make_org_setup("Organização Beta", prefix="b")


@pytest.fixture
def project_a(org_a):
    return org_a.create_project(code="IA-ALFA-01")


@pytest.fixture
def roles():
    return Role
