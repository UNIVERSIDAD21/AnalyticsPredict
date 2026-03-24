#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/backups/sqlite}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

AUTH_DB="${AUTH_DB_PATH:-$ROOT_DIR/backend/data/auth.db}"
PAGOS_DB="${PAGOS_DB_PATH:-$ROOT_DIR/backend/data/pagos.db}"

mkdir -p "$OUT_DIR/$TS"

copy_if_exists () {
  local src="$1"; local dst="$2"
  if [[ -f "$src" ]]; then
    cp "$src" "$dst"
  else
    echo "WARN: no existe $src" >&2
  fi
}

copy_if_exists "$AUTH_DB" "$OUT_DIR/$TS/auth.db"
copy_if_exists "$PAGOS_DB" "$OUT_DIR/$TS/pagos.db"

echo "$OUT_DIR/$TS"
