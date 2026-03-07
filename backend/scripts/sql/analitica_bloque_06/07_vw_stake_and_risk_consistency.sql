-- 07_vw_stake_and_risk_consistency.sql
-- Bloque 06 - Etapa 4
-- Vista canónica de consistencia stake/riesgo (observabilidad operativa).

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_stake_and_risk_consistency AS
WITH apuestas_base AS (
  SELECT
    b.sport,
    b.market_type,
    b.confidence_bucket,
    b.periodo,
    b.source,
    CASE WHEN b.source = 'apuestas' THEN a.stake::numeric ELSE af.stake::numeric END AS stake_value,
    CASE WHEN b.source = 'apuestas' THEN a.fraccion_kelly::numeric ELSE af.fraccion_kelly::numeric END AS kelly_usage,
    b.source_quality_flag,
    b.residual_warning,
    COALESCE(p.status_policy, 'SIN_POLICY')::text AS status_policy
  FROM analytics.vw_base_metricas_unificadas_v1 b
  LEFT JOIN apuestas a
    ON b.source = 'apuestas'
   AND b.event_id = ('nba_apuestas:' || a.id::text)
  LEFT JOIN apuestas_futbol af
    ON b.source = 'apuestas_futbol'
   AND b.event_id = ('fut_apuestas:' || af.id::text)
  LEFT JOIN analytics.vw_policy_odds_compliance p
    ON p.market_type = b.market_type
   AND p.odds_bucket = b.odds_bucket
   AND p.periodo = b.periodo
   AND p.source = b.source
  WHERE b.source IN ('apuestas', 'apuestas_futbol')
)
SELECT
  sport,
  market_type,
  confidence_bucket,
  periodo,
  COUNT(*)::bigint AS n,
  ROUND(AVG(stake_value)::numeric, 6) AS average_stake,
  ROUND(COALESCE(STDDEV_SAMP(stake_value), 0)::numeric, 6) AS stake_dispersion,
  ROUND(AVG(kelly_usage)::numeric, 6) AS kelly_usage,
  SUM(CASE WHEN status_policy IN ('BLOQUEADO', 'RESTRINGIDO') THEN 1 ELSE 0 END)::bigint AS violaciones_policy,
  MIN(source_quality_flag)::text AS source_quality_flag,
  STRING_AGG(DISTINCT (
      CASE
        WHEN source = 'apuestas_futbol' THEN COALESCE(residual_warning, '') || ';drift_futbol_residual'
        ELSE residual_warning
      END
    ), ';' ORDER BY (
      CASE
        WHEN source = 'apuestas_futbol' THEN COALESCE(residual_warning, '') || ';drift_futbol_residual'
        ELSE residual_warning
      END
    )) FILTER (WHERE residual_warning IS NOT NULL OR source = 'apuestas_futbol') AS residual_warning
FROM apuestas_base
GROUP BY sport, market_type, confidence_bucket, periodo;
