-- 03_vw_perf_market_odds_confidence.sql
-- Bloque 06 - Etapa 3
-- Vista canónica de performance por mercado/odds/confidence reutilizando capa base.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_perf_market_odds_confidence AS
SELECT
  b.sport,
  b.market_type,
  b.odds_bucket,
  b.confidence_bucket,
  b.periodo,
  b.source,
  SUM(b.n)::bigint AS n,
  CASE
    WHEN SUM(b.win_count + b.loss_count) = 0 THEN NULL
    ELSE ROUND(SUM(b.win_count)::numeric / SUM(b.win_count + b.loss_count)::numeric, 6)
  END AS win_rate,
  ROUND(AVG(b.roi_pct_monetario)::numeric, 6) AS roi_pct_monetario,
  ROUND(AVG(b.roi_unit_pct)::numeric, 6) AS roi_unit_pct,
  ROUND(AVG(b.edge_medio_base)::numeric, 6) AS edge_medio,
  MIN(b.source_quality_flag)::text AS source_quality_flag,
  STRING_AGG(DISTINCT b.residual_warning, ';' ORDER BY b.residual_warning)
    FILTER (WHERE b.residual_warning IS NOT NULL AND b.residual_warning <> '') AS residual_warning
FROM analytics.vw_base_metricas_unificadas_v1 b
GROUP BY
  b.sport,
  b.market_type,
  b.odds_bucket,
  b.confidence_bucket,
  b.periodo,
  b.source;
