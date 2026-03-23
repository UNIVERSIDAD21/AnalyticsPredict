# CHECKLIST_NO_REGRESION_B06

Objetivo: asegurar que el bloque 08 no rompe las vistas canónicas del bloque 06.

## Estado actual
- Fecha: 2026-03-09 00:53 UTC
- Responsable QA: Agente Borlty
- Resultado global: **PASS (7/7 vistas sin error SQL)**

## Checks (1 por vista canónica)

| # | Vista canónica bloque 06 | Query de verificación | Filas | MAX(periodo) | Estado | Observaciones |
|---|---|---|---:|---|---|---|
| 1 | `analytics.vw_base_metricas_unificadas_v1` | `SELECT COUNT(*), MAX(periodo) FROM analytics.vw_base_metricas_unificadas_v1;` | 2281 | 2026-02-12 | PASS | Estructura intacta |
| 2 | `analytics.vw_perf_market_odds_confidence` | `SELECT COUNT(*), MAX(periodo) FROM analytics.vw_perf_market_odds_confidence;` | 587 | 2026-02-12 | PASS | Estructura intacta |
| 3 | `analytics.vw_policy_odds_compliance` | `SELECT COUNT(*), MAX(periodo) FROM analytics.vw_policy_odds_compliance;` | 273 | 2026-02-12 | PASS | Estructura intacta |
| 4 | `analytics.vw_calibration_scorecard` | `SELECT COUNT(*), MAX(periodo) FROM analytics.vw_calibration_scorecard;` | 1912 | 2026-02-12 | PASS | Estructura intacta |
| 5 | `analytics.vw_stake_and_risk_consistency` | `SELECT COUNT(*), MAX(periodo) FROM analytics.vw_stake_and_risk_consistency;` | 70 | 2026-02-03 | PASS | Estructura intacta |
| 6 | `analytics.vw_data_quality_core` | `SELECT COUNT(*), MAX(periodo) FROM analytics.vw_data_quality_core;` | 52 | 2026-02-12 | PASS | Prerrequisito para scorecard B08 (hay datos) |
| 7 | `analytics.vw_nba_vs_futbol_madurez_operativa` | `SELECT COUNT(*), MAX(periodo) FROM analytics.vw_nba_vs_futbol_madurez_operativa;` | 32 | 2026-02-12 | PASS | Comparativo dominio operativo |

## Criterio de no-regresión

- PASS total solo si las 7 vistas responden sin error SQL.
- Si falla una vista, bloquear despliegue de bloque 08 hasta diagnóstico.
- Si el fallo viene de datos ausentes (no de SQL), registrar como `WARN_NO_DATA`.
