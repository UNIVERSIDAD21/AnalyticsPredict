-- BASELINES_VALIDACION_NBA.sql
-- Fuente canónica elegida: tabla `apuestas` (bitácora NBA), porque contiene
-- resultado final de apuesta, stake/ganancia, mercado, cuota y confianza_sistema.
-- Las consultas asumen que `resultado` usa: GANADA, PERDIDA, PUSH, PENDIENTE, ANULADA.

-- Parámetros esperados (inyectados por cliente SQL/script):
-- :fecha_inicio (DATE/TIMESTAMP)
-- :fecha_fin    (DATE/TIMESTAMP)

-- 1) Universo base (solo apuestas resueltas para métricas de rendimiento)
WITH base AS (
  SELECT
    id,
    creado_en,
    fecha_partido,
    mercado,
    lado,
    cuota,
    stake,
    ganancia,
    confianza_sistema,
    resultado
  FROM apuestas
  WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN :fecha_inicio::date AND :fecha_fin::date
)
SELECT
  COUNT(*) AS n_total,
  COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA','PUSH')) AS n_resueltas,
  MIN(COALESCE(fecha_partido::date, creado_en::date)) AS fecha_min,
  MAX(COALESCE(fecha_partido::date, creado_en::date)) AS fecha_max
FROM base;

-- 2) Baseline global: win rate + ROI
WITH base AS (
  SELECT *
  FROM apuestas
  WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN :fecha_inicio::date AND :fecha_fin::date
    AND resultado IN ('GANADA','PERDIDA','PUSH')
)
SELECT
  COUNT(*) AS n_resueltas,
  COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
  COUNT(*) FILTER (WHERE resultado = 'GANADA') AS n_ganadas,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
    / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
    4
  ) AS win_rate_pct,
  ROUND(
    100.0 * COALESCE(SUM(ganancia), 0)
    / NULLIF(COALESCE(SUM(stake), 0), 0),
    4
  ) AS roi_pct,
  ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
  ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
FROM base;

-- 3) Confidence paradox: desempeño por confianza_sistema
WITH base AS (
  SELECT *
  FROM apuestas
  WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN :fecha_inicio::date AND :fecha_fin::date
    AND resultado IN ('GANADA','PERDIDA','PUSH')
)
SELECT
  UPPER(COALESCE(confianza_sistema, 'SIN_DATO')) AS confianza,
  COUNT(*) AS n_resueltas,
  COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
  COUNT(*) FILTER (WHERE resultado = 'GANADA') AS n_ganadas,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
    / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
    4
  ) AS win_rate_pct,
  ROUND(100.0 * COALESCE(SUM(ganancia),0) / NULLIF(COALESCE(SUM(stake),0),0), 4) AS roi_pct,
  ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
  ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
FROM base
GROUP BY 1
ORDER BY CASE UPPER(COALESCE(confianza_sistema, 'SIN_DATO'))
  WHEN 'ALTA' THEN 1
  WHEN 'MEDIA' THEN 2
  WHEN 'BAJA' THEN 3
  ELSE 9
END;

-- 4) Odds > 2.0 vs <= 2.0
WITH base AS (
  SELECT *
  FROM apuestas
  WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN :fecha_inicio::date AND :fecha_fin::date
    AND resultado IN ('GANADA','PERDIDA','PUSH')
    AND cuota IS NOT NULL
)
SELECT
  CASE WHEN cuota > 2.0 THEN 'ODDS_GT_2_0' ELSE 'ODDS_LE_2_0' END AS segmento_odds,
  COUNT(*) AS n_resueltas,
  COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
    / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
    4
  ) AS win_rate_pct,
  ROUND(100.0 * COALESCE(SUM(ganancia),0) / NULLIF(COALESCE(SUM(stake),0),0), 4) AS roi_pct,
  ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
  ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
FROM base
GROUP BY 1
ORDER BY 1;

-- 5) Quarter markets vs Full-game
WITH base AS (
  SELECT *
  FROM apuestas
  WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN :fecha_inicio::date AND :fecha_fin::date
    AND resultado IN ('GANADA','PERDIDA','PUSH')
)
SELECT
  CASE
    WHEN UPPER(COALESCE(mercado, '')) IN ('Q1','Q2','Q3','Q4') THEN 'QUARTER_MARKETS'
    WHEN UPPER(COALESCE(mercado, '')) IN ('COMPLETO','FULL','FULL_GAME') THEN 'FULL_GAME_MARKETS'
    ELSE 'OTROS'
  END AS segmento_mercado,
  COUNT(*) AS n_resueltas,
  COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
    / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
    4
  ) AS win_rate_pct,
  ROUND(100.0 * COALESCE(SUM(ganancia),0) / NULLIF(COALESCE(SUM(stake),0),0), 4) AS roi_pct,
  ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
  ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
FROM base
GROUP BY 1
ORDER BY 1;
