-- 10_vw_nba_vs_futbol_madurez_operativa.sql
-- Bloque 06 - Etapa final
-- Vista comparativa de madurez operativa por deporte y periodo.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_nba_vs_futbol_madurez_operativa AS
WITH perf AS (
  SELECT
    p.sport,
    p.periodo,
    SUM(p.n)::bigint AS n,
    CASE
      WHEN SUM(p.n) = 0 THEN NULL
      ELSE ROUND(SUM((p.win_rate * p.n)::numeric) / SUM(p.n)::numeric, 6)
    END AS win_rate,
    ROUND(AVG(p.roi_pct_monetario)::numeric, 6) AS roi_pct_monetario,
    ROUND(AVG(p.roi_unit_pct)::numeric, 6) AS roi_unit_pct,
    MIN(p.source_quality_flag)::text AS source_quality_flag,
    STRING_AGG(DISTINCT p.residual_warning, ';' ORDER BY p.residual_warning)
      FILTER (WHERE p.residual_warning IS NOT NULL AND p.residual_warning <> '') AS residual_warning
  FROM analytics.vw_perf_market_odds_confidence p
  GROUP BY p.sport, p.periodo
),
calib AS (
  SELECT
    c.sport,
    c.periodo,
    -- score simple: mejor mientras menor brier/logloss y menor gap absoluto
    ROUND((1.0 - AVG(c.brier_score))::numeric, 6) AS brier_component,
    ROUND((1.0 - LEAST(AVG(c.log_loss), 1.0))::numeric, 6) AS logloss_component,
    ROUND((1.0 - LEAST(ABS(AVG(c.calibration_gap)), 1.0))::numeric, 6) AS gap_component,
    ROUND(((1.0 - AVG(c.brier_score)) + (1.0 - LEAST(AVG(c.log_loss), 1.0)) + (1.0 - LEAST(ABS(AVG(c.calibration_gap)), 1.0))) / 3.0, 6) AS calibration_score
  FROM analytics.vw_calibration_scorecard c
  GROUP BY c.sport, c.periodo
),
quality AS (
  SELECT
    CASE
      WHEN dq.source_table IN ('apuestas', 'predicciones_registradas') THEN 'NBA'
      WHEN dq.source_table IN ('apuestas_futbol', 'predicciones_futbol') THEN 'FUTBOL'
      ELSE 'OTRO'
    END AS sport,
    dq.periodo,
    ROUND(AVG((COALESCE(dq.completeness_rate, 0) + (1.0 - LEAST(COALESCE(dq.outlier_rate, 0), 1.0))) / 2.0)::numeric, 6) AS quality_score
  FROM analytics.vw_data_quality_core dq
  GROUP BY 1, dq.periodo
),
policy AS (
  SELECT
    p.sport,
    p.periodo,
    ROUND(AVG(
      CASE
        WHEN po.status_policy = 'BLOQUEADO' AND po.tiene_violacion THEN 0.0
        WHEN po.status_policy = 'RESTRINGIDO' AND po.tiene_violacion THEN 0.5
        ELSE 1.0
      END
    )::numeric, 6) AS policy_compliance
  FROM analytics.vw_perf_market_odds_confidence p
  LEFT JOIN analytics.vw_policy_odds_compliance po
    ON po.market_type = p.market_type
   AND po.odds_bucket = p.odds_bucket
   AND po.periodo = p.periodo
   AND po.source = p.source
  GROUP BY p.sport, p.periodo
)
SELECT
  perf.sport,
  perf.periodo,
  perf.n,
  perf.win_rate,
  perf.roi_pct_monetario,
  perf.roi_unit_pct,
  calib.calibration_score,
  quality.quality_score,
  policy.policy_compliance,
  perf.source_quality_flag,
  perf.residual_warning
FROM perf
LEFT JOIN calib
  ON calib.sport = perf.sport
 AND calib.periodo = perf.periodo
LEFT JOIN quality
  ON quality.sport = perf.sport
 AND quality.periodo = perf.periodo
LEFT JOIN policy
  ON policy.sport = perf.sport
 AND policy.periodo = perf.periodo;
