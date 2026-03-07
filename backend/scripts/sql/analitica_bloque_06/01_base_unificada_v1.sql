-- 01_base_unificada_v1.sql
-- Bloque 06 - Etapa 2
-- Crea capa base física compartida para métricas analíticas sin duplicar lógica.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_base_metricas_unificadas_v1 AS
WITH nba_apuestas AS (
  SELECT
    'nba_apuestas:' || a.id::text AS event_id,
    'NBA'::text AS sport,
    'apuestas'::text AS source,
    UPPER(COALESCE(a.mercado::text, 'SIN_MERCADO'))::text AS market_type,
    COALESCE(a.fecha_partido::date, a.creado_en::date) AS periodo,
    a.cuota::numeric AS odds_value,
    CASE
      WHEN a.cuota IS NULL THEN 'SIN_ODDS'
      WHEN a.cuota < 1.6 THEN '<1.6'
      WHEN a.cuota < 1.8 THEN '1.6-1.8'
      WHEN a.cuota < 2.0 THEN '1.8-2.0'
      ELSE '>=2.0'
    END::text AS odds_bucket,
    a.probabilidad_sistema::numeric AS confidence_prob,
    CASE
      WHEN a.probabilidad_sistema IS NULL THEN 'SIN_CONFIANZA'
      WHEN a.probabilidad_sistema >= 0.80 THEN '0.80+'
      WHEN a.probabilidad_sistema >= 0.70 THEN '0.70-0.79'
      WHEN a.probabilidad_sistema >= 0.60 THEN '0.60-0.69'
      ELSE '<0.60'
    END::text AS confidence_bucket,
    1::int AS n,
    CASE WHEN UPPER(COALESCE(a.resultado::text, '')) = 'GANADA' THEN 1 ELSE 0 END::int AS win_count,
    CASE WHEN UPPER(COALESCE(a.resultado::text, '')) = 'PERDIDA' THEN 1 ELSE 0 END::int AS loss_count,
    CASE WHEN UPPER(COALESCE(a.resultado::text, '')) = 'PUSH' THEN 1 ELSE 0 END::int AS push_count,
    CASE
      WHEN a.stake IS NULL OR a.stake = 0 OR a.ganancia IS NULL THEN NULL
      ELSE (a.ganancia / a.stake) * 100.0
    END::numeric AS roi_pct_monetario,
    NULL::numeric AS roi_unit_pct,
    CASE
      WHEN a.valor_esperado IS NOT NULL THEN a.valor_esperado::numeric
      WHEN a.probabilidad_sistema IS NOT NULL AND a.cuota IS NOT NULL AND a.cuota > 0
        THEN (a.probabilidad_sistema - (1.0 / a.cuota))::numeric
      ELSE NULL
    END::numeric AS edge_medio_base,
    CASE
      WHEN a.probabilidad_sistema IS NOT NULL THEN 'B'
      ELSE 'A'
    END::text AS source_quality_flag,
    CASE
      WHEN a.probabilidad_sistema IS NOT NULL THEN 'confidence_temporal_policy_activa'
      ELSE NULL
    END::text AS residual_warning
  FROM apuestas a
  WHERE UPPER(COALESCE(a.resultado::text, '')) IN ('GANADA', 'PERDIDA', 'PUSH')
),
nba_pred AS (
  SELECT
    'nba_pred:' || pr.id::text AS event_id,
    'NBA'::text AS sport,
    'predicciones_registradas'::text AS source,
    UPPER(COALESCE(pr.mercado::text, 'SIN_MERCADO'))::text AS market_type,
    COALESCE(pr.fecha_partido::date, pr.timestamp_generacion::date) AS periodo,
    pr.cuota::numeric AS odds_value,
    CASE
      WHEN pr.cuota IS NULL THEN 'SIN_ODDS'
      WHEN pr.cuota < 1.6 THEN '<1.6'
      WHEN pr.cuota < 1.8 THEN '1.6-1.8'
      WHEN pr.cuota < 2.0 THEN '1.8-2.0'
      ELSE '>=2.0'
    END::text AS odds_bucket,
    COALESCE(pr.p_calibrada, pr.p_raw)::numeric AS confidence_prob,
    CASE
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) IS NULL THEN 'SIN_CONFIANZA'
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) >= 0.80 THEN '0.80+'
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) >= 0.70 THEN '0.70-0.79'
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) >= 0.60 THEN '0.60-0.69'
      ELSE '<0.60'
    END::text AS confidence_bucket,
    1::int AS n,
    CASE WHEN pr.outcome_binario IS TRUE THEN 1 ELSE 0 END::int AS win_count,
    CASE WHEN pr.outcome_binario IS FALSE THEN 1 ELSE 0 END::int AS loss_count,
    0::int AS push_count,
    NULL::numeric AS roi_pct_monetario,
    CASE
      WHEN pr.cuota IS NULL OR pr.cuota <= 0 OR pr.outcome_binario IS NULL THEN NULL
      WHEN pr.outcome_binario IS TRUE THEN (pr.cuota - 1.0) * 100.0
      ELSE -100.0
    END::numeric AS roi_unit_pct,
    CASE
      WHEN COALESCE(pr.p_calibrada, pr.p_raw) IS NOT NULL AND pr.cuota IS NOT NULL AND pr.cuota > 0
        THEN (COALESCE(pr.p_calibrada, pr.p_raw) - (1.0 / pr.cuota))::numeric
      ELSE NULL
    END::numeric AS edge_medio_base,
    'B'::text AS source_quality_flag,
    'confidence_temporal_policy_activa'::text AS residual_warning
  FROM predicciones_registradas pr
  WHERE pr.outcome_binario IS NOT NULL
),
fut_apuestas AS (
  SELECT
    'fut_apuestas:' || af.id::text AS event_id,
    'FUTBOL'::text AS sport,
    'apuestas_futbol'::text AS source,
    UPPER(COALESCE(af.mercado::text, 'SIN_MERCADO'))::text AS market_type,
    COALESCE(af.fecha_partido::date, af.creado_en::date) AS periodo,
    af.cuota::numeric AS odds_value,
    CASE
      WHEN af.cuota IS NULL THEN 'SIN_ODDS'
      WHEN af.cuota < 1.6 THEN '<1.6'
      WHEN af.cuota < 1.8 THEN '1.6-1.8'
      WHEN af.cuota < 2.0 THEN '1.8-2.0'
      ELSE '>=2.0'
    END::text AS odds_bucket,
    af.probabilidad_sistema::numeric AS confidence_prob,
    CASE
      WHEN af.probabilidad_sistema IS NULL THEN 'SIN_CONFIANZA'
      WHEN af.probabilidad_sistema >= 0.80 THEN '0.80+'
      WHEN af.probabilidad_sistema >= 0.70 THEN '0.70-0.79'
      WHEN af.probabilidad_sistema >= 0.60 THEN '0.60-0.69'
      ELSE '<0.60'
    END::text AS confidence_bucket,
    1::int AS n,
    CASE WHEN UPPER(COALESCE(af.resultado::text, '')) = 'GANADA' THEN 1 ELSE 0 END::int AS win_count,
    CASE WHEN UPPER(COALESCE(af.resultado::text, '')) = 'PERDIDA' THEN 1 ELSE 0 END::int AS loss_count,
    CASE WHEN UPPER(COALESCE(af.resultado::text, '')) = 'PUSH' THEN 1 ELSE 0 END::int AS push_count,
    CASE
      WHEN af.stake IS NULL OR af.stake = 0 OR af.ganancia IS NULL THEN NULL
      ELSE (af.ganancia / af.stake) * 100.0
    END::numeric AS roi_pct_monetario,
    NULL::numeric AS roi_unit_pct,
    CASE
      WHEN af.valor_esperado IS NOT NULL THEN af.valor_esperado::numeric
      WHEN af.probabilidad_sistema IS NOT NULL AND af.cuota IS NOT NULL AND af.cuota > 0
        THEN (af.probabilidad_sistema - (1.0 / af.cuota))::numeric
      ELSE NULL
    END::numeric AS edge_medio_base,
    CASE
      WHEN af.probabilidad_sistema IS NOT NULL THEN 'C'
      ELSE 'B'
    END::text AS source_quality_flag,
    CASE
      WHEN af.probabilidad_sistema IS NOT NULL THEN 'drift_futbol_residual;confidence_temporal_policy_activa'
      ELSE 'drift_futbol_residual'
    END::text AS residual_warning
  FROM apuestas_futbol af
  WHERE UPPER(COALESCE(af.resultado::text, '')) IN ('GANADA', 'PERDIDA', 'PUSH')
),
fut_pred AS (
  SELECT
    'fut_pred:' || pf.id::text AS event_id,
    'FUTBOL'::text AS sport,
    'predicciones_futbol'::text AS source,
    UPPER(COALESCE(pf.mercado::text, 'SIN_MERCADO'))::text AS market_type,
    COALESCE(pf.fecha_partido::date, pf.timestamp_generacion::date) AS periodo,
    NULL::numeric AS odds_value,
    'SIN_ODDS'::text AS odds_bucket,
    COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under)::numeric AS confidence_prob,
    CASE
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) IS NULL THEN 'SIN_CONFIANZA'
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) >= 0.80 THEN '0.80+'
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) >= 0.70 THEN '0.70-0.79'
      WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, pf.prob_under_calibrada, pf.prob_under) >= 0.60 THEN '0.60-0.69'
      ELSE '<0.60'
    END::text AS confidence_bucket,
    1::int AS n,
    CASE WHEN pf.outcome_binario IS TRUE THEN 1 ELSE 0 END::int AS win_count,
    CASE WHEN pf.outcome_binario IS FALSE THEN 1 ELSE 0 END::int AS loss_count,
    0::int AS push_count,
    NULL::numeric AS roi_pct_monetario,
    NULL::numeric AS roi_unit_pct,
    NULL::numeric AS edge_medio_base,
    'C'::text AS source_quality_flag,
    'drift_futbol_residual;confidence_temporal_policy_activa'::text AS residual_warning
  FROM predicciones_futbol pf
  WHERE pf.outcome_binario IS NOT NULL
)
SELECT * FROM nba_apuestas
UNION ALL SELECT * FROM nba_pred
UNION ALL SELECT * FROM fut_apuestas
UNION ALL SELECT * FROM fut_pred;
