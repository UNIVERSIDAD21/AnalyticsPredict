#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "[A6][ERROR] No se encontró Python del venv en $PYTHON_BIN"
  exit 1
fi

TS_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
REPORT_DIR="$ROOT_DIR/docs/reportes"
REPORT_FILE="$REPORT_DIR/A6_RC-A_${TS_UTC//:/-}.md"
mkdir -p "$REPORT_DIR"

run_step() {
  local name="$1"
  shift
  echo "\n[A6] >>> $name"
  "$@"
  echo "[A6] <<< OK: $name"
}

pushd "$ROOT_DIR" >/dev/null

run_step "Backend suite A2/A3/A4/A5" \
  "$PYTHON_BIN" -m pytest -q \
  backend/tests/api/test_auth_endpoints.py \
  backend/tests/api/test_bitacora_contract.py \
  backend/tests/api/test_apuestas_futbol_contract.py \
  backend/tests/test_observabilidad_http.py \
  backend/tests/test_observabilidad_http_endpoint.py \
  backend/tests/test_smoke_api.py

run_step "Frontend lint" npm --prefix "$FRONTEND_DIR" run lint
run_step "Frontend build" npm --prefix "$FRONTEND_DIR" run build

cat >"$REPORT_FILE" <<EOF
# Reporte RC-A (A6) — Validación integral

- Fecha UTC: $TS_UTC
- Resultado global: APROBADO
- Gate P0/P1: 0 bloqueantes detectados en validación automatizada del bloque

## Evidencia ejecutada

1. Backend (A2/A3/A4/A5):
   - test_auth_endpoints.py
   - test_bitacora_contract.py
   - test_apuestas_futbol_contract.py
   - test_observabilidad_http.py
   - test_observabilidad_http_endpoint.py
   - test_smoke_api.py

2. Frontend:
   - npm run lint
   - npm run build

## Nota operativa

Este reporte cubre el gate técnico automatizable de la Fase A. Para release comercial, mantener chequeos manuales de despliegue/staging según checklists de operación.
EOF

echo "\n[A6] Reporte generado: ${REPORT_FILE#$ROOT_DIR/}"

echo "[A6] RC-A completado exitosamente"

popd >/dev/null
