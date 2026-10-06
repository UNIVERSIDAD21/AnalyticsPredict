-- Definición de la vista dependiente observada en Neon el 2026-10-06.
CREATE VIEW public.vista_resumen_calibracion AS
 SELECT mercado,
    origen,
    count(*) AS n_predicciones,
    round(avg(p_raw), 4) AS promedio_p_raw,
    round(avg(COALESCE(p_calibrada, p_raw)), 4) AS promedio_p_efectiva,
    round(avg(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END), 4) AS frecuencia_real,
    round(avg(p_raw) - avg(CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END), 4) AS sesgo_bruto,
    round(avg(power(p_raw - CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END, 2::numeric)), 4) AS brier_score_raw,
    round(avg(power(COALESCE(p_calibrada, p_raw) - CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END, 2::numeric)), 4) AS brier_score_efectivo,
    round(stddev(p_raw), 4) AS sharpness,
    min(fecha_partido) AS fecha_min,
    max(fecha_partido) AS fecha_max
   FROM public.vista_predicciones_para_calibracion
  GROUP BY mercado, origen
  ORDER BY mercado, origen;
