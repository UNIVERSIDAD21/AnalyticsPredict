#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-reports/semanal_auto/$(date -u +%F_%H%M%S)}"
mkdir -p "$OUT_DIR"

curl -sSf "$BASE_URL/api/metricas/tablero-salud" > "$OUT_DIR/tablero_salud.json"
curl -sSf "$BASE_URL/api/metricas/calidad-mercados?min_muestras=30&limite=50" > "$OUT_DIR/calidad_mercados.json"
curl -sSf "$BASE_URL/api/metricas/recomendaciones-accion" > "$OUT_DIR/recomendaciones_accion.json"
curl -sSf "$BASE_URL/api/metricas/drift-mercados?min_muestras=20&limite=50" > "$OUT_DIR/drift_mercados.json"
curl -sSf "$BASE_URL/api/metricas/alertas-ingestion?max_horas_sin_actualizar=24" > "$OUT_DIR/alertas_ingestion.json"
curl -sSf "$BASE_URL/api/metricas/sugerencias-umbrales?min_muestras=30" > "$OUT_DIR/sugerencias_umbrales.json"
curl -sSf "$BASE_URL/api/metricas/modo-estricto?score_minimo=75" > "$OUT_DIR/modo_estricto.json"

python3 - <<PY
import json, pathlib
p=pathlib.Path("$OUT_DIR")
t=json.loads((p/'tablero_salud.json').read_text())
q=json.loads((p/'calidad_mercados.json').read_text())
r=json.loads((p/'recomendaciones_accion.json').read_text())
d=json.loads((p/'drift_mercados.json').read_text())
a=json.loads((p/'alertas_ingestion.json').read_text())
u=json.loads((p/'sugerencias_umbrales.json').read_text())
m=json.loads((p/'modo_estricto.json').read_text())

lines=[]
lines.append('# Reporte Semanal Automático')
lines.append('')
lines.append(f"- score_global: {t.get('score_global')}")
lines.append(f"- resumen: {t.get('resumen_ejecutivo')}")
lines.append(f"- semaforo_global: {r.get('semaforo_global')}")
lines.append(f"- go_no_go: {'GO' if m.get('habilitar_recomendaciones') else 'NO-GO'}")
if not m.get('habilitar_recomendaciones'):
    for motivo in m.get('motivos_bloqueo',[])[:4]:
        lines.append(f"  - bloqueo: {motivo}")
lines.append('')
lines.append('## Métricas por deporte')
for dep in t.get('deportes',[]):
    lines.append(f"- {dep.get('deporte')}: n_total={dep.get('n_total')} n_resueltas={dep.get('n_resueltas')} accuracy={dep.get('accuracy')} brier={dep.get('brier')}")

lines.append('')
lines.append('## Mercados críticos (Brier alto)')
crit=[x for x in q.get('ranking',[]) if x.get('brier') is not None and x.get('brier')>0.26]
for x in crit[:10]:
    lines.append(f"- {x.get('deporte')}/{x.get('mercado')}: brier={x.get('brier')} n={x.get('n_resueltas')}")
if not crit:
    lines.append('- Sin mercados críticos con muestra suficiente.')

lines.append('')
lines.append('## Drift por mercado (top)')
for x in d.get('items',[])[:10]:
    lines.append(f"- {x.get('deporte')}/{x.get('mercado')}: drift={x.get('drift_pct')}% severidad={x.get('severidad')} n7={x.get('n_7d')} n30={x.get('n_prev_30d')}")
if not d.get('items'):
    lines.append('- Sin datos suficientes para drift.')

lines.append('')
lines.append('## Alertas de ingestión')
lines.append(f"- resumen: {a.get('resumen')}")
for it in a.get('alertas',[])[:10]:
    lines.append(f"- {it.get('fuente')}: stale={it.get('stale')} sev={it.get('severidad')} horas={it.get('horas_sin_actualizar')}")

lines.append('')
lines.append('## Sugerencias de umbrales')
for s in u.get('sugerencias',[])[:8]:
    lines.append(
      f"- {s.get('deporte')}: warning={s.get('warning_brier_sugerido')} bloqueo={s.get('bloqueo_brier_sugerido')} muestra={s.get('muestra_base')}"
    )

lines.append('')
lines.append('## Acciones priorizadas')
for ac in r.get('acciones',[])[:12]:
    lines.append(f"- [{ac.get('prioridad')}/{ac.get('semaforo')}] {ac.get('accion')} — {ac.get('motivo')}")

out=p/'REPORTE_SEMANAL_AUTO.md'
out.write_text('\n'.join(lines), encoding='utf-8')
print(out)
PY

echo "[semanal-auto] generado en $OUT_DIR"