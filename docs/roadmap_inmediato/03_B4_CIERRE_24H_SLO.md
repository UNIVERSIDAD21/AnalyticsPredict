# 03 — B4 cierre formal (24h SLO)

## Objetivo
Validar operación de notificaciones por 24h reales con cumplimiento SLO.

## Criterio de done
- 24h de datos operativos reales.
- Cumplimiento de SLO definido en B4.
- Estado B4 => CERRADO.

## Entregables
- Evidencia de cola, entregas, reintentos y latencias.
- Reporte de ciclo 24h.

---

## Runbook operativo

### Generar reporte de ciclo 24h
```bash
BASE_URL="http://localhost:8000" ./scripts/b4_ciclo_24h_reporte.sh
```

Salida:
- `docs/reportes/B4_CICLO_24H_<timestamp>.md`

### Criterio de aprobación
- El reporte debe demostrar cumplimiento de SLO.
- Si no cumple, abrir incidente y repetir ciclo.

## Evidencia mínima
1. Reporte B4 de 24h.
2. Veredicto cumplimiento/no cumplimiento.
3. Registro en estado/changelog.
