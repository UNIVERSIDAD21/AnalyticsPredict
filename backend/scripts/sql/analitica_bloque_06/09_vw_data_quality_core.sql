-- 09_vw_data_quality_core.sql
-- Bloque 06 - Etapa final
-- Guardrail analítico mínimo de calidad de datos (no framework completo bloque 07).

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_data_quality_core AS
WITH base AS (
  SELECT
    b.source AS source_table,
    b.periodo,
    b.sport,
    COUNT(*)::numeric AS total_rows,
    SUM(CASE WHEN b.market_type IS NOT NULL AND b.market_type <> 'SIN_MERCADO' THEN 1 ELSE 0 END)::numeric AS ok_market,
    SUM(CASE WHEN b.odds_bucket IS NOT NULL AND b.odds_bucket <> 'SIN_ODDS' THEN 1 ELSE 0 END)::numeric AS ok_odds,
    SUM(CASE WHEN b.confidence_bucket IS NOT NULL AND b.confidence_bucket <> 'SIN_CONFIANZA' THEN 1 ELSE 0 END)::numeric AS ok_conf,
    MAX(b.periodo)::date AS max_periodo,
    MIN(b.source_quality_flag)::text AS source_quality_flag,
    STRING_AGG(DISTINCT b.residual_warning, ';' ORDER BY b.residual_warning)
      FILTER (WHERE b.residual_warning IS NOT NULL AND b.residual_warning <> '') AS residual_warning
  FROM analytics.vw_base_metricas_unificadas_v1 b
  GROUP BY b.source, b.periodo, b.sport
),
outliers AS (
  SELECT
    source AS source_table,
    periodo,
    AVG(
      CASE
        WHEN roi_pct_monetario IS NOT NULL AND ABS(roi_pct_monetario) > 500 THEN 1.0
        WHEN roi_unit_pct IS NOT NULL AND ABS(roi_unit_pct) > 500 THEN 1.0
        ELSE 0.0
      END
    )::numeric AS outlier_rate
  FROM analytics.vw_base_metricas_unificadas_v1
  GROUP BY source, periodo
),
coverage AS (
  SELECT
    source AS source_table,
    periodo,
    COUNT(*)::numeric AS coverage_n
  FROM analytics.vw_base_metricas_unificadas_v1
  GROUP BY source, periodo
)
SELECT
  b.source_table,
  b.periodo,
  ROUND(((b.ok_market + b.ok_odds + b.ok_conf) / NULLIF(3.0 * b.total_rows, 0))::numeric, 6) AS completeness_rate,
  ROUND(EXTRACT(EPOCH FROM (NOW()::timestamp - b.max_periodo::timestamp)) / 3600.0, 4) AS freshness_lag_horas,
  ROUND(COALESCE(o.outlier_rate, 0)::numeric, 6) AS outlier_rate,
  COALESCE(c.coverage_n, 0)::bigint AS source_coverage,
  b.source_quality_flag,
  b.residual_warning
FROM base b
LEFT JOIN outliers o
  ON o.source_table = b.source_table
 AND o.periodo = b.periodo
LEFT JOIN coverage c
  ON c.source_table = b.source_table
 AND c.periodo = b.periodo;
