#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
USER_ID="${USER_ID:-}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="docs/reportes"
OUT_FILE="${OUT_DIR}/B3_CICLO_SEMANAL_${TS}.md"
TMP_JSON="/tmp/b3_estabilidad_${TS}.json"

mkdir -p "$OUT_DIR"

HDR=()
if [[ -n "$AUTH_TOKEN" ]]; then
  HDR+=(-H "Authorization: Bearer ${AUTH_TOKEN}")
fi
if [[ -n "$USER_ID" ]]; then
  HDR+=(-H "X-Usuario-Id: ${USER_ID}")
fi

code=$(curl -sS "${HDR[@]}" -o "$TMP_JSON" -w "%{http_code}" "${BASE_URL}/api/futbol/metricas/b3-estabilidad" || true)
if [[ "$code" != "200" ]]; then
  echo "Error: endpoint b3-estabilidad devolvió HTTP $code"
  cat "$TMP_JSON" || true
  exit 1
fi

read -r criticos ligas_evaluadas <<< "$(python3 - "$TMP_JSON" << 'PY'
import json,sys
p=sys.argv[1]
with open(p,'r',encoding='utf-8') as f:
    d=json.load(f)
ligas=d.get('ligas') or d.get('items') or []
crit=0
for l in ligas:
    estado=(l.get('estado') or '').upper()
    if 'CRIT' in estado:
        crit+=1
evals=d.get('ligas_evaluadas')
if evals is None:
    evals=len(ligas)
print(f"{crit} {evals}")
PY
)"

cat > "$OUT_FILE" <<EOF
# B3 — Ciclo semanal de estabilidad

Fecha UTC: ${TS}
Base URL: ${BASE_URL}

## Resultado
- Endpoint: "/api/futbol/metricas/b3-estabilidad" ✅
- Ligas en estado crítico: **${criticos}**

## Evidencia JSON

\`\`\`json
$(cat "$TMP_JSON")
\`\`\`

## Veredicto de ciclo
$(
if [[ "${ligas_evaluadas}" == "0" ]]; then
  echo '- ⚠️ Ciclo sin muestra evaluable (no computa para cierre formal B3).'
elif [[ "$criticos" == "0" ]]; then
  echo '- ✅ Ciclo apto (sin críticos).'
else
  echo '- ⚠️ Ciclo con críticos (no apto para cierre B3).'
fi
)
EOF

echo "Reporte generado: $OUT_FILE"
