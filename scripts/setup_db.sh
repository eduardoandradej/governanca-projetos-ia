#!/usr/bin/env bash
# Cria (de forma idempotente) o papel e o banco PostgreSQL usados pela aplicação.
# Uso: DB_PASSWORD=... ./scripts/setup_db.sh
# Por padrão executa psql como o usuário 'postgres' via sudo; ajuste com PSQL_AS="su postgres -c".
set -euo pipefail
DB_NAME="${DB_NAME:-govia}"
DB_USER="${DB_USER:-govia}"
: "${DB_PASSWORD:?Defina DB_PASSWORD}"

pg() {  # executa SQL como superusuário do PostgreSQL
  if [ "${PSQL_AS:-sudo}" = "sudo" ]; then sudo -u postgres psql -v ON_ERROR_STOP=1 -tAc "$1"
  else su postgres -c "psql -v ON_ERROR_STOP=1 -tAc \"$1\""; fi
}

if [ "$(pg "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'")" != "1" ]; then
  # CREATEDB só é necessário para criar o banco de testes (test_${DB_NAME}); remova em produção.
  pg "CREATE ROLE ${DB_USER} LOGIN CREATEDB PASSWORD '${DB_PASSWORD}'" >/dev/null
  echo "Papel ${DB_USER} criado."
else
  echo "Papel ${DB_USER} já existe (senha não alterada)."
fi

if [ "$(pg "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'")" != "1" ]; then
  pg "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}" >/dev/null
  echo "Banco ${DB_NAME} criado."
else
  echo "Banco ${DB_NAME} já existe."
fi
