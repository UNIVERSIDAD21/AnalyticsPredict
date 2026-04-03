# BLOQUE 19.7 — Runbook de automatización diaria (corners prioritarios)

## Entrypoint único
```bash
./.venv/bin/python backend/scripts/automation_diaria_corners_b19_7.py
```

## Cron sugerido (UTC, diario 06:10)
```cron
10 6 * * * cd /ruta/AnalyticsPredict && ./.venv/bin/python backend/scripts/automation_diaria_corners_b19_7.py >> logs/b19_7_automation.log 2>&1
```

## Regla crítica
- Este job **NO** ejecuta B20 automáticamente.
- Solo consolida señales y registra si el gate B20 quedó habilitado.

## Artefactos
- `docs/reportes/BLOQUE_19_7_AUTOMATION_DIARIA_CORNERS.json`
- `docs/reportes/BLOQUE_19_7_AUTOMATION_DIARIA_CORNERS.md`
- `docs/reportes/BLOQUE_19_7_AUTOMATION_STATE.json`
