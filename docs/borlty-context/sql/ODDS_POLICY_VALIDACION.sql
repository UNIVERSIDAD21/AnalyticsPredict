-- ODDS_POLICY_VALIDACION.sql
-- Consultas para sustentar política temporal de odds altas (bloque 05 - prioridad crítica 2)

-- 1) Dataset ampliado deduplicado por (partido_id, mercado, linea)
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
SELECT mercado,
  CASE WHEN cuota <1.6 THEN '<1.6' WHEN cuota <1.8 THEN '1.6-1.8' WHEN cuota <2.0 THEN '1.8-2.0' ELSE '>=2.0' END odds_bucket,
  COUNT(*) n,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct,
  ROUND(AVG(prob_pred)::numeric,4) prob_media,
  ROUND(AVG((1.0/NULLIF(cuota,0)))::numeric,4) p_implied_media,
  ROUND(AVG(prob_pred - (1.0/NULLIF(cuota,0)))::numeric,4) edge_medio
FROM expanded
WHERE cuota IS NOT NULL
GROUP BY mercado, odds_bucket
ORDER BY mercado, odds_bucket;

-- 2) Dataset corto (apuestas ejecutadas)
SELECT mercado,
  CASE WHEN cuota <1.6 THEN '<1.6' WHEN cuota <1.8 THEN '1.6-1.8' WHEN cuota <2.0 THEN '1.8-2.0' ELSE '>=2.0' END odds_bucket,
  COUNT(*) n,
  ROUND(100.0*AVG(CASE WHEN resultado='GANADA' THEN 1.0 ELSE 0.0 END),4) win_rate_pct,
  ROUND(100.0*AVG(CASE WHEN resultado='GANADA' THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct,
  ROUND(AVG(probabilidad_sistema)::numeric,4) prob_media,
  ROUND(AVG((1.0/NULLIF(cuota,0)))::numeric,4) p_implied_media,
  ROUND(AVG(probabilidad_sistema - (1.0/NULLIF(cuota,0)))::numeric,4) edge_medio
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA')
  AND cuota IS NOT NULL
GROUP BY mercado, odds_bucket
ORDER BY mercado, odds_bucket;

-- 3) Confiabilidad global por bucket (dataset ampliado)
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
SELECT
  CASE WHEN cuota <1.6 THEN '<1.6' WHEN cuota <1.8 THEN '1.6-1.8' WHEN cuota <2.0 THEN '1.8-2.0' ELSE '>=2.0' END odds_bucket,
  COUNT(*) n,
  ROUND(AVG(prob_pred)::numeric,4) prob_media,
  ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4) hit_rate,
  ROUND(AVG(prob_pred - (1.0/NULLIF(cuota,0)))::numeric,4) edge_medio,
  ROUND(100.0*AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END),4) roi_unit_pct
FROM expanded
WHERE cuota IS NOT NULL
GROUP BY 1
ORDER BY 1;
