-- Migración destructiva single-user. Aplicar solamente tras backup pg_dump
-- verificado y con la aplicación detenida. Probada primero sobre restauración aislada.
-- La cuenta con más actividad aporta la configuración; por instrucción posterior
-- del Jefe, todos los registros deportivos se muestran como histórico personal.
-- La procedencia anterior queda en el backup, no en el esquema activo.

BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $$
DECLARE
  ganador uuid := '00000000-0000-0000-0000-000000000001';
  total_ganador bigint;
  total_segundo bigint;
BEGIN
  SELECT count(*) INTO total_ganador FROM usuarios WHERE id = ganador;
  IF total_ganador <> 1 THEN
    RAISE EXCEPTION 'El histórico ganador no existe exactamente una vez';
  END IF;
  WITH actividad AS (
    SELECT u.id,
      (SELECT count(*) FROM apuestas a WHERE a.usuario_id = u.id) +
      (SELECT count(*) FROM apuestas_futbol a WHERE a.usuario_id = u.id) +
      (SELECT count(*) FROM apuestas_combinadas a WHERE a.usuario_id = u.id) +
      (SELECT count(*) FROM selecciones_combinada s
         JOIN apuestas_combinadas ac ON ac.id = s.combinada_id WHERE ac.usuario_id = u.id) AS n
    FROM usuarios u
  )
  SELECT n INTO total_ganador FROM actividad WHERE id = ganador;
  WITH actividad AS (
    SELECT u.id,
      (SELECT count(*) FROM apuestas a WHERE a.usuario_id = u.id) +
      (SELECT count(*) FROM apuestas_futbol a WHERE a.usuario_id = u.id) +
      (SELECT count(*) FROM apuestas_combinadas a WHERE a.usuario_id = u.id) +
      (SELECT count(*) FROM selecciones_combinada s
         JOIN apuestas_combinadas ac ON ac.id = s.combinada_id WHERE ac.usuario_id = u.id) AS n
    FROM usuarios u
  )
  SELECT coalesce(max(n), -1) INTO total_segundo FROM actividad WHERE id <> ganador;
  IF total_ganador <= total_segundo THEN
    RAISE EXCEPTION 'El UUID esperado no es ganador único: % frente a %', total_ganador, total_segundo;
  END IF;
END $$;

CREATE TEMP TABLE single_user_expected ON COMMIT DROP AS
SELECT
  (SELECT count(*) FROM apuestas) AS apuestas,
  (SELECT count(*) FROM apuestas_futbol) AS futbol,
  (SELECT count(*) FROM apuestas_combinadas) AS combinadas,
  (SELECT count(*) FROM selecciones_combinada) AS selecciones,
  (SELECT count(*) FROM apuestas_analizadas) AS analizadas,
  (SELECT count(*) FROM predicciones_registradas) AS predicciones_nba,
  (SELECT count(*) FROM predicciones_futbol) AS predicciones_futbol,
  (SELECT count(*) FROM partidos_baloncesto) AS partidos_nba,
  (SELECT count(*) FROM partidos_futbol) AS partidos_futbol
FROM usuarios u WHERE u.id = '00000000-0000-0000-0000-000000000001';

CREATE TABLE configuracion_sistema (
  id boolean PRIMARY KEY DEFAULT true CHECK (id),
  preferencias jsonb,
  bankroll_inicial numeric,
  bankroll_actual numeric,
  perfil_riesgo_default varchar,
  config_sizing jsonb,
  actualizado_en timestamptz NOT NULL DEFAULT now()
);
INSERT INTO configuracion_sistema (
  id, preferencias, bankroll_inicial, bankroll_actual, perfil_riesgo_default, config_sizing
)
SELECT true, preferencias, bankroll_inicial, bankroll_actual, perfil_riesgo_default, config_sizing
FROM usuarios WHERE id = '00000000-0000-0000-0000-000000000001';

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM single_user_expected e WHERE
      (SELECT count(*) FROM apuestas) <> e.apuestas OR
      (SELECT count(*) FROM apuestas_futbol) <> e.futbol OR
      (SELECT count(*) FROM apuestas_combinadas) <> e.combinadas OR
      (SELECT count(*) FROM selecciones_combinada) <> e.selecciones) THEN
    RAISE EXCEPTION 'No coinciden los conteos del histórico completo';
  END IF;
END $$;

DROP VIEW vista_resumen_por_tipo_apuesta;
DROP VIEW vista_bitacora_unificada;
DROP VIEW vista_analisis_apuestas;
DROP VIEW vista_resumen_apuestas;
DROP VIEW vista_resumen_apuestas_futbol;

ALTER TABLE apuestas DROP COLUMN usuario_id;
ALTER TABLE apuestas_futbol DROP COLUMN usuario_id;
ALTER TABLE apuestas_combinadas DROP COLUMN usuario_id;

DROP TABLE onboarding_events;
DROP TABLE onboarding_profiles;
DROP TABLE payment_events;
DROP TABLE payment_intents;
DROP TABLE subscriptions;
DROP TABLE auth_reset_tokens_v2;
DROP TABLE auth_reset_tokens;
DROP TABLE auth_revoked_tokens;
DROP TABLE auth_users;
DROP TABLE usuarios;

