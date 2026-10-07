-- El esquema single-user histórico conserva tres vistas con ROI sin gate.
-- Mantener columnas/tipos y filas; despublicar solo el ratio no certificable.
-- Validar primero en PostgreSQL efímero y aplicar con backup de definiciones.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

CREATE OR REPLACE VIEW vista_analisis_apuestas AS
SELECT a.*,
  CASE WHEN a.devig_overround IS NOT NULL THEN round((a.devig_overround - 1) * 100, 2) END AS vig_porcentaje,
  round((a.probabilidad_sistema - coalesce(a.devig_p_mkt_raw, 1 / nullif(a.cuota, 0))) * 100, 2) AS edge_raw_porcentaje,
  round(coalesce(a.edge_real, 0) * 100, 2) AS edge_real_porcentaje,
  CASE WHEN a.bankroll_momento > 0 THEN round(a.stake / a.bankroll_momento * 100, 2) END AS stake_porcentaje_real,
  NULL::numeric AS roi_porcentaje,
  CASE WHEN a.score_total IS NULL THEN 'SIN_SCORE'
       WHEN a.score_total >= 5 THEN 'EXCELENTE'
       WHEN a.score_total >= 3 THEN 'BUENA'
       WHEN a.score_total >= 1 THEN 'ACEPTABLE'
       WHEN a.score_total > 0 THEN 'MARGINAL' ELSE 'NO_APTA' END AS clasificacion_calidad
FROM apuestas a;

CREATE OR REPLACE VIEW vista_resumen_apuestas AS
SELECT count(*) AS total_apuestas,
  count(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
  count(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
  count(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
  count(*) FILTER (WHERE resultado = 'PUSH') AS push,
  round(100.0 * count(*) FILTER (WHERE resultado = 'GANADA') /
    nullif(count(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')), 0), 2) AS winrate,
  sum(ganancia) AS ganancia_total,
  sum(stake) FILTER (WHERE resultado <> 'PENDIENTE') AS total_apostado,
  NULL::numeric AS roi
FROM apuestas;

CREATE OR REPLACE VIEW vista_resumen_apuestas_futbol AS
SELECT mercado, count(*) AS total_apuestas,
  count(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
  count(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
  count(*) FILTER (WHERE resultado = 'PUSH') AS push,
  count(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
  round(100.0 * count(*) FILTER (WHERE resultado = 'GANADA') /
    nullif(count(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')), 0), 2) AS win_rate,
  sum(stake) AS stake_total, sum(ganancia) AS ganancia_total,
  NULL::numeric AS roi
FROM apuestas_futbol GROUP BY mercado;

COMMIT;
