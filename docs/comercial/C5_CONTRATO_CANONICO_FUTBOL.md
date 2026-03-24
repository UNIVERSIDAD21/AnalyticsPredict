# C5 — Contrato canónico de fútbol

Fecha: 2026-03-24
Estado: CERRADO (operativo)

## Objetivo
Eliminar ambigüedad contractual entre frontend/backend en el módulo de fútbol y fijar endpoints oficiales para operación comercial controlada (beta).

## Contrato canónico definido

### Métricas principales
- `GET /api/futbol/metricas/calibracion`
- `GET /api/futbol/metricas/rendimiento`
- `GET /api/futbol/metricas/modelos`
- `GET /api/futbol/metricas/resumen`
- `GET /api/futbol/metricas/roi-temporal` ✅ (nuevo en C5, reemplaza serie simulada en frontend)

### Calidad y estabilidad
- `GET /api/futbol/metricas/b3-estabilidad`
- `GET /api/futbol/metricas/resumen-calidad-1x2`

## Decisiones canónicas
1. **Sin mocks productivos** para la serie temporal de ROI (dashboard consume backend real).
2. `roi-temporal` entrega serie de ROI acumulado por día para usuario autenticado.
3. Si no existe tabla/columnas requeridas, el endpoint retorna serie vacía (no datos simulados).
4. Cualquier endpoint legacy o alias no listado arriba se considera no canónico para operación comercial.

## Criterio de aceptación C5 (contrato)
- Dashboard de fútbol sin datos simulados para ROI temporal.
- Contrato explícito y estable para métricas y trazabilidad de fútbol.