-- Vistas analíticas conservadas sin identidad de cuenta.
CREATE VIEW vista_analisis_apuestas AS
SELECT a.*,
  CASE WHEN a.devig_overround IS NOT NULL THEN round((a.devig_overround - 1) * 100, 2) END AS vig_porcentaje,
  round((a.probabilidad_sistema - coalesce(a.devig_p_mkt_raw, 1 / nullif(a.cuota, 0))) * 100, 2) AS edge_raw_porcentaje,
  round(coalesce(a.edge_real, 0) * 100, 2) AS edge_real_porcentaje,
  CASE WHEN a.bankroll_momento > 0 THEN round(a.stake / a.bankroll_momento * 100, 2) END AS stake_porcentaje_real,
  CASE WHEN a.stake > 0 THEN round(coalesce(a.ganancia, 0) / a.stake * 100, 2) END AS roi_porcentaje,
  CASE WHEN a.score_total IS NULL THEN 'SIN_SCORE'
       WHEN a.score_total >= 5 THEN 'EXCELENTE'
       WHEN a.score_total >= 3 THEN 'BUENA'
       WHEN a.score_total >= 1 THEN 'ACEPTABLE'
       WHEN a.score_total > 0 THEN 'MARGINAL' ELSE 'NO_APTA' END AS clasificacion_calidad
FROM apuestas a;

CREATE VIEW vista_bitacora_unificada AS
SELECT a.id, 'SIMPLE'::text AS tipo_apuesta, NULL::uuid AS combinada_id,
  a.equipo_local, a.equipo_visitante, a.fecha_partido, a.mercado, a.lado,
  a.linea, a.cuota, a.stake, a.probabilidad_sistema, a.confianza_sistema,
  a.valor_esperado, a.resultado, a.ganancia, 1 AS n_selecciones,
  NULL::integer AS selecciones_ganadas, NULL::integer AS selecciones_perdidas,
  NULL::boolean AS tiene_correlacion, a.creado_en, a.fecha_resolucion
FROM apuestas a
UNION ALL
SELECT ac.id, 'COMBINADA'::text, ac.id,
  (SELECT string_agg(DISTINCT s.equipo_local || ' vs ' || s.equipo_visitante, ' | ')
   FROM selecciones_combinada s WHERE s.combinada_id = ac.id),
  NULL::varchar, (SELECT min(s.fecha_partido) FROM selecciones_combinada s WHERE s.combinada_id = ac.id),
  'PARLAY'::varchar, NULL::varchar, NULL::numeric, ac.cuota_total, ac.stake,
  ac.probabilidad_ajustada, ac.confianza_sistema, ac.valor_esperado, ac.resultado,
  ac.ganancia, ac.n_selecciones, ac.selecciones_ganadas, ac.selecciones_perdidas,
  ac.tiene_mismo_partido, ac.creado_en, ac.fecha_resolucion
FROM apuestas_combinadas ac;

CREATE VIEW vista_resumen_apuestas AS
SELECT count(*) AS total_apuestas,
  count(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
  count(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
  count(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
  count(*) FILTER (WHERE resultado = 'PUSH') AS push,
  round(100.0 * count(*) FILTER (WHERE resultado = 'GANADA') /
    nullif(count(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')), 0), 2) AS winrate,
  sum(ganancia) AS ganancia_total,
  sum(stake) FILTER (WHERE resultado <> 'PENDIENTE') AS total_apostado,
  round(100.0 * sum(ganancia) /
    nullif(sum(stake) FILTER (WHERE resultado <> 'PENDIENTE'), 0), 2) AS roi
FROM apuestas;

CREATE VIEW vista_resumen_apuestas_futbol AS
SELECT mercado, count(*) AS total_apuestas,
  count(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
  count(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
  count(*) FILTER (WHERE resultado = 'PUSH') AS push,
  count(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
  round(100.0 * count(*) FILTER (WHERE resultado = 'GANADA') /
    nullif(count(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')), 0), 2) AS win_rate,
  sum(stake) AS stake_total, sum(ganancia) AS ganancia_total,
  round(100.0 * sum(ganancia) / nullif(sum(stake), 0), 2) AS roi
FROM apuestas_futbol GROUP BY mercado;

CREATE VIEW vista_resumen_por_tipo_apuesta AS
SELECT tipo_apuesta, count(*) AS total_apuestas,
  count(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
  count(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
  count(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
  round(100.0 * count(*) FILTER (WHERE resultado = 'GANADA') /
    nullif(count(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')), 0), 2) AS winrate,
  sum(ganancia) AS ganancia_total
FROM vista_bitacora_unificada GROUP BY tipo_apuesta;

DO $$ BEGIN
  IF (SELECT count(*) FROM configuracion_sistema) <> 1 OR
     EXISTS (SELECT 1 FROM single_user_expected e WHERE
       (SELECT count(*) FROM vista_bitacora_unificada) <> e.apuestas + e.combinadas OR
       (SELECT count(*) FROM apuestas_analizadas) <> e.analizadas OR
       (SELECT count(*) FROM predicciones_registradas) <> e.predicciones_nba OR
       (SELECT count(*) FROM predicciones_futbol) <> e.predicciones_futbol OR
       (SELECT count(*) FROM partidos_baloncesto) <> e.partidos_nba OR
       (SELECT count(*) FROM partidos_futbol) <> e.partidos_futbol) OR
     EXISTS (SELECT 1 FROM information_schema.columns
       WHERE table_schema = 'public' AND column_name IN ('usuario_id', 'user_id', 'auth_user_id')) THEN
    RAISE EXCEPTION 'Validación de esquema single-user falló';
  END IF;
END $$;
COMMIT;
