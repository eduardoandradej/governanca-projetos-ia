#!/usr/bin/env bash
# Executa lint, checagens do Django e a suíte de testes no PostgreSQL de teste isolado.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
.venv/bin/ruff check .
$PY manage.py check
$PY manage.py makemigrations --check --dry-run
.venv/bin/pytest -q "$@"
