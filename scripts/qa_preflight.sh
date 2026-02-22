#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "[qa] root=$ROOT_DIR"

# 1) checks estáticos Python
python3 -m py_compile \
  "$ROOT_DIR/backend/app.py" \
  "$ROOT_DIR/backend/configuracion.py" \
  "$ROOT_DIR/backend/api/rutas_analisis_futbol.py" \
  "$ROOT_DIR/backend/api/rutas_metricas.py" \
  "$ROOT_DIR/backend/api/rutas_internas.py" \
  "$ROOT_DIR/backend/motor/resolucion_predicciones.py" \
  "$ROOT_DIR/backend/motor/resolucion_predicciones_futbol.py"

echo "[qa] py_compile OK"

# 2) endpoint base
curl -sSf "$BASE_URL/salud" >/dev/null
echo "[qa] /salud OK"

# 3) endpoints de calidad
curl -sSf "$BASE_URL/api/metricas/tablero-salud" >/dev/null
echo "[qa] /api/metricas/tablero-salud OK"

curl -sSf "$BASE_URL/api/metricas/calidad-mercados?min_muestras=30&limite=10" >/dev/null
echo "[qa] /api/metricas/calidad-mercados OK"

# 4) endpoint resumen
curl -sSf "$BASE_URL/api/metricas/resumen-deportes" >/dev/null
echo "[qa] /api/metricas/resumen-deportes OK"

# 5) alertas de ingestión
curl -sSf "$BASE_URL/api/metricas/alertas-ingestion?max_horas_sin_actualizar=24" >/dev/null
echo "[qa] /api/metricas/alertas-ingestion OK"

echo "[qa] PRE-FLIGHT COMPLETADO"
