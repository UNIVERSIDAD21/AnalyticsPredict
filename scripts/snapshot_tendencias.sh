#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-reports/tendencias}"
mkdir -p "$OUT_DIR"

TABLERO_JSON=$(curl -sSf "$BASE_URL/api/metricas/tablero-salud")
DRIFT_JSON=$(curl -sSf "$BASE_URL/api/metricas/drift-mercados?min_muestras=20&limite=30")
POLICY_JSON=$(curl -sSf "$BASE_URL/api/metricas/politica-mercados?min_muestras=30")

python3 - <<PY
import json, pathlib, datetime
out_dir=pathlib.Path("$OUT_DIR")
row={
  "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
  "tablero": json.loads('''$TABLERO_JSON'''),
  "drift": json.loads('''$DRIFT_JSON'''),
  "policy": json.loads('''$POLICY_JSON'''),
}
jsonl=out_dir/'health_snapshots.jsonl'
with jsonl.open('a',encoding='utf-8') as f:
  f.write(json.dumps(row, ensure_ascii=False)+"\n")
print(jsonl)
PY

echo "[snapshot] tendencia guardada en $OUT_DIR/health_snapshots.jsonl"