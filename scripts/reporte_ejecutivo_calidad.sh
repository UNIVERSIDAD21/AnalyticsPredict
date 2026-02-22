#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-reports/ejecutivo/$(date -u +%F_%H%M%S)}"
mkdir -p "$OUT_DIR"

curl -sSf "$BASE_URL/api/metricas/tablero-salud" > "$OUT_DIR/tablero_salud.json"
curl -sSf "$BASE_URL/api/metricas/calidad-mercados?min_muestras=30&limite=20" > "$OUT_DIR/calidad_mercados.json"
curl -sSf "$BASE_URL/api/metricas/recomendaciones-accion" > "$OUT_DIR/recomendaciones_accion.json"
curl -sSf "$BASE_URL/api/metricas/alertas-ingestion?max_horas_sin_actualizar=24" > "$OUT_DIR/alertas_ingestion.json"
curl -sSf "$BASE_URL/api/metricas/sugerencias-umbrales?min_muestras=30" > "$OUT_DIR/sugerencias_umbrales.json"
curl -sSf "$BASE_URL/api/metricas/modo-estricto?score_minimo=75" > "$OUT_DIR/modo_estricto.json"
curl -sSf "$BASE_URL/api/metricas/resumen-ejecutivo-compacto?min_muestras=30" > "$OUT_DIR/resumen_compacto.json"

python3 - <<PY
import json, pathlib
p=pathlib.Path("$OUT_DIR")
t=json.loads((p/'tablero_salud.json').read_text())
r=json.loads((p/'recomendaciones_accion.json').read_text())
a=json.loads((p/'alertas_ingestion.json').read_text())
u=json.loads((p/'sugerencias_umbrales.json').read_text())
m=json.loads((p/'modo_estricto.json').read_text())
c=json.loads((p/'resumen_compacto.json').read_text())

lineas=[]
lineas.append('# Reporte ejecutivo de calidad')
lineas.append('')
lineas.append(f"- score_global: {t.get('score_global')}")
lineas.append(f"- semaforo_global: {r.get('semaforo_global')}")
lineas.append(f"- go_no_go: {'GO' if m.get('habilitar_recomendaciones') else 'NO-GO'}")
if not m.get('habilitar_recomendaciones'):
    for motivo in m.get('motivos_bloqueo',[])[:3]:
        lineas.append(f"  - bloqueo: {motivo}")
lineas.append('')
lineas.append('## Resumen compacto (30s)')
lineas.append(f"- GO/NO-GO: {c.get('go_no_go')}")
lineas.append(f"- score: {c.get('score_global')} | semaforo: {c.get('semaforo_global')}")
lineas.append(f"- alertas_criticas: {c.get('alertas_criticas')}")
for a_top in c.get('top_acciones',[])[:3]:
    lineas.append(f"- top: {a_top}")

lineas.append('')
lineas.append('## Estado por deporte')
for d in t.get('deportes',[]):
    lineas.append(
      f"- {d.get('deporte')}: n_total={d.get('n_total')} n_resueltas={d.get('n_resueltas')} "
      f"brier={d.get('brier')} accuracy={d.get('accuracy')}"
    )
lineas.append('')
lineas.append('## Alertas de ingestión')
lineas.append(f"- resumen: {a.get('resumen')}")
for it in a.get('alertas',[])[:8]:
    lineas.append(f"- {it.get('fuente')}: stale={it.get('stale')} sev={it.get('severidad')} horas={it.get('horas_sin_actualizar')}")

lineas.append('')
lineas.append('## Sugerencias de umbrales')
for s in u.get('sugerencias',[])[:5]:
    lineas.append(
      f"- {s.get('deporte')}: warning={s.get('warning_brier_sugerido')} bloqueo={s.get('bloqueo_brier_sugerido')} muestra={s.get('muestra_base')}"
    )

lineas.append('')
lineas.append('## Acciones priorizadas')
for ac in r.get('acciones',[])[:10]:
    lineas.append(f"- [{ac.get('prioridad')}/{ac.get('semaforo')}] {ac.get('accion')} — {ac.get('motivo')}")

out=p/'REPORTE_EJECUTIVO.md'
out.write_text('\n'.join(lineas), encoding='utf-8')
print(out)
PY

echo "[reporte] generado en $OUT_DIR"