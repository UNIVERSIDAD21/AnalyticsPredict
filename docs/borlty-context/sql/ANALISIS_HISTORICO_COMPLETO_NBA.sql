-- ANALISIS_HISTORICO_COMPLETO_NBA.sql
-- Consultas exactas usadas para ANALISIS_HISTORICO_COMPLETO_NBA.md

-- =========================
-- CTE base (reutilizado)
-- =========================
WITH expanded AS (
  SELECT * FROM (
    SELECT
      pr.id,
      pr.partido_id,
      pr.mercado,
      pr.lado,
      pr.linea,
      pr.cuota,
      COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
      pr.p_raw,
      pr.p_calibrada,
      pr.outcome_binario,
      pr.fecha_partido,
      pr.timestamp_generacion,
      ROW_NUMBER() OVER (
        PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
        ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
      ) AS rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t
  WHERE rn = 1
),
short_apuestas AS (
  SELECT
    id,
    partido_id,
    mercado,
    lado,
    linea,
    cuota,
    probabilidad_sistema AS prob_pred,
    NULL::numeric AS p_raw,
    NULL::numeric AS p_calibrada,
    CASE
      WHEN resultado='GANADA' THEN TRUE
      WHEN resultado='PERDIDA' THEN FALSE
      ELSE NULL
    END AS outcome_binario,
    fecha_partido,
    creado_en AS timestamp_generacion
  FROM apuestas
  WHERE resultado IN ('GANADA','PERDIDA')
)
SELECT 1;

-- 1) Cobertura temporal y tamaño
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
), short_apuestas AS (
  SELECT id, partido_id, mercado, lado, linea, cuota, probabilidad_sistema AS prob_pred,
         CASE WHEN resultado='GANADA' THEN TRUE WHEN resultado='PERDIDA' THEN FALSE END AS outcome_binario,
         fecha_partido, creado_en AS timestamp_generacion
  FROM apuestas WHERE resultado IN ('GANADA','PERDIDA')
)
SELECT 'expanded' dataset, COUNT(*) n,
MIN(COALESCE(fecha_partido::date,timestamp_generacion::date)) min_fecha,
MAX(COALESCE(fecha_partido::date,timestamp_generacion::date)) max_fecha
FROM expanded
UNION ALL
SELECT 'short_apuestas', COUNT(*),
MIN(COALESCE(fecha_partido::date,timestamp_generacion::date)),
MAX(COALESCE(fecha_partido::date,timestamp_generacion::date))
FROM short_apuestas
UNION ALL
SELECT 'predicciones_registradas_raw', COUNT(*),
MIN(COALESCE(fecha_partido::date,timestamp_generacion::date)),
MAX(COALESCE(fecha_partido::date,timestamp_generacion::date))
FROM predicciones_registradas
UNION ALL
SELECT 'partidos_baloncesto', COUNT(*), MIN(fecha_partido::date), MAX(fecha_partido::date)
FROM partidos_baloncesto;

-- 2) Global compare
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
), short_apuestas AS (
  SELECT cuota, probabilidad_sistema AS prob_pred,
         CASE WHEN resultado='GANADA' THEN TRUE WHEN resultado='PERDIDA' THEN FALSE END AS outcome_binario
  FROM apuestas WHERE resultado IN ('GANADA','PERDIDA')
)
SELECT 'expanded' dataset, COUNT(*) n,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
FROM expanded
UNION ALL
SELECT 'short_apuestas', COUNT(*),
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4),
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4)
FROM short_apuestas;

-- 3) Mercado compare
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
), short_apuestas AS (
  SELECT mercado, cuota, probabilidad_sistema AS prob_pred,
         CASE WHEN resultado='GANADA' THEN TRUE WHEN resultado='PERDIDA' THEN FALSE END AS outcome_binario
  FROM apuestas WHERE resultado IN ('GANADA','PERDIDA')
)
SELECT dataset, mercado, n, win_rate_pct, roi_unit_pct FROM (
  SELECT 'expanded' dataset, mercado, COUNT(*) n,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
  FROM expanded GROUP BY mercado
  UNION ALL
  SELECT 'short_apuestas', mercado, COUNT(*) n,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4),
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4)
  FROM short_apuestas GROUP BY mercado
) s ORDER BY mercado,dataset;

