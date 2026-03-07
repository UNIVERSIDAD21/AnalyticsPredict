-- 11_validaciones_minimas_bloque_06_completo.sql
-- Validaciones mínimas reproducibles del bloque 06 completo.

-- A) Capa base
SELECT source, COUNT(*) AS n
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY source
ORDER BY source;

SELECT sport, COUNT(*) AS n
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY sport
ORDER BY sport;

-- B) Performance / Policy
SELECT sport, market_type, odds_bucket, source,
       SUM(n)::bigint AS n,
       ROUND(AVG(win_rate)::numeric,6) AS win_rate,
       ROUND(AVG(roi_pct_monetario)::numeric,6) AS roi_pct_monetario,
       ROUND(AVG(roi_unit_pct)::numeric,6) AS roi_unit_pct
FROM analytics.vw_perf_market_odds_confidence
GROUP BY sport, market_type, odds_bucket, source
ORDER BY sport, market_type, odds_bucket, source
LIMIT 120;

SELECT status_policy, COUNT(*) AS n_rows, SUM(n)::bigint AS n_eventos
FROM analytics.vw_policy_odds_compliance
GROUP BY status_policy
ORDER BY status_policy;

-- C) Calibration / Risk
SELECT sport, market_type,
       SUM(n)::bigint AS n_eventos,
       ROUND(AVG(calibration_gap)::numeric,6) AS calibration_gap_prom,
       MIN(source_quality_flag) AS source_quality_flag
FROM analytics.vw_calibration_scorecard
GROUP BY sport, market_type
ORDER BY sport, market_type;

SELECT sport, market_type,
       SUM(n)::bigint AS n_eventos,
       SUM(violaciones_policy)::bigint AS violaciones_policy,
       ROUND(AVG(average_stake)::numeric,6) AS avg_stake,
       ROUND(AVG(kelly_usage)::numeric,6) AS avg_kelly
FROM analytics.vw_stake_and_risk_consistency
GROUP BY sport, market_type
ORDER BY sport, market_type;

-- D) Data Quality Core
SELECT source_table, periodo,
       completeness_rate,
       freshness_lag_horas,
       outlier_rate,
       source_coverage,
       source_quality_flag,
       residual_warning
FROM analytics.vw_data_quality_core
ORDER BY periodo DESC, source_table
LIMIT 200;

-- E) Madurez operativa
SELECT sport, periodo,
       n,
       win_rate,
       roi_pct_monetario,
       roi_unit_pct,
       calibration_score,
       quality_score,
       policy_compliance,
       source_quality_flag,
       residual_warning
FROM analytics.vw_nba_vs_futbol_madurez_operativa
ORDER BY periodo DESC, sport;
