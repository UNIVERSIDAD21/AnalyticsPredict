#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-reports/policy_review/$(date -u +%F_%H%M%S)}"
mkdir -p "$OUT_DIR"

curl -sSf "$BASE_URL/api/metricas/politica-mercados?min_muestras=30" > "$OUT_DIR/politica_mercados.json"
curl -sSf "$BASE_URL/api/metricas/sugerencias-umbrales?min_muestras=30" > "$OUT_DIR/sugerencias_umbrales.json"

python3 - <<PY
import json, pathlib
p=pathlib.Path("$OUT_DIR")
pol=json.loads((p/'politica_mercados.json').read_text())
sug=json.loads((p/'sugerencias_umbrales.json').read_text())

rows=[]
rows.append('# Revisión de Política de Mercados')
rows.append('')
res=pol.get('resumen',{})
rows.append(f"- total={res.get('total')} verdes={res.get('verdes')} amarillos={res.get('amarillos')} rojos={res.get('rojos')} bloqueados={res.get('bloqueados')}")
rows.append('')
rows.append('## Umbrales sugeridos')
for s in sug.get('sugerencias',[]):
    rows.append(f"- {s.get('deporte')}: warning={s.get('warning_brier_sugerido')} bloqueo={s.get('bloqueo_brier_sugerido')} (muestra={s.get('muestra_base')})")
rows.append('')
rows.append('## Top mercados bloqueados')
bloq=[m for m in pol.get('mercados',[]) if m.get('bloqueado')]
for m in bloq[:20]:
    rows.append(f"- {m.get('deporte')}/{m.get('mercado')} brier={m.get('brier')} motivo={m.get('motivo')}")
if not bloq:
    rows.append('- Sin mercados bloqueados actualmente.')

out=p/'REVISION_POLITICA.md'
out.write_text('\n'.join(rows), encoding='utf-8')
print(out)
PY

echo "[policy] revisión generada en $OUT_DIR"