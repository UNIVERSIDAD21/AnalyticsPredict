# BASE_FISICA_BLOQUE_06_V1.md

## Qué se implementó
Se creó la capa base física compartida del bloque 06:
- `analytics.vw_base_metricas_unificadas_v1`

Objetivo:
- unificar dimensiones y métricas base reutilizables,
- separar ROI monetario vs ROI unitario,
- propagar flags de calidad/residualidad del bloque 05.

## Ruta de implementación
- SQL de creación:
  - `backend/scripts/sql/analitica_bloque_06/01_base_unificada_v1.sql`
- Validaciones reproducibles:
  - `backend/scripts/sql/analitica_bloque_06/02_validaciones_base_unificada_v1.sql`
- Ejecutor reproducible:
  - `backend/scripts/ejecutar_base_bloque_06_v1.py`
- Evidencia de ejecución:
  - `reports/auditoria_baselines/base_bloque_06_v1_validaciones_20260307T0200Z.json`

## Columnas canónicas expuestas
- `event_id`
- `sport`
- `source`
- `market_type`
- `periodo`
- `odds_value`
- `odds_bucket`
- `confidence_prob`
- `confidence_bucket`
- `n`
- `win_count`
- `loss_count`
- `push_count`
- `roi_pct_monetario`
- `roi_unit_pct`
- `edge_medio_base`
- `source_quality_flag`
- `residual_warning`

## Reglas clave respetadas
1. ROI monetario y unitario separados en columnas distintas.
2. `source_quality_flag` obligatorio.
3. `residual_warning` explícito para deuda residual (confidence temporal y drift fútbol).
4. No implementación de vistas finales del bloque 06 en esta etapa.

## Hallazgo real de datos en esta ejecución
En el corte actual de datos, la base unificada pobló fuentes NBA (`apuestas`, `predicciones_registradas`).
No aparecieron filas de fuentes fútbol en las validaciones porque no hay registros resueltos detectables con los filtros actuales (`resultado` en apuestas_futbol / `outcome_binario` en predicciones_futbol).

Esto queda documentado como hecho de datos, no como ausencia de soporte en la vista.
