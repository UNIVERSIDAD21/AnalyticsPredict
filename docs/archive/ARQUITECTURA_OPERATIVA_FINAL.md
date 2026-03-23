# Arquitectura Operativa Final (AnalyticsPredict)

## Flujo maestro

1. **Preflight técnico**
   - `make qa-preflight`
2. **Resolución + actualización de métricas**
   - `make calidad-ciclo`
3. **Decisión ejecutiva (GO/NO-GO)**
   - `make check-modo-estricto`
4. **Reporte diario**
   - `make reporte-ejecutivo`
5. **Cierre operativo**
   - `make cierre-operativo`

## Flujo semanal
1. `make reporte-semanal-auto`
2. `make revision-politica`
3. `make export-metricas-csv`

## Flujo de diagnóstico rápido
- `make estado-unificado`

## Reglas de operación
- Si NO-GO: no publicar recomendaciones automáticas.
- Si mercado en rojo: bloqueado por policy gate.
- Si ingestión crítica stale: priorizar pipeline de datos antes de recalibrar.

## Artefactos de evidencia
- `reports/calidad/*`
- `reports/ejecutivo/*`
- `reports/semanal_auto/*`
- `reports/cierre/*`
- `reports/csv/*`
- `reports/tendencias/health_snapshots.jsonl`
