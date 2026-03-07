-- 04_vw_policy_odds_compliance.sql
-- Bloque 06 - Etapa 3
-- Vista de cumplimiento de policy temporal de odds por mercado/bucket/periodo.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_policy_odds_compliance AS
WITH policy_rules AS (
  -- Policy temporal vigente bloque 05 (documental) aterrizada en SQL.
  SELECT * FROM (
    VALUES
      ('COMPLETO','<1.6','PERMITIDO'),
      ('COMPLETO','1.6-1.8','RESTRINGIDO'),
      ('COMPLETO','1.8-2.0','PERMITIDO'),
      ('COMPLETO','>=2.0','BLOQUEADO'),
      ('Q1','<1.6','RESTRINGIDO'),
      ('Q1','1.6-1.8','PERMITIDO'),
      ('Q1','1.8-2.0','PERMITIDO'),
      ('Q1','>=2.0','PERMITIDO_CON_CAUTELA'),
      ('Q2','<1.6','MUESTRA_INSUFICIENTE'),
      ('Q2','1.6-1.8','PERMITIDO_CON_CAUTELA'),
      ('Q2','1.8-2.0','PERMITIDO'),
      ('Q2','>=2.0','PERMITIDO_CON_CAUTELA'),
      ('Q3','<1.6','RESTRINGIDO'),
      ('Q3','1.6-1.8','RESTRINGIDO'),
      ('Q3','1.8-2.0','RESTRINGIDO'),
      ('Q3','>=2.0','MUESTRA_INSUFICIENTE'),
      ('Q4','<1.6','RESTRINGIDO'),
      ('Q4','1.6-1.8','RESTRINGIDO'),
      ('Q4','1.8-2.0','RESTRINGIDO'),
      ('Q4','>=2.0','MUESTRA_INSUFICIENTE')
  ) AS t(market_type, odds_bucket, status_policy)
),
agg AS (
  SELECT
    p.market_type,
    p.odds_bucket,
    p.periodo,
    p.source,
    SUM(p.n)::bigint AS n,
    ROUND(AVG(p.roi_pct_monetario)::numeric, 6) AS roi_pct_monetario,
    ROUND(AVG(p.roi_unit_pct)::numeric, 6) AS roi_unit_pct,
    MIN(p.source_quality_flag)::text AS source_quality_flag,
    STRING_AGG(DISTINCT p.residual_warning, ';' ORDER BY p.residual_warning)
      FILTER (WHERE p.residual_warning IS NOT NULL AND p.residual_warning <> '') AS residual_warning
  FROM analytics.vw_perf_market_odds_confidence p
  GROUP BY p.market_type, p.odds_bucket, p.periodo, p.source
)
SELECT
  a.market_type,
  a.odds_bucket,
  a.periodo,
  a.source,
  a.n,
  a.roi_pct_monetario,
  a.roi_unit_pct,
  COALESCE(r.status_policy, 'SIN_POLICY')::text AS status_policy,
  CASE
    WHEN COALESCE(r.status_policy, 'SIN_POLICY') = 'BLOQUEADO' AND a.n > 0 THEN a.n
    ELSE 0
  END::bigint AS brechas,
  CASE
    WHEN COALESCE(r.status_policy, 'SIN_POLICY') = 'BLOQUEADO' AND a.n > 0 THEN TRUE
    ELSE FALSE
  END AS tiene_violacion,
  a.source_quality_flag,
  a.residual_warning
FROM agg a
LEFT JOIN policy_rules r
  ON r.market_type = a.market_type
 AND r.odds_bucket = a.odds_bucket;
