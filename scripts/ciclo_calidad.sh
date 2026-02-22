#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
LIMITE_BASKET="${LIMITE_BASKET:-2000}"
LIMITE_FUTBOL="${LIMITE_FUTBOL:-2000}"
MIN_MUESTRAS="${MIN_MUESTRAS:-30}"
OUT_DIR="${OUT_DIR:-reports/calidad/$(date -u +%F_%H%M%S)}"

mkdir -p "$OUT_DIR"

echo "[calidad] Verificando API en $BASE_URL/salud"
curl -sSf "$BASE_URL/salud" > "$OUT_DIR/salud.json"

echo "[calidad] Resolviendo predicciones baloncesto..."
curl -sSf -X POST "$BASE_URL/api/interno/resolver-predicciones" \
  -H 'Content-Type: application/json' \
  -d "{\"limite\":$LIMITE_BASKET}" > "$OUT_DIR/resolver_baloncesto.json"

echo "[calidad] Resolviendo predicciones fútbol..."
curl -sSf -X POST "$BASE_URL/api/interno/resolver-predicciones-futbol" \
  -H 'Content-Type: application/json' \
  -d "{\"limite\":$LIMITE_FUTBOL}" > "$OUT_DIR/resolver_futbol.json"

echo "[calidad] Capturando tablero de salud..."
curl -sSf "$BASE_URL/api/metricas/tablero-salud" > "$OUT_DIR/tablero_salud.json"

echo "[calidad] Capturando ranking de mercados..."
curl -sSf "$BASE_URL/api/metricas/calidad-mercados?min_muestras=$MIN_MUESTRAS&limite=20" > "$OUT_DIR/calidad_mercados.json"

python3 - <<PY
import json, pathlib
p=pathlib.Path("$OUT_DIR")
t=json.loads((p/'tablero_salud.json').read_text())
rb=json.loads((p/'resolver_baloncesto.json').read_text())
rf=json.loads((p/'resolver_futbol.json').read_text())
print("\n=== RESUMEN CICLO CALIDAD ===")
print("score_global:", t.get('score_global'))
print("baloncesto resueltas:", rb.get('resumen',{}).get('resueltas'))
print("futbol resueltas:", rf.get('resumen',{}).get('resueltas'))
for d in t.get('deportes',[]):
    print(f"- {d.get('deporte')}: n_total={d.get('n_total')} n_resueltas={d.get('n_resueltas')} brier={d.get('brier')}")
print("salida:", p)
PY

echo "[calidad] OK"