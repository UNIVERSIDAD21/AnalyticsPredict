-- Bloque E: conservar filas históricas, excluir pares ligados a marcador NBA 0–0.
-- Solo cambia la vista agregada; mismo orden, tipos y número de columnas.
-- La vista base retiene las filas para que auditores contabilicen exclusiones.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE OR REPLACE VIEW public.vista_resumen_calibracion AS
 SELECT mercado,
    origen,
    count(p_raw_pareada) AS n_predicciones,
    round(avg(p_raw_pareada), 4) AS promedio_p_raw,
    round(avg(p_efectiva_pareada), 4) AS promedio_p_efectiva,
    round(avg(CASE WHEN p_raw_pareada IS NULL THEN NULL
                   WHEN outcome_binario THEN 1.0 ELSE 0.0 END), 4) AS frecuencia_real,
    round(avg(p_raw_pareada) - avg(CASE WHEN p_raw_pareada IS NULL THEN NULL
                                        WHEN outcome_binario THEN 1.0 ELSE 0.0 END), 4) AS sesgo_bruto,
    round(avg(power(p_raw_pareada - CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END, 2::numeric)), 4) AS brier_score_raw,
    round(avg(power(p_efectiva_pareada - CASE WHEN outcome_binario THEN 1.0 ELSE 0.0 END, 2::numeric)), 4) AS brier_score_efectivo,
    round(stddev(p_raw_pareada), 4) AS sharpness,
    min(fecha_partido) FILTER (WHERE p_raw_pareada IS NOT NULL) AS fecha_min,
    max(fecha_partido) FILTER (WHERE p_raw_pareada IS NOT NULL) AS fecha_max
   FROM (
     SELECT v.mercado, v.origen, v.fecha_partido, v.outcome_binario,
            CASE WHEN v.p_raw BETWEEN 0 AND 1 AND v.p_efectiva BETWEEN 0 AND 1
                       AND NOT COALESCE(pb.local_total = 0 AND pb.visitante_total = 0, false)
                 THEN v.p_raw END AS p_raw_pareada,
            CASE WHEN v.p_raw BETWEEN 0 AND 1 AND v.p_efectiva BETWEEN 0 AND 1
                       AND NOT COALESCE(pb.local_total = 0 AND pb.visitante_total = 0, false)
                 THEN v.p_efectiva END AS p_efectiva_pareada
       FROM public.vista_predicciones_para_calibracion v
       LEFT JOIN public.partidos_baloncesto pb ON pb.id = v.partido_id
   ) pares
  GROUP BY mercado, origen
  ORDER BY mercado, origen;

COMMIT;
