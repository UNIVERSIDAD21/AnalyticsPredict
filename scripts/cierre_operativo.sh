#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-reports/cierre/$(date -u +%F_%H%M%S)}"
mkdir -p "$OUT_DIR"

echo "[cierre] Ejecutando ciclo rápido de control..."
curl -sSf "$BASE_URL/salud" > "$OUT_DIR/salud.json"
curl -sSf "$BASE_URL/api/metricas/resumen-ejecutivo-compacto" > "$OUT_DIR/resumen_compacto.json"
curl -sSf "$BASE_URL/api/metricas/modo-estricto?score_minimo=75" > "$OUT_DIR/modo_estricto.json"
curl -sSf "$BASE_URL/api/metricas/alertas-ingestion?max_horas_sin_actualizar=24" > "$OUT_DIR/alertas_ingestion.json"

python3 - <<PY
import json, pathlib
p=pathlib.Path("$OUT_DIR")
r=json.loads((p/'resumen_compacto.json').read_text())
m=json.loads((p/'modo_estricto.json').read_text())

lineas=[]
lineas.append('# Cierre Operativo')
lineas.append('')
lineas.append(f"- GO/NO-GO: {r.get('go_no_go')}")
lineas.append(f"- score_global: {r.get('score_global')}")
lineas.append(f"- semaforo_global: {r.get('semaforo_global')}")
if not m.get('habilitar_recomendaciones'):
    lineas.append('- Motivos de bloqueo:')
    for x in m.get('motivos_bloqueo',[])[:5]:
        lineas.append(f"  - {x}")
else:
    lineas.append('- Recomendaciones habilitadas para siguiente ventana.')

out=p/'CIERRE_OPERATIVO.md'
out.write_text('\n'.join(lineas), encoding='utf-8')
print(out)
PY

echo "[cierre] reporte generado en $OUT_DIR"