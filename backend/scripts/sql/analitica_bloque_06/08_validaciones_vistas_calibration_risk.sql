-- 08_validaciones_vistas_calibration_risk.sql
-- Validaciones mínimas reproducibles para etapa 4 (calibration + stake/risk)

-- 1) Validación por market_type (calibration)
SELECT sport, market_type, COUNT(*) AS n_rows,
       SUM(n)::bigint AS n_eventos,
       ROUND(AVG(calibration_gap)::numeric, 6) AS calibration_gap_prom
FROM analytics.vw_calibration_scorecard
GROUP BY sport, market_type
ORDER BY sport, market_type;

-- 2) Validación por confidence_bucket (calibration)
SELECT sport, confidence_bucket, COUNT(*) AS n_rows,
       SUM(n)::bigint AS n_eventos,
       ROUND(AVG(hit_rate)::numeric, 6) AS hit_rate_prom,
       ROUND(AVG(prob_media)::numeric, 6) AS prob_media_prom
FROM analytics.vw_calibration_scorecard
GROUP BY sport, confidence_bucket
ORDER BY sport, confidence_bucket;

-- 3) Validación: calibration_gap marcado como sensible a deuda residual
SELECT source_quality_flag, residual_warning, COUNT(*) AS n_rows
FROM analytics.vw_calibration_scorecard
WHERE calibration_gap IS NOT NULL
GROUP BY source_quality_flag, residual_warning
ORDER BY source_quality_flag, residual_warning;

-- 4) Consistencia stake/risk y policy (cuando aplica)
SELECT sport, market_type,
       SUM(n)::bigint AS n_eventos,
       SUM(violaciones_policy)::bigint AS violaciones_policy,
       ROUND(AVG(average_stake)::numeric, 6) AS avg_stake,
       ROUND(AVG(stake_dispersion)::numeric, 6) AS avg_stake_dispersion
FROM analytics.vw_stake_and_risk_consistency
GROUP BY sport, market_type
ORDER BY sport, market_type;

-- 5) Cobertura por source inferida en stake/risk (a través de quality/warnings)
SELECT source_quality_flag, residual_warning, COUNT(*) AS n_rows
FROM analytics.vw_stake_and_risk_consistency
GROUP BY source_quality_flag, residual_warning
ORDER BY source_quality_flag, residual_warning;
