-- 06_vw_calibration_scorecard.sql
-- Bloque 06 - Etapa 4
-- Vista canónica de calibración (observabilidad, no corrección del bug).

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_calibration_scorecard AS
WITH nba AS (
  SELECT
    'NBA'::text AS sport,
    UPPER(COALESCE(pr.mercado::text, 'SIN_MERCADO'))::text AS market_type,
    COALESCE(pr.modelo_version_id::text, 'SIN_MODELO')::text AS model_version,
    COALESCE(pr.fecha_partido::date, pr.timestamp_generacion::date) AS periodo,
    CASE
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) IS NULL THEN 'SIN_CONFIANZA'
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) >= 0.80 THEN '0.80+'
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) >= 0.70 THEN '0.70-0.79'
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) >= 0.60 THEN '0.60-0.69'
      ELSE '<0.60'
    END::text AS confidence_bucket,
    CASE WHEN pr.outcome_binario IS TRUE THEN 1.0 ELSE 0.0 END::numeric AS y,
    COALESCE(pr.p_calibrada, pr.p_raw)::numeric AS p,
    'B'::text AS source_quality_flag,
    'confidence_temporal_policy_activa'::text AS residual_warning
  FROM predicciones_registradas pr
  WHERE pr.outcome_binario IS NOT NULL
    AND COALESCE(pr.p_calibrada, pr.p_raw) IS NOT NULL
),
fut AS (
  SELECT
    'FUTBOL'::text AS sport,
    UPPER(COALESCE(pf.mercado::text, 'SIN_MERCADO'))::text AS market_type,
    COALESCE(pf.modelo_version_id::text, 'SIN_MODELO')::text AS model_version,
    COALESCE(pf.fecha_partido::date, pf.timestamp_generacion::date) AS periodo,
    CASE
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) IS NULL THEN 'SIN_CONFIANZA'
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) >= 0.80 THEN '0.80+'
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) >= 0.70 THEN '0.70-0.79'
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) >= 0.60 THEN '0.60-0.69'
      ELSE '<0.60'
    END::text AS confidence_bucket,
    CASE WHEN pf.outcome_binario IS TRUE THEN 1.0 ELSE 0.0 END::numeric AS y,
    COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under)::numeric AS p,
    'C'::text AS source_quality_flag,
    'drift_futbol_residual;confidence_temporal_policy_activa'::text AS residual_warning
  FROM predicciones_futbol pf
  WHERE pf.outcome_binario IS NOT NULL
    AND COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) IS NOT NULL
),
base AS (
  SELECT * FROM nba
  UNION ALL
  SELECT * FROM fut
)
SELECT
  sport,
  market_type,
  model_version,
  periodo,
  confidence_bucket,
  COUNT(*)::bigint AS n,
  ROUND(AVG(y)::numeric, 6) AS hit_rate,
  ROUND(AVG(p)::numeric, 6) AS prob_media,
  ROUND(AVG(POWER(p - y, 2))::numeric, 6) AS brier_score,
  ROUND(AVG(-((y * LN(GREATEST(LEAST(p, 0.999999), 0.000001))) + ((1 - y) * LN(GREATEST(LEAST(1 - p, 0.999999), 0.000001)))))::numeric, 6) AS log_loss,
  ROUND((AVG(p) - AVG(y))::numeric, 6) AS calibration_gap,
  MIN(source_quality_flag)::text AS source_quality_flag,
  STRING_AGG(DISTINCT residual_warning, ';' ORDER BY residual_warning)
    FILTER (WHERE residual_warning IS NOT NULL AND residual_warning <> '') AS residual_warning
FROM base
GROUP BY sport, market_type, model_version, periodo, confidence_bucket;
