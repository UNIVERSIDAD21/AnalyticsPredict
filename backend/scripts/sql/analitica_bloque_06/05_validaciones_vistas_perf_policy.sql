-- 05_validaciones_vistas_perf_policy.sql
-- Validaciones mínimas reproducibles para vistas etapa 3 (performance + policy).

-- 1) Comparación de conteos base vs vista perf (por source)
SELECT
  b.source,
  COUNT(*) AS n_base_rows,
  COALESCE(p.n_perf_rows, 0) AS n_perf_rows
FROM analytics.vw_base_metricas_unificadas_v1 b
LEFT JOIN (
  SELECT source, SUM(n)::bigint AS n_perf_rows
  FROM analytics.vw_perf_market_odds_confidence
  GROUP BY source
) p USING (source)
GROUP BY b.source, p.n_perf_rows
ORDER BY b.source;

-- 2) Ejemplo de bucket >=2.0 en performance
SELECT
  sport,
  market_type,
  odds_bucket,
  source,
  SUM(n)::bigint AS n,
  ROUND(AVG(win_rate)::numeric,6) AS win_rate,
  ROUND(AVG(roi_pct_monetario)::numeric,6) AS roi_pct_monetario,
  ROUND(AVG(roi_unit_pct)::numeric,6) AS roi_unit_pct,
  MIN(source_quality_flag) AS source_quality_flag
FROM analytics.vw_perf_market_odds_confidence
WHERE odds_bucket = '>=2.0'
GROUP BY sport, market_type, odds_bucket, source
ORDER BY sport, market_type, source;

-- 3) Separación ROI monetario vs ROI unitario en performance
SELECT
  source,
  COUNT(*) AS n,
  COUNT(*) FILTER (WHERE roi_pct_monetario IS NOT NULL) AS n_roi_monetario,
  COUNT(*) FILTER (WHERE roi_unit_pct IS NOT NULL) AS n_roi_unitario,
  COUNT(*) FILTER (WHERE roi_pct_monetario IS NOT NULL AND roi_unit_pct IS NOT NULL) AS n_conflicto
FROM analytics.vw_perf_market_odds_confidence
GROUP BY source
ORDER BY source;

-- 4) Verificación de flags residuales en performance
SELECT source_quality_flag, residual_warning, COUNT(*) AS n
FROM analytics.vw_perf_market_odds_confidence
GROUP BY source_quality_flag, residual_warning
ORDER BY source_quality_flag, residual_warning;

-- 5) Verificación policy: buckets bloqueados con violación
SELECT
  market_type,
  odds_bucket,
  periodo,
  source,
  n,
  status_policy,
  brechas,
  tiene_violacion,
  source_quality_flag,
  residual_warning
FROM analytics.vw_policy_odds_compliance
WHERE status_policy = 'BLOQUEADO'
ORDER BY periodo DESC, source;

-- 6) Resumen policy por status
SELECT status_policy, COUNT(*) AS n_rows, SUM(n)::bigint AS n_events
FROM analytics.vw_policy_odds_compliance
GROUP BY status_policy
ORDER BY status_policy;
