#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   STAGING_BASE_URL="http://localhost:18000" ./scripts/a1_smoke_staging.sh

BASE_URL="${STAGING_BASE_URL:-http://localhost:18000}"
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
  code=$(curl -s -o /tmp/a1_smoke_resp.txt -w "%{http_code}" "${BASE_URL}${path}" || true)
  if [[ "$code" == "$expected" ]]; then
    pass "${path} -> HTTP ${code}"
  else
    echo "Respuesta: $(cat /tmp/a1_smoke_resp.txt 2>/dev/null || true)" | tee -a "$OUT_FILE"
    fail "${path} -> esperado ${expected}, recibido ${code}"
  fi
}

cat > "$OUT_FILE" <<EOF
# A1 Smoke Staging

Fecha (UTC): ${TS}
Base URL: ${BASE_URL}

## Verificaciones
EOF

check_status "/salud" "200"
check_status "/api/pagos/matriz-estados" "200"
check_status "/api/onboarding/estado" "401"

cat >> "$OUT_FILE" <<EOF

## Resultado
- Smoke staging completado.
- Nota: endpoints autenticados pueden devolver 401 sin token válido (esperado en smoke sin sesión).
EOF

echo "Reporte generado: $OUT_FILE"
