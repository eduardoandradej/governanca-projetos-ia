#!/usr/bin/env bash
# Backup do PostgreSQL (formato custom) + anexos privados, com checksum.
# Uso: ./scripts/backup.sh /caminho/destino     (lê DB_* e PRIVATE_MEDIA_ROOT do ambiente/.env)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }
DEST="${1:?Informe o diretório de destino}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$DEST"
export PGPASSWORD="${DB_PASSWORD:?}"
pg_dump -h "${DB_HOST:-127.0.0.1}" -p "${DB_PORT:-5432}" -U "${DB_USER:-govia}" -Fc -f "$DEST/govia-$STAMP.dump" "${DB_NAME:-govia}"
MEDIA="${PRIVATE_MEDIA_ROOT:-var/private_media}"
if [ -d "$MEDIA" ]; then tar -czf "$DEST/anexos-$STAMP.tar.gz" -C "$(dirname "$MEDIA")" "$(basename "$MEDIA")"; fi
( cd "$DEST" && sha256sum ./*"$STAMP"* > "SHA256SUMS-$STAMP" )
echo "Backup concluído: $DEST (carimbo $STAMP)"
