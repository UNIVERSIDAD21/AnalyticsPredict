-- DIAGNOSTICO_CONFIDENCE_CALIBRATION.sql
-- Reproduce diagnóstico de confidence/calibration del bloque 05 prioridad crítica 1.

-- =============================================================
-- A) Reconstrucción exacta del nivel de confidence (backend NBA)
-- Heurística en código (nba_predictor_cuartos.py):
-- - score_vol: desviacion_total <5.5 =>2, <7.5 =>1, else 0
-- - score_prob: p>=0.70 =>2, p>=0.60 =>1, else 0
-- - score_edge: z>=1.5 =>2, z>=1.0 =>1, else 0
-- - nivel: score_total>=3 ALTA, >=2 MEDIA, else BAJA
--
-- Aquí se aproxima con columnas persistidas:
-- - desviacion_predicha ~ desviacion_total
-- - prob = COALESCE(p_calibrada, p_raw)
-- - z = abs(media_predicha-linea)/desviacion_predicha
--
WITH base AS (
  SELECT
    id,
    mercado,
    cuota,
    COALESCE(p_calibrada, p_raw) AS prob,
    media_predicha,
    linea,
    desviacion_predicha,
    outcome_binario,
    CASE
      WHEN desviacion_predicha < 5.5 THEN 2
      WHEN desviacion_predicha < 7.5 THEN 1
      ELSE 0
    END AS score_vol,
    CASE
      WHEN COALESCE(p_calibrada,p_raw) >= 0.70 THEN 2
      WHEN COALESCE(p_calibrada,p_raw) >= 0.60 THEN 1
      ELSE 0
    END AS score_prob,
    CASE
      WHEN linea IS NULL OR desviacion_predicha IS NULL OR desviacion_predicha = 0 THEN 0
      WHEN abs(media_predicha - linea) / NULLIF(desviacion_predicha,0) >= 1.5 THEN 2
      WHEN abs(media_predicha - linea) / NULLIF(desviacion_predicha,0) >= 1.0 THEN 1
      ELSE 0
    END AS score_edge,
    CASE
      WHEN linea IS NULL OR desviacion_predicha IS NULL OR desviacion_predicha = 0 THEN NULL
      ELSE abs(media_predicha - linea) / NULLIF(desviacion_predicha,0)
    END AS distancia_z,
    ROW_NUMBER() OVER (
      PARTITION BY partido_id, mercado, COALESCE(linea,-9999)
      ORDER BY COALESCE(p_calibrada,p_raw) DESC, timestamp_generacion DESC, id DESC
    ) rn
  FROM predicciones_registradas
  WHERE outcome_binario IS NOT NULL
), d AS (
  SELECT *,
    (score_vol + score_prob + score_edge) AS score_total,
    CASE
      WHEN (score_vol + score_prob + score_edge) >= 3 THEN 'ALTA'
      WHEN (score_vol + score_prob + score_edge) >= 2 THEN 'MEDIA'
      ELSE 'BAJA'
    END AS nivel_confianza,
    CASE WHEN score_vol=0 THEN 'alta' WHEN score_vol=1 THEN 'moderada' ELSE 'baja' END AS volatilidad
  FROM base
  WHERE rn=1
)
SELECT
  nivel_confianza,
  COUNT(*) AS n,
  ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4) AS hit_rate,
  ROUND(AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END)::numeric,4) AS roi_unit,
  ROUND(AVG(prob)::numeric,4) AS prob_media,
  ROUND(AVG(distancia_z)::numeric,4) AS z_media
FROM d
GROUP BY 1
ORDER BY CASE nivel_confianza WHEN 'ALTA' THEN 1 WHEN 'MEDIA' THEN 2 ELSE 3 END;

-- =============================================================
-- B) Monotonicidad por mercado
WITH base AS (
  SELECT
    id,
    mercado,
    cuota,
    COALESCE(p_calibrada,p_raw) AS prob,
    media_predicha,
    linea,
    desviacion_predicha,
    outcome_binario,
    CASE WHEN desviacion_predicha < 5.5 THEN 2 WHEN desviacion_predicha < 7.5 THEN 1 ELSE 0 END AS score_vol,
    CASE WHEN COALESCE(p_calibrada,p_raw) >= 0.70 THEN 2 WHEN COALESCE(p_calibrada,p_raw) >= 0.60 THEN 1 ELSE 0 END AS score_prob,
    CASE
      WHEN linea IS NULL OR desviacion_predicha IS NULL OR desviacion_predicha = 0 THEN 0
      WHEN abs(media_predicha - linea) / NULLIF(desviacion_predicha,0) >= 1.5 THEN 2
      WHEN abs(media_predicha - linea) / NULLIF(desviacion_predicha,0) >= 1.0 THEN 1
      ELSE 0
    END AS score_edge,
    ROW_NUMBER() OVER (
      PARTITION BY partido_id, mercado, COALESCE(linea,-9999)
      ORDER BY COALESCE(p_calibrada,p_raw) DESC, timestamp_generacion DESC, id DESC
    ) rn
  FROM predicciones_registradas
  WHERE outcome_binario IS NOT NULL
), d AS (
  SELECT *,
    CASE
      WHEN (score_vol + score_prob + score_edge) >= 3 THEN 'ALTA'
      WHEN (score_vol + score_prob + score_edge) >= 2 THEN 'MEDIA'
      ELSE 'BAJA'
    END AS nivel_confianza
  FROM base
  WHERE rn=1
)
SELECT
  mercado,
  nivel_confianza,
  COUNT(*) AS n,
  ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4) AS hit_rate,
  ROUND(AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END)::numeric,4) AS roi_unit
