# 07 — Sunset legacy (A3 post-cierre)

## Objetivo
Ejecutar retiro de legado según umbral ADR con evidencia.

## Criterio de done
- Métrica legacy <5% por 7 días.
- Aviso emitido según política.
- Retiro de legacy aplicado y documentado.

## Entregables
- Reporte de adopción.
- Acta de retiro de legacy.

---

## Monitoreo operativo habilitado
Script diario:
```bash
BASE_URL="http://localhost:8000" ./scripts/a3_monitoreo_legacy.sh
```

Salida:
- `docs/reportes/A3_MONITOREO_LEGACY_<timestamp>.md`

## Regla de decisión
- Si hay 7 reportes consecutivos con `legacyRatePct < 5`, se habilita acta de retiro legacy.
