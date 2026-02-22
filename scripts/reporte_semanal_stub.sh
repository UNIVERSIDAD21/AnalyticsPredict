#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-reports/semanal/$(date -u +%F_%H%M%S)}"
mkdir -p "$OUT_DIR"
cp docs/REPORTE_SEMANAL_TEMPLATE.md "$OUT_DIR/REPORTE_SEMANAL.md"
echo "[semanal] Template creado: $OUT_DIR/REPORTE_SEMANAL.md"