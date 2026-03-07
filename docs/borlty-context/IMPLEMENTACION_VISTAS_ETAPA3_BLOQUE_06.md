# IMPLEMENTACION_VISTAS_ETAPA3_BLOQUE_06.md

## Alcance
Implementación física de vistas prioritarias del bloque 06:
1. `analytics.vw_perf_market_odds_confidence`
2. `analytics.vw_policy_odds_compliance`

Reutilizando la capa base:
- `analytics.vw_base_metricas_unificadas_v1`

## Archivos SQL
- `backend/scripts/sql/analitica_bloque_06/03_vw_perf_market_odds_confidence.sql`
- `backend/scripts/sql/analitica_bloque_06/04_vw_policy_odds_compliance.sql`
- `backend/scripts/sql/analitica_bloque_06/05_validaciones_vistas_perf_policy.sql`

## Ejecución reproducible
- Script: `backend/scripts/ejecutar_vistas_bloque_06_etapa3.py`
- Evidencia: `reports/auditoria_baselines/vistas_bloque_06_etapa3_validaciones_20260307T0212Z.json`

## Notas de deuda residual explícitas
- `source_quality_flag` y `residual_warning` se propagan desde capa base.
- Confidence sigue en política temporal (bloque 05 P1).
- Policy de odds sigue temporal-operativa (bloque 05 P2).
- Drift residual fútbol sigue explícito por flags (bloque 05 P4).

## Hallazgo de cobertura en esta corrida
En el corte actual de validación, las vistas quedaron pobladas con fuentes NBA.
No aparecieron filas de fútbol porque no se detectaron registros resueltos bajo los filtros activos de esta corrida.
Esto se documenta como hecho de datos del corte actual, no como ausencia de soporte estructural.
