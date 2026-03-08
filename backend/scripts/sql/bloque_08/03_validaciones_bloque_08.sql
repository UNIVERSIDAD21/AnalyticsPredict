-- 03_validaciones_bloque_08.sql
-- Validaciones estructurales bloque 08 (PostgreSQL 14+)
-- Ejecutable incluso con BD sin datos.

-- CHECK 1: tabla dq_rule_results existe
SELECT
  'check_01_dq_rule_results_existe' AS check_name,
  CASE WHEN to_regclass('analytics.dq_rule_results') IS NOT NULL THEN 'PASS' ELSE 'FAIL' END AS status;

-- CHECK 2: estructura mínima de dq_rule_results
SELECT
  'check_02_dq_rule_results_columnas_minimas' AS check_name,
  CASE WHEN COUNT(*) >= 8 THEN 'PASS' ELSE 'FAIL' END AS status,
  COUNT(*) AS columnas_detectadas
FROM information_schema.columns
WHERE table_schema = 'analytics'
  AND table_name = 'dq_rule_results'
  AND column_name IN (
    'periodo','domain','rule_id','category','severity','failed_rows','total_rows','fail_rate'
  );

-- CHECK 3: tabla dq_alerts existe
SELECT
  'check_03_dq_alerts_existe' AS check_name,
  CASE WHEN to_regclass('analytics.dq_alerts') IS NOT NULL THEN 'PASS' ELSE 'FAIL' END AS status;

-- CHECK 4: vistas bloque 06 accesibles
WITH vistas AS (
  SELECT unnest(ARRAY[
    'vw_base_metricas_unificadas_v1',
    'vw_perf_market_odds_confidence',
    'vw_policy_odds_compliance',
    'vw_calibration_scorecard',
    'vw_stake_and_risk_consistency',
    'vw_data_quality_core',
    'vw_nba_vs_futbol_madurez_operativa'
  ]) AS vista
)
SELECT
  'check_04_vistas_bloque_06_disponibles' AS check_name,
  CASE WHEN COUNT(*) = 7 THEN 'PASS' ELSE 'FAIL' END AS status,
  COUNT(*) AS vistas_detectadas
FROM vistas v
JOIN information_schema.views iv
  ON iv.table_schema = 'analytics'
 AND iv.table_name = v.vista;

-- CHECK 5: scorecards últimas 24h (informativo si no hay datos)
SELECT
  'check_05_scorecard_24h_nba' AS check_name,
  CASE WHEN COUNT(*) >= 1 THEN 'PASS' ELSE 'WARN_NO_DATA' END AS status,
  COUNT(*) AS filas
FROM analytics.dq_scorecard_daily
WHERE domain = 'NBA'
  AND calculated_at >= NOW() - INTERVAL '24 hours';

SELECT
  'check_06_scorecard_24h_futbol' AS check_name,
  CASE WHEN COUNT(*) >= 1 THEN 'PASS' ELSE 'WARN_NO_DATA' END AS status,
  COUNT(*) AS filas
FROM analytics.dq_scorecard_daily
WHERE domain = 'FUTBOL'
  AND calculated_at >= NOW() - INTERVAL '24 hours';
