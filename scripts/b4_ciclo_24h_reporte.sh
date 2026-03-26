#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_DIR="docs/reportes"
OUT_FILE="${OUT_DIR}/B4_CICLO_24H_${TS}.md"
TMP_MET="/tmp/b4_metricas_${TS}.json"
TMP_HIS="/tmp/b4_historial_${TS}.json"

mkdir -p "$OUT_DIR"

HDR=()
if [[ -n "$AUTH_TOKEN" ]]; then
  HDR=(-H "Authorization: Bearer ${AUTH_TOKEN}")
fi

code_m=$(curl -sS "${HDR[@]}" -o "$TMP_MET" -w "%{http_code}" "${BASE_URL}/api/notificaciones/metricas-entrega?horas=24" || true)
code_h=$(curl -sS "${HDR[@]}" -o "$TMP_HIS" -w "%{http_code}" "${BASE_URL}/api/notificaciones/historial?limit=200" || true)

if [[ "$code_m" != "200" || "$code_h" != "200" ]]; then
  echo "Error obteniendo datos B4 (metricas:$code_m historial:$code_h)"
  exit 1
fi

cat > "$OUT_FILE" <<EOF
# B4 — Reporte ciclo 24h

Fecha UTC: ${TS}
Base URL: ${BASE_URL}

## Fuentes
- /api/notificaciones/metricas-entrega?horas=24
- /api/notificaciones/historial?limit=200

## Métricas 24h
\`\`\`json
$(cat "$TMP_MET")
\`\`\`

## Historial (muestra)
\`\`\`json
$(cat "$TMP_HIS")
\`\`\`

## Checklist de cierre B4
- [ ] Cumplimiento SLO definido en reporte oficial B4.
- [ ] Sin backlog crítico de cola.
- [ ] Reintentos dentro de umbral esperado.
- [ ] Evidencia anexada a estado/changelog.
EOF

echo "Reporte generado: $OUT_FILE"
