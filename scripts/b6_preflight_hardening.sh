#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-deploy/staging/staging.env}"
OUT_DIR="docs/reportes"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT_FILE="${OUT_DIR}/B6_PREFLIGHT_${TS}.md"

mkdir -p "$OUT_DIR"

required_vars=(
  DATABASE_URL
  AUTH_SECRET_KEY
  MP_ACCESS_TOKEN
  MP_WEBHOOK_SECRET
)

echo "# B6 Preflight Hardening" > "$OUT_FILE"
echo "" >> "$OUT_FILE"
echo "Fecha UTC: ${TS}" >> "$OUT_FILE"
echo "Env file: ${ENV_FILE}" >> "$OUT_FILE"
echo "" >> "$OUT_FILE"
echo "## Verificación de secretos mínimos" >> "$OUT_FILE"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "- ❌ No existe ${ENV_FILE}" >> "$OUT_FILE"
  echo "Reporte: $OUT_FILE"
  exit 1
fi

missing=0
for v in "${required_vars[@]}"; do
  if grep -qE "^${v}=.+" "$ENV_FILE"; then
    echo "- ✅ ${v} presente" >> "$OUT_FILE"
  else
    echo "- ❌ ${v} faltante o vacío" >> "$OUT_FILE"
    missing=$((missing+1))
  fi
done

echo "" >> "$OUT_FILE"
echo "## Verificación de artefactos operativos" >> "$OUT_FILE"

checks=(
  "deploy/staging/docker-compose.yml"
  "deploy/staging/cron-notificaciones.example"
  "scripts/a1_smoke_staging.sh"
  "scripts/b3_ciclo_semanal.sh"
  "scripts/b4_ciclo_24h_reporte.sh"
)

for p in "${checks[@]}"; do
  if [[ -f "$p" ]]; then
    echo "- ✅ ${p}" >> "$OUT_FILE"
  else
    echo "- ❌ ${p} (faltante)" >> "$OUT_FILE"
    missing=$((missing+1))
  fi
done

echo "" >> "$OUT_FILE"
if [[ "$missing" -eq 0 ]]; then
  echo "## Veredicto" >> "$OUT_FILE"
  echo "- ✅ Preflight B6 en verde (mínimos de hardening presentes)." >> "$OUT_FILE"
else
  echo "## Veredicto" >> "$OUT_FILE"
  echo "- ⚠️ Preflight B6 incompleto (${missing} hallazgos)." >> "$OUT_FILE"
fi

echo "Reporte generado: $OUT_FILE"
