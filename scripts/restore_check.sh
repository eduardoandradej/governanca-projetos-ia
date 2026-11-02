#!/usr/bin/env bash
# Valida um backup restaurando-o em um banco TEMPORÁRIO e comparando contagens com a origem.
# Nunca sobrescreve o banco da aplicação. Uso: ./scripts/restore_check.sh arquivo.dump
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }
DUMP="${1:?Informe o arquivo .dump}"
export PGPASSWORD="${DB_PASSWORD:?}"
H=(-h "${DB_HOST:-127.0.0.1}" -p "${DB_PORT:-5432}" -U "${DB_USER:-govia}")
TMPDB="govia_restore_check_$(date +%s)"
createdb "${H[@]}" "$TMPDB"
trap 'dropdb "${H[@]}" --if-exists "$TMPDB"' EXIT
pg_restore "${H[@]}" -d "$TMPDB" --no-owner "$DUMP"
FAIL=0
for t in projects_project lifecycle_stageinstance governance_gatedecision auditlog_auditevent risks_risk evidence_evidenceversion analytics_insight; do
  a=$(psql "${H[@]}" -tAc "SELECT count(*) FROM $t" "${DB_NAME:-govia}")
  b=$(psql "${H[@]}" -tAc "SELECT count(*) FROM $t" "$TMPDB")
  printf "%-32s origem=%-6s restaurado=%-6s %s\n" "$t" "$a" "$b" "$([ "$a" = "$b" ] && echo OK || echo DIVERGE)"
  [ "$a" = "$b" ] || FAIL=1
done
trig=$(psql "${H[@]}" -tAc "SELECT count(*) FROM pg_trigger WHERE tgname='auditlog_auditevent_append_only'" "$TMPDB")
echo "gatilho append-only restaurado: $trig"
[ "$trig" = "1" ] || FAIL=1
exit $FAIL
