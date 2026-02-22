#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[full] 1) QA preflight"
bash scripts/qa_preflight.sh

echo "[full] 2) Ciclo de calidad"
bash scripts/ciclo_calidad.sh

echo "[full] 3) Check modo estricto"
bash scripts/check_modo_estricto.sh

echo "[full] 4) Reporte ejecutivo"
bash scripts/reporte_ejecutivo_calidad.sh

echo "[full] 5) Snapshot tendencias"
bash scripts/snapshot_tendencias.sh

echo "[full] Completado"