-- 4) Odds bucket compare
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
), short_apuestas AS (
  SELECT cuota, probabilidad_sistema AS prob_pred,
         CASE WHEN resultado='GANADA' THEN TRUE WHEN resultado='PERDIDA' THEN FALSE END AS outcome_binario
  FROM apuestas WHERE resultado IN ('GANADA','PERDIDA')
)
SELECT dataset, odds_bucket, n, win_rate_pct, roi_unit_pct FROM (
  SELECT 'expanded' dataset,
  CASE WHEN cuota <1.6 THEN '<1.6' WHEN cuota <1.8 THEN '1.6-1.8' WHEN cuota <2.0 THEN '1.8-2.0' ELSE '>=2.0' END odds_bucket,
  COUNT(*) n,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
  FROM expanded WHERE cuota IS NOT NULL GROUP BY 2
  UNION ALL
  SELECT 'short_apuestas',
  CASE WHEN cuota <1.6 THEN '<1.6' WHEN cuota <1.8 THEN '1.6-1.8' WHEN cuota <2.0 THEN '1.8-2.0' ELSE '>=2.0' END,
  COUNT(*),
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4),
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4)
  FROM short_apuestas WHERE cuota IS NOT NULL GROUP BY 2
) s ORDER BY odds_bucket,dataset;

-- 5) Confidence bucket compare
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
), short_apuestas AS (
  SELECT probabilidad_sistema AS prob_pred, cuota,
         CASE WHEN resultado='GANADA' THEN TRUE WHEN resultado='PERDIDA' THEN FALSE END AS outcome_binario
  FROM apuestas WHERE resultado IN ('GANADA','PERDIDA')
)
SELECT dataset, conf_bucket, n, prob_media, hit_rate, roi_unit_pct FROM (
  SELECT 'expanded' dataset,
  CASE WHEN prob_pred >=0.8 THEN '0.80+' WHEN prob_pred >=0.7 THEN '0.70-0.79' WHEN prob_pred >=0.6 THEN '0.60-0.69' ELSE '<0.60' END conf_bucket,
  COUNT(*) n,
  ROUND(AVG(prob_pred)::numeric,4) prob_media,
  ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4) hit_rate,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
  FROM expanded WHERE prob_pred IS NOT NULL GROUP BY 2
  UNION ALL
  SELECT 'short_apuestas',
  CASE WHEN prob_pred >=0.8 THEN '0.80+' WHEN prob_pred >=0.7 THEN '0.70-0.79' WHEN prob_pred >=0.6 THEN '0.60-0.69' ELSE '<0.60' END,
  COUNT(*), ROUND(AVG(prob_pred)::numeric,4),
  ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4),
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4)
  FROM short_apuestas WHERE prob_pred IS NOT NULL GROUP BY 2
) s ORDER BY conf_bucket,dataset;

-- 6) Quarter focus (expanded)
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
)
SELECT mercado, COUNT(*) n,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
FROM expanded WHERE mercado IN ('Q1','Q2','Q3','Q4') GROUP BY mercado ORDER BY mercado;

-- 7) Full-game por línea (expanded)
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
)
SELECT CASE WHEN linea <205 THEN '<205' WHEN linea<215 THEN '205-214.9' WHEN linea<225 THEN '215-224.9' ELSE '>=225' END line_bucket,
COUNT(*) n,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
FROM expanded WHERE mercado='COMPLETO' GROUP BY 1 ORDER BY 1;

-- 8) Full-game por odds (expanded)
WITH expanded AS (
  SELECT * FROM (
    SELECT pr.*, COALESCE(pr.p_calibrada, pr.p_raw) AS prob_pred,
           ROW_NUMBER() OVER (
             PARTITION BY pr.partido_id, pr.mercado, COALESCE(pr.linea,-9999)
             ORDER BY COALESCE(pr.p_calibrada, pr.p_raw) DESC, pr.timestamp_generacion DESC, pr.id DESC
           ) rn
    FROM predicciones_registradas pr
    WHERE pr.outcome_binario IS NOT NULL
  ) t WHERE rn=1
)
SELECT CASE WHEN cuota <1.6 THEN '<1.6' WHEN cuota<1.8 THEN '1.6-1.8' WHEN cuota<2.0 THEN '1.8-2.0' ELSE '>=2.0' END odds_bucket,
COUNT(*) n,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
FROM expanded WHERE mercado='COMPLETO' AND cuota IS NOT NULL GROUP BY 1 ORDER BY 1;
