-- ANALISIS_SEGMENTOS_NBA.sql
-- Análisis de segmentos NBA (sin cambios de modelo/pipeline)
-- Fuente principal: tabla apuestas (resultado realizado de picks NBA)

-- A) ROI por quarter (Q1-Q4)
SELECT mercado, COUNT(*) n,
ROUND(100.0*SUM(CASE WHEN resultado='GANADA' THEN 1 ELSE 0 END)
/NULLIF(SUM(CASE WHEN resultado IN ('GANADA','PERDIDA') THEN 1 ELSE 0 END),0),4) win_rate_pct,
ROUND(100.0*SUM(COALESCE(ganancia,0))/NULLIF(SUM(COALESCE(stake,0)),0),4) roi_pct,
ROUND(SUM(stake),2) stake_total, ROUND(SUM(ganancia),2) ganancia_total
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
  AND UPPER(COALESCE(mercado,'')) IN ('Q1','Q2','Q3','Q4')
GROUP BY mercado ORDER BY mercado;

-- B) Distribución por línea (quarter)
SELECT mercado, linea, COUNT(*) n,
ROUND(100.0*SUM(CASE WHEN resultado='GANADA' THEN 1 ELSE 0 END)
/NULLIF(SUM(CASE WHEN resultado IN ('GANADA','PERDIDA') THEN 1 ELSE 0 END),0),2) win_rate_pct,
ROUND(100.0*SUM(ganancia)/NULLIF(SUM(stake),0),2) roi_pct
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
  AND UPPER(COALESCE(mercado,'')) IN ('Q1','Q2','Q3','Q4')
GROUP BY mercado,linea ORDER BY mercado,linea;

-- C) Quarter x confidence
SELECT mercado, UPPER(COALESCE(confianza_sistema,'SIN_DATO')) confianza,
COUNT(*) n,
ROUND(100.0*SUM(CASE WHEN resultado='GANADA' THEN 1 ELSE 0 END)
/NULLIF(SUM(CASE WHEN resultado IN ('GANADA','PERDIDA') THEN 1 ELSE 0 END),0),2) win_rate_pct,
ROUND(100.0*SUM(ganancia)/NULLIF(SUM(stake),0),2) roi_pct
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
AND UPPER(COALESCE(mercado,'')) IN ('Q1','Q2','Q3','Q4')
GROUP BY mercado,2 ORDER BY mercado,2;

-- D) Full-game: breakdown por bucket de línea
SELECT CASE
 WHEN linea < 205 THEN '<205'
 WHEN linea >=205 AND linea <215 THEN '205-214.9'
 WHEN linea >=215 AND linea <225 THEN '215-224.9'
 ELSE '>=225' END linea_bucket,
COUNT(*) n,
ROUND(100.0*SUM(CASE WHEN resultado='GANADA' THEN 1 ELSE 0 END)
/NULLIF(SUM(CASE WHEN resultado IN ('GANADA','PERDIDA') THEN 1 ELSE 0 END),0),2) win_rate_pct,
ROUND(100.0*SUM(ganancia)/NULLIF(SUM(stake),0),2) roi_pct
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
AND UPPER(COALESCE(mercado,'')) IN ('COMPLETO','FULL','FULL_GAME')
GROUP BY 1 ORDER BY 1;

-- E) Full-game: breakdown por odds bucket
SELECT CASE
 WHEN cuota < 1.6 THEN '<1.6'
 WHEN cuota >=1.6 AND cuota <1.8 THEN '1.6-1.8'
 WHEN cuota >=1.8 AND cuota <2.0 THEN '1.8-2.0'
 ELSE '>=2.0' END odds_bucket,
COUNT(*) n,
ROUND(100.0*SUM(CASE WHEN resultado='GANADA' THEN 1 ELSE 0 END)
/NULLIF(SUM(CASE WHEN resultado IN ('GANADA','PERDIDA') THEN 1 ELSE 0 END),0),2) win_rate_pct,
ROUND(100.0*SUM(ganancia)/NULLIF(SUM(stake),0),2) roi_pct
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
AND cuota IS NOT NULL
AND UPPER(COALESCE(mercado,'')) IN ('COMPLETO','FULL','FULL_GAME')
GROUP BY 1 ORDER BY 1;

-- F) Odds global bucket
SELECT CASE
 WHEN cuota < 1.6 THEN '<1.6'
 WHEN cuota >=1.6 AND cuota <1.8 THEN '1.6-1.8'
 WHEN cuota >=1.8 AND cuota <2.0 THEN '1.8-2.0'
 ELSE '>=2.0' END odds_bucket,
COUNT(*) n,
ROUND(100.0*SUM(CASE WHEN resultado='GANADA' THEN 1 ELSE 0 END)
/NULLIF(SUM(CASE WHEN resultado IN ('GANADA','PERDIDA') THEN 1 ELSE 0 END),0),2) win_rate_pct,
ROUND(100.0*SUM(ganancia)/NULLIF(SUM(stake),0),2) roi_pct
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
AND cuota IS NOT NULL
GROUP BY 1 ORDER BY 1;

-- G) Confidence por probabilidad (redefinición de buckets)
SELECT CASE
 WHEN probabilidad_sistema >= 0.80 THEN '0.80-1.00'
 WHEN probabilidad_sistema >= 0.70 THEN '0.70-0.79'
 WHEN probabilidad_sistema >= 0.60 THEN '0.60-0.69'
 WHEN probabilidad_sistema >= 0.50 THEN '0.50-0.59'
 ELSE '<0.50' END prob_bucket,
COUNT(*) n,
ROUND(AVG(probabilidad_sistema)::numeric,4) prob_media,
ROUND(AVG(CASE WHEN resultado='GANADA' THEN 1.0 WHEN resultado='PERDIDA' THEN 0.0 ELSE NULL END)::numeric,4) hit_rate,
ROUND(100.0*SUM(ganancia)/NULLIF(SUM(stake),0),2) roi_pct
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
AND probabilidad_sistema IS NOT NULL
GROUP BY 1 ORDER BY 1 DESC;

-- H) Calibración cruda (probabilidad vs outcome)
SELECT ROUND(probabilidad_sistema::numeric,2) prob_bin,
COUNT(*) n,
ROUND(AVG(CASE WHEN resultado='GANADA' THEN 1.0 WHEN resultado='PERDIDA' THEN 0.0 ELSE NULL END)::numeric,4) observed_win
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA')
AND probabilidad_sistema IS NOT NULL
GROUP BY 1 ORDER BY 1;

-- I) Cobertura temporal y verificación de histórico fuera de apuestas
SELECT 'apuestas' fuente, MIN(COALESCE(fecha_partido::date,creado_en::date)) min_fecha,
MAX(COALESCE(fecha_partido::date,creado_en::date)) max_fecha, COUNT(*) n
FROM apuestas
UNION ALL
SELECT 'predicciones_registradas', MIN(COALESCE(fecha_partido::date,timestamp_generacion::date)),
MAX(COALESCE(fecha_partido::date,timestamp_generacion::date)), COUNT(*)
FROM predicciones_registradas
UNION ALL
SELECT 'partidos_baloncesto', MIN(fecha_partido::date), MAX(fecha_partido::date), COUNT(*)
FROM partidos_baloncesto;
