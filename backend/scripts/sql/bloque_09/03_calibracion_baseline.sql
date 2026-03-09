-- 03_calibracion_baseline.sql
-- Baseline de calibración por mercado (COMPLETO, Q1-Q4)
-- Fuente: analytics.vw_calibration_scorecard

WITH base AS (
  SELECT
    market_type,
    confidence_bucket,
    SUM(n)::bigint AS n,
    AVG(hit_rate)::numeric AS hit_rate,
    AVG(prob_media)::numeric AS prob_media,
    AVG(brier_score)::numeric AS brier,
    AVG(log_loss)::numeric AS logloss,
    AVG(calibration_gap)::numeric AS calibration_gap
  FROM analytics.vw_calibration_scorecard
  WHERE market_type IN ('COMPLETO','Q1','Q2','Q3','Q4')
  GROUP BY market_type, confidence_bucket
),
totals AS (
  SELECT market_type, SUM(n)::numeric AS n_total
  FROM base
  GROUP BY market_type
),
agg AS (
  SELECT
    b.market_type,
    t.n_total::bigint AS n_total,
    AVG(b.brier)::numeric AS brier,
    AVG(b.logloss)::numeric AS logloss,
    AVG(b.calibration_gap)::numeric AS calibration_gap,
    SUM((b.n::numeric / NULLIF(t.n_total,0)) * ABS(b.hit_rate - b.prob_media))::numeric AS ece
  FROM base b
  JOIN totals t ON t.market_type = b.market_type
  GROUP BY b.market_type, t.n_total
)
SELECT
  market_type,
  n_total,
  ROUND(brier, 6) AS brier,
  ROUND(ece, 6) AS ece,
  ROUND(logloss, 6) AS logloss,
  ROUND(calibration_gap, 6) AS calibration_gap
FROM agg
ORDER BY ece DESC, n_total DESC;
