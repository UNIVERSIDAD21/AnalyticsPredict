#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <backup_dir_ts>" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_DIR="$1"

AUTH_DB="${AUTH_DB_PATH:-$ROOT_DIR/backend/data/auth.db}"
PAGOS_DB="${PAGOS_DB_PATH:-$ROOT_DIR/backend/data/pagos.db}"

mkdir -p "$(dirname "$AUTH_DB")" "$(dirname "$PAGOS_DB")"

if [[ -f "$SRC_DIR/auth.db" ]]; then
  cp "$SRC_DIR/auth.db" "$AUTH_DB"
fi
if [[ -f "$SRC_DIR/pagos.db" ]]; then
  cp "$SRC_DIR/pagos.db" "$PAGOS_DB"
fi

echo "restore_ok"
