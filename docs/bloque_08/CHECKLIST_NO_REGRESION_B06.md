# CHECKLIST_NO_REGRESION_B06

Objetivo: asegurar que el bloque 08 no rompe las vistas canónicas del bloque 06.

## Estado actual
- Fecha: 2026-03-08
- Responsable QA: pendiente
- Resultado global: PENDIENTE DE EJECUCIÓN EN ENTORNO CON DATOS

## Checks (1 por vista canónica)

| # | Vista canónica bloque 06 | Query de verificación | PASS/FAIL | Observaciones |
|---|---|---|---|---|
| 1 | `analytics.vw_base_metricas_unificadas_v1` | `SELECT COUNT(*) FROM analytics.vw_base_metricas_unificadas_v1;` | PENDIENTE | Debe responder sin error |
| 2 | `analytics.vw_perf_market_odds_confidence` | `SELECT COUNT(*) FROM analytics.vw_perf_market_odds_confidence;` | PENDIENTE | Debe responder sin error |
| 3 | `analytics.vw_policy_odds_compliance` | `SELECT COUNT(*) FROM analytics.vw_policy_odds_compliance;` | PENDIENTE | Debe responder sin error |
| 4 | `analytics.vw_calibration_scorecard` | `SELECT COUNT(*) FROM analytics.vw_calibration_scorecard;` | PENDIENTE | Debe responder sin error |
| 5 | `analytics.vw_stake_and_risk_consistency` | `SELECT COUNT(*) FROM analytics.vw_stake_and_risk_consistency;` | PENDIENTE | Debe responder sin error |
| 6 | `analytics.vw_data_quality_core` | `SELECT COUNT(*) FROM analytics.vw_data_quality_core;` | PENDIENTE | Base de scorecard B08 |
| 7 | `analytics.vw_nba_vs_futbol_madurez_operativa` | `SELECT COUNT(*) FROM analytics.vw_nba_vs_futbol_madurez_operativa;` | PENDIENTE | Comparativo dominio |

## Criterio de no-regresión

- PASS total solo si las 7 vistas responden sin error SQL.
- Si falla una vista, bloquear despliegue de bloque 08 hasta diagnóstico.
- Si el fallo viene de datos ausentes (no de SQL), registrar como `WARN_NO_DATA`.
