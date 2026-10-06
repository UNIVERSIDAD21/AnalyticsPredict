-- H9: solo hay calibración efectiva con ID existente, mercado coincidente y p válida.
-- Una calibración histórica no depende del estado activo actual del calibrador.
-- CREATE OR REPLACE conserva columnas, tipos, permisos y dependencias; no altera filas.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE OR REPLACE VIEW public.vista_predicciones_para_calibracion AS
 SELECT pr.id,
    pr.timestamp_generacion,
    pr.origen,
    pr.modelo_version_id,
    CASE WHEN probs.p_calibrada_valida IS NOT NULL THEN pr.calibrador_id END AS calibrador_id,
    pr.partido_id,
    pr.temporada_id,
    pr.equipo_local_id,
    pr.equipo_visitante_id,
    pr.fecha_partido,
    pr.tipo_partido,
    pr.equipo_local_nombre,
    pr.equipo_visitante_nombre,
    pr.mercado,
    pr.lado,
    pr.linea,
    pr.linea_es_sintetica,
    pr.cuota,
    pr.cuota_over,
    pr.cuota_under,
    pr.media_predicha,
    pr.desviacion_predicha,
    pr.p_raw,
    pr.intervalo_inferior,
    pr.intervalo_superior,
    pr.nivel_intervalo,
    probs.p_calibrada_valida::numeric(5,4) AS p_calibrada,
    CASE WHEN probs.p_calibrada_valida IS NOT NULL THEN pr.calibrador_metodo END::character varying(20) AS calibrador_metodo,
    pr.valor_real,
    pr.outcome_binario,
    pr.timestamp_resolucion,
    pr.resuelto,
    pr.creado_en,
    pr.actualizado_en,
    floor(probs.p_raw_valida * 10::numeric) / 10::numeric AS bin_p_raw,
    floor(COALESCE(probs.p_calibrada_valida, probs.p_raw_valida) * 10::numeric) / 10::numeric AS bin_p_efectiva,
    COALESCE(probs.p_calibrada_valida, probs.p_raw_valida)::numeric(5,4) AS p_efectiva,
    el.nombre AS local_nombre,
    el.abreviatura AS local_abr,
    ev.nombre AS visitante_nombre,
    ev.abreviatura AS visitante_abr,
    t.nombre AS temporada_nombre
   FROM public.predicciones_registradas pr
     JOIN public.equipos el ON pr.equipo_local_id = el.id
     JOIN public.equipos ev ON pr.equipo_visitante_id = ev.id
     LEFT JOIN public.temporadas_baloncesto t ON pr.temporada_id = t.id
     LEFT JOIN public.calibradores cal ON cal.id = pr.calibrador_id AND cal.mercado = pr.mercado
     CROSS JOIN LATERAL (
       SELECT CASE WHEN pr.p_raw BETWEEN 0 AND 1 THEN pr.p_raw END AS p_raw_valida,
              CASE WHEN cal.id IS NOT NULL AND pr.p_calibrada BETWEEN 0 AND 1
                   THEN pr.p_calibrada END AS p_calibrada_valida
     ) probs
  WHERE pr.resuelto = true AND pr.outcome_binario IS NOT NULL;

-- La vista dependiente usaba COALESCE sin procedencia y podía incluir p fuera de rango.
-- Solo compara pares raw/efectiva válidos; 0 pares conserva métricas NULL/N-D.
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
     SELECT mercado, origen, fecha_partido, outcome_binario,
            CASE WHEN p_raw BETWEEN 0 AND 1 AND p_efectiva BETWEEN 0 AND 1
                 THEN p_raw END AS p_raw_pareada,
            CASE WHEN p_raw BETWEEN 0 AND 1 AND p_efectiva BETWEEN 0 AND 1
                 THEN p_efectiva END AS p_efectiva_pareada
       FROM public.vista_predicciones_para_calibracion
   ) pares
  GROUP BY mercado, origen
  ORDER BY mercado, origen;

COMMIT;
