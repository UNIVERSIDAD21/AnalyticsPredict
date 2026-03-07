-- 02_validaciones_base_unificada_v1.sql
-- Validaciones mínimas reproducibles para analytics.vw_base_metricas_unificadas_v1

-- 1) Conteos por source
SELECT source, COUNT(*) AS n
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY source
ORDER BY source;

-- 2) Cobertura por sport
SELECT sport, COUNT(*) AS n
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY sport
ORDER BY sport;

-- 3) Ejemplo segmentación por odds_bucket
SELECT sport, market_type, odds_bucket,
       COUNT(*) AS n,
       ROUND(AVG(CASE WHEN win_count=1 THEN 1.0 ELSE 0.0 END)::numeric,4) AS hit_rate
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY sport, market_type, odds_bucket
ORDER BY sport, market_type, odds_bucket
LIMIT 120;

-- 4) Ejemplo segmentación por confidence_bucket
SELECT sport, market_type, confidence_bucket,
       COUNT(*) AS n,
       ROUND(AVG(CASE WHEN win_count=1 THEN 1.0 ELSE 0.0 END)::numeric,4) AS hit_rate
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY sport, market_type, confidence_bucket
ORDER BY sport, market_type, confidence_bucket
LIMIT 120;

-- 5) Confirmación de separación ROI monetario vs unitario
SELECT
  source,
  COUNT(*) AS n,
  COUNT(*) FILTER (WHERE roi_pct_monetario IS NOT NULL) AS n_roi_monetario,
  COUNT(*) FILTER (WHERE roi_unit_pct IS NOT NULL) AS n_roi_unitario,
  COUNT(*) FILTER (WHERE roi_pct_monetario IS NOT NULL AND roi_unit_pct IS NOT NULL) AS n_conflicto_ambos_no_nulos
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY source
ORDER BY source;

-- 6) Cobertura de flags de calidad residual
SELECT source_quality_flag, residual_warning, COUNT(*) AS n
FROM analytics.vw_base_metricas_unificadas_v1
GROUP BY source_quality_flag, residual_warning
ORDER BY source_quality_flag, residual_warning;
