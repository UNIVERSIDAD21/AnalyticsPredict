#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="docs/reportes"
OUT_FILE="${OUT_DIR}/A3_MONITOREO_LEGACY_${TS}.md"
TMP_JSON="/tmp/a3_legacy_${TS}.json"

mkdir -p "$OUT_DIR"

HDR=()
if [[ -n "$AUTH_TOKEN" ]]; then
  HDR=(-H "Authorization: Bearer ${AUTH_TOKEN}")
fi

# Endpoint flexible: intenta kpis onboarding y luego health de adopción
CODE=$(curl -sS "${HDR[@]}" -o "$TMP_JSON" -w "%{http_code}" "${BASE_URL}/api/onboarding/kpis" || true)
if [[ "$CODE" != "200" ]]; then
  CODE=$(curl -sS "${HDR[@]}" -o "$TMP_JSON" -w "%{http_code}" "${BASE_URL}/api/onboarding/estado-adopcion" || true)
fi

if [[ "$CODE" != "200" ]]; then
  echo "No se pudo obtener métrica de adopción legacy (HTTP $CODE)"
  exit 1
fi

rate=$(python - << 'PY'
import json,sys
p=sys.argv[1]
with open(p,'r',encoding='utf-8') as f:
    d=json.load(f)
# intenta múltiples llaves posibles
candidates=[
    d.get('legacyRatePct'),
    d.get('legacy_rate_pct'),
    (d.get('kpis') or {}).get('legacyRatePct'),
    (d.get('kpis') or {}).get('legacy_rate_pct'),
]
val=None
for c in candidates:
    if c is not None:
        try:
            val=float(c)
            break
        except Exception:
            pass
if val is None:
    val=-1
print(val)
PY
"$TMP_JSON")

cat > "$OUT_FILE" <<EOF
# A3 — Monitoreo de adopción legacy

Fecha UTC: ${TS}
Base URL: ${BASE_URL}

## Resultado
- Legacy rate pct: ${rate}
- Umbral de retiro ADR: < 5% por 7 días consecutivos

## Evidencia JSON
\`\`\`json
$(cat "$TMP_JSON")
\`\`\`

## Veredicto
$(if python - << 'PY'
import sys
r=float(sys.argv[1])
print('OK' if r>=0 and r<5 else 'NO')
PY
"$rate" | grep -q OK; then
  echo "- ✅ Día apto para conteo de ventana de retiro (rate < 5%)."
else
  echo "- ⚠️ Día no apto para cierre de sunset (rate >= 5% o métrica no disponible)."
fi)
EOF

echo "Reporte generado: $OUT_FILE"
