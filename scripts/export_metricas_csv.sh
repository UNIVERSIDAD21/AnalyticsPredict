#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-reports/csv/$(date -u +%F_%H%M%S)}"
mkdir -p "$OUT_DIR"

curl -sSf "$BASE_URL/api/metricas/calidad-mercados?min_muestras=30&limite=100" > "$OUT_DIR/calidad_mercados.json"
curl -sSf "$BASE_URL/api/metricas/drift-mercados?min_muestras=20&limite=200" > "$OUT_DIR/drift_mercados.json"
curl -sSf "$BASE_URL/api/metricas/politica-mercados?min_muestras=30" > "$OUT_DIR/politica_mercados.json"

python3 - <<PY
import csv, json, pathlib
p = pathlib.Path("$OUT_DIR")

calidad = json.loads((p/'calidad_mercados.json').read_text())
drift = json.loads((p/'drift_mercados.json').read_text())
policy = json.loads((p/'politica_mercados.json').read_text())

with open(p/'calidad_mercados.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['deporte','mercado','n_resueltas','accuracy','brier','precision_label'])
    for r in calidad.get('ranking',[]):
        w.writerow([r.get('deporte'),r.get('mercado'),r.get('n_resueltas'),r.get('accuracy'),r.get('brier'),r.get('precision_label')])

with open(p/'drift_mercados.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['deporte','mercado','n_7d','n_prev_30d','brier_7d','brier_prev_30d','drift_pct','severidad'])
    for r in drift.get('items',[]):
        w.writerow([r.get('deporte'),r.get('mercado'),r.get('n_7d'),r.get('n_prev_30d'),r.get('brier_7d'),r.get('brier_prev_30d'),r.get('drift_pct'),r.get('severidad')])

with open(p/'politica_mercados.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['deporte','mercado','estado','bloqueado','motivo','brier','n_resueltas'])
    for r in policy.get('mercados',[]):
        w.writerow([r.get('deporte'),r.get('mercado'),r.get('estado'),r.get('bloqueado'),r.get('motivo'),r.get('brier'),r.get('n_resueltas')])

print(p)
PY

echo "[csv] exportado en $OUT_DIR"