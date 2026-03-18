#!/usr/bin/env bash
set -euo pipefail

# Tick automático B4 para ejecutar scheduler + procesamiento de cola.
# Uso:
#   API_BASE_URL=http://127.0.0.1:8000 \
#   USUARIO_ID=00000000-0000-0000-0000-000000000001 \
#   USUARIO_EMAIL=tu@correo.com \
#   TIPO=todos \
#   MAX_ITEMS=50 \
#   bash scripts/notificaciones_scheduler_tick.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
USUARIO_ID="${USUARIO_ID:-00000000-0000-0000-0000-000000000001}"
USUARIO_EMAIL="${USUARIO_EMAIL:-}"
TIPO="${TIPO:-todos}"
MAX_ITEMS="${MAX_ITEMS:-50}"

if [[ -z "$USUARIO_EMAIL" ]]; then
  echo "ERROR: USUARIO_EMAIL es requerido" >&2
  exit 1
fi

HEADERS=(
  -H "Content-Type: application/json"
  -H "X-Usuario-Id: ${USUARIO_ID}"
  -H "X-Usuario-Email: ${USUARIO_EMAIL}"
)

echo "[b4] encolando scheduler tipo=${TIPO}"
curl -fsS -X POST "${API_BASE_URL}/api/notificaciones/scheduler/encolar?tipo=${TIPO}" "${HEADERS[@]}" >/tmp/b4_scheduler_encolar.json
cat /tmp/b4_scheduler_encolar.json

echo "[b4] procesando cola max_items=${MAX_ITEMS}"
curl -fsS -X POST "${API_BASE_URL}/api/notificaciones/procesar-cola?max_items=${MAX_ITEMS}" "${HEADERS[@]}" >/tmp/b4_scheduler_procesar.json
cat /tmp/b4_scheduler_procesar.json

echo "[b4] tick completado"