FROM d
GROUP BY mercado, nivel_confianza
ORDER BY mercado, CASE nivel_confianza WHEN 'ALTA' THEN 1 WHEN 'MEDIA' THEN 2 ELSE 3 END;

-- =============================================================
-- C) Componentes raíz (volatilidad, probabilidad, edge-z)
WITH base AS (
  SELECT
    id,
    cuota,
    COALESCE(p_calibrada,p_raw) AS prob,
    outcome_binario,
    CASE WHEN desviacion_predicha < 5.5 THEN 2 WHEN desviacion_predicha < 7.5 THEN 1 ELSE 0 END AS score_vol,
    CASE WHEN COALESCE(p_calibrada,p_raw) >= 0.70 THEN 2 WHEN COALESCE(p_calibrada,p_raw) >= 0.60 THEN 1 ELSE 0 END AS score_prob,
    CASE
      WHEN linea IS NULL OR desviacion_predicha IS NULL OR desviacion_predicha = 0 THEN 0
      WHEN abs(media_predicha - linea) / NULLIF(desviacion_predicha,0) >= 1.5 THEN 2
      WHEN abs(media_predicha - linea) / NULLIF(desviacion_predicha,0) >= 1.0 THEN 1
      ELSE 0
    END AS score_edge,
    ROW_NUMBER() OVER (
      PARTITION BY partido_id, mercado, COALESCE(linea,-9999)
      ORDER BY COALESCE(p_calibrada,p_raw) DESC, timestamp_generacion DESC, id DESC
    ) rn
  FROM predicciones_registradas
  WHERE outcome_binario IS NOT NULL
), d AS (
  SELECT *,
    CASE WHEN score_vol=0 THEN 'vol_alta' WHEN score_vol=1 THEN 'vol_mod' ELSE 'vol_baja' END AS vol_bucket,
    CASE WHEN score_prob=2 THEN 'prob_>=0.70' WHEN score_prob=1 THEN 'prob_0.60_0.69' ELSE 'prob_<0.60' END AS prob_bucket,
    CASE WHEN score_edge=2 THEN 'z_>=1.5' WHEN score_edge=1 THEN 'z_1.0_1.49' ELSE 'z_<1.0' END AS edge_bucket
  FROM base
  WHERE rn=1
)
SELECT 'volatilidad' eje, vol_bucket bucket, COUNT(*) n,
ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4) hit_rate,
ROUND(AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END)::numeric,4) roi_unit
FROM d GROUP BY 1,2
UNION ALL
SELECT 'probabilidad', prob_bucket, COUNT(*),
ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4),
ROUND(AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END)::numeric,4)
FROM d GROUP BY 1,2
UNION ALL
SELECT 'edge_z', edge_bucket, COUNT(*),
ROUND(AVG(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END)::numeric,4),
ROUND(AVG(CASE WHEN outcome_binario THEN (COALESCE(cuota,1)-1) ELSE -1 END)::numeric,4)
FROM d GROUP BY 1,2
ORDER BY eje,bucket;

-- =============================================================
-- D) Dependencia stake vs confidence en apuestas ejecutadas (tabla apuestas)
SELECT
  UPPER(confianza_sistema) AS confianza,
  COUNT(*) AS n,
  ROUND(AVG(stake)::numeric,2) AS stake_promedio,
  ROUND(AVG(CASE WHEN resultado='GANADA' THEN 1.0 ELSE 0.0 END)::numeric,4) AS hit_rate
FROM apuestas
WHERE resultado IN ('GANADA','PERDIDA','PUSH')
GROUP BY 1
ORDER BY 1;

-- =============================================================
-- E) Cobertura de volatilidad (si score_vol discrimina realmente)
WITH base AS (
  SELECT
    CASE WHEN desviacion_predicha < 5.5 THEN 'baja'
         WHEN desviacion_predicha < 7.5 THEN 'moderada'
         ELSE 'alta' END AS volatilidad,
    ROW_NUMBER() OVER (
      PARTITION BY partido_id, mercado, COALESCE(linea,-9999)
      ORDER BY COALESCE(p_calibrada,p_raw) DESC, timestamp_generacion DESC, id DESC
    ) rn
  FROM predicciones_registradas
  WHERE outcome_binario IS NOT NULL
)
SELECT volatilidad, COUNT(*) n
FROM base
WHERE rn=1
GROUP BY 1
ORDER BY 1;
