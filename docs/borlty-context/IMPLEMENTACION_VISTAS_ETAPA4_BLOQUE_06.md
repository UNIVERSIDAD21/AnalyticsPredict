# IMPLEMENTACION_VISTAS_ETAPA4_BLOQUE_06.md

## Alcance
Implementación física de vistas canónicas etapa 4 del bloque 06:
1. `analytics.vw_calibration_scorecard`
2. `analytics.vw_stake_and_risk_consistency`

Sin declarar resuelto el confidence bug y sin mezclar bloque 07.

## Archivos SQL
- `backend/scripts/sql/analitica_bloque_06/06_vw_calibration_scorecard.sql`
- `backend/scripts/sql/analitica_bloque_06/07_vw_stake_and_risk_consistency.sql`
- `backend/scripts/sql/analitica_bloque_06/08_validaciones_vistas_calibration_risk.sql`

## Ejecución reproducible
- Script: `backend/scripts/ejecutar_vistas_bloque_06_etapa4.py`
- Evidencia: `reports/auditoria_baselines/vistas_bloque_06_etapa4_validaciones_20260307T0220Z.json`

## Equivalencias técnicas documentadas
1. `model_version`:
   - se implementa desde `modelo_version_id` (cast a texto).
2. `confidence_bucket`:
   - se deriva de probabilidad disponible (`p_calibrada/p_raw` en NBA; `prob_over/prob_under` calibradas o raw en fútbol).
3. `violaciones_policy` en stake/risk:
   - se computa por unión con `vw_policy_odds_compliance` (status `BLOQUEADO/RESTRINGIDO`).

## Warnings residuales explícitos
- `source_quality_flag` y `residual_warning` quedan visibles en ambas vistas.
- Confidence sigue marcado como temporal (`confidence_temporal_policy_activa`).
- Drift fútbol se preserva como warning cuando aplique (`drift_futbol_residual`).

## Hallazgo de cobertura en esta corrida
En este corte, las validaciones quedaron pobladas principalmente con NBA.
No aparecieron filas de fútbol en los resultados de validación de esta ejecución por ausencia de registros resueltos detectables en los filtros activos.
Esto se documenta como hecho del dataset/corte actual, no como ausencia de soporte estructural en las vistas.
