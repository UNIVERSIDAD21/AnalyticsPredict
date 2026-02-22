#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "=== ESTADO UNIFICADO ANALYTICSPREDICT ==="
echo "Fecha UTC: $(date -u +%F' '%T)"
echo

echo "[1/5] Salud API"
curl -sSf "$BASE_URL/salud" | python3 -m json.tool | sed -n '1,40p'
echo

echo "[2/5] Resumen ejecutivo compacto"
curl -sSf "$BASE_URL/api/metricas/resumen-ejecutivo-compacto" | python3 -m json.tool | sed -n '1,80p'
echo

echo "[3/5] Modo estricto"
curl -sSf "$BASE_URL/api/metricas/modo-estricto?score_minimo=75" | python3 -m json.tool | sed -n '1,80p'
echo

echo "[4/5] Alertas ingestión"
curl -sSf "$BASE_URL/api/metricas/alertas-ingestion?max_horas_sin_actualizar=24" | python3 -m json.tool | sed -n '1,120p'
echo

echo "[5/5] Política mercados (resumen)"
curl -sSf "$BASE_URL/api/metricas/politica-mercados?min_muestras=30" | python3 - <<'PY'
import sys, json
j=json.load(sys.stdin)
print(json.dumps({'exito':j.get('exito'),'resumen':j.get('resumen')}, indent=2, ensure_ascii=False))
PY

echo
echo "=== FIN ESTADO UNIFICADO ==="