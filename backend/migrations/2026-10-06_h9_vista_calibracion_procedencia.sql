-- H9: la vista NBA solo usa p_calibrada con calibrador_id verificable.
-- CREATE OR REPLACE conserva columnas, tipos, permisos y dependencias.
-- Definición cotejada read-only con Neon el 2026-10-06; no altera filas.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE OR REPLACE VIEW public.vista_predicciones_para_calibracion AS
 SELECT pr.id,
    pr.timestamp_generacion,
    pr.origen,
    pr.modelo_version_id,
    pr.calibrador_id,
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
    pr.p_calibrada,
    pr.calibrador_metodo,
    pr.valor_real,
    pr.outcome_binario,
    pr.timestamp_resolucion,
    pr.resuelto,
    pr.creado_en,
    pr.actualizado_en,
    floor(pr.p_raw * 10::numeric) / 10::numeric AS bin_p_raw,
    floor(COALESCE(CASE WHEN pr.calibrador_id IS NOT NULL THEN pr.p_calibrada END,
                   pr.p_raw) * 10::numeric) / 10::numeric AS bin_p_efectiva,
    COALESCE(CASE WHEN pr.calibrador_id IS NOT NULL THEN pr.p_calibrada END,
             pr.p_raw) AS p_efectiva,
    el.nombre AS local_nombre,
    el.abreviatura AS local_abr,
    ev.nombre AS visitante_nombre,
    ev.abreviatura AS visitante_abr,
    t.nombre AS temporada_nombre
   FROM predicciones_registradas pr
     JOIN equipos el ON pr.equipo_local_id = el.id
     JOIN equipos ev ON pr.equipo_visitante_id = ev.id
     LEFT JOIN temporadas_baloncesto t ON pr.temporada_id = t.id
  WHERE pr.resuelto = true AND pr.outcome_binario IS NOT NULL;

COMMIT;
