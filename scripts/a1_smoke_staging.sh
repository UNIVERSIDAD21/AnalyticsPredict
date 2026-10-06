#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   STAGING_BASE_URL="http://127.0.0.1:18000" ./scripts/a1_smoke_staging.sh

BASE_URL="${STAGING_BASE_URL:-http://127.0.0.1:18000}"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT_DIR="docs/reportes"
OUT_FILE="${OUT_DIR}/A1_SMOKE_STAGING_${TS}.md"

mkdir -p "$OUT_DIR"

pass() { echo "- ✅ $1" | tee -a "$OUT_FILE"; }
fail() { echo "- ❌ $1" | tee -a "$OUT_FILE"; exit 1; }

check_status() {
  local path="$1"
  local expected="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${path}" || true)
  if [[ "$code" == "$expected" ]]; then
    pass "${path} -> HTTP ${code}"
  else
    fail "${path} -> esperado ${expected}, recibido ${code}"
  fi
}

cat > "$OUT_FILE" <<EOF
# Smoke HTTP de Compose local single-user

Fecha (UTC): ${TS}
Base URL: ${BASE_URL}

## Verificaciones
EOF

check_status "/salud" "200"
check_status "/openapi.json" "200"

cat >> "$OUT_FILE" <<EOF

## Resultado
- Smoke HTTP local completado. No certifica BD, entrenamiento ni analítica.
EOF

echo "Reporte generado: $OUT_FILE"
