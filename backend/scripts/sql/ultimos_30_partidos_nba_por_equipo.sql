-- Últimos partidos NBA por equipo, con splits general/local/visitante.
-- Cambia :limite por 5, 10, 20 o 30 según el corte requerido.
WITH nba AS (
  SELECT id FROM competiciones_baloncesto WHERE lower(codigo) = 'nba' LIMIT 1
), apariciones AS (
  SELECT
    e.id AS equipo_id,
    e.abreviatura,
    e.nombre AS equipo,
    p.id AS partido_id,
    p.fecha_partido,
    'LOCAL' AS localia,
    p.tipo_partido,
    p.local_q1 AS puntos_q1, p.local_q2 AS puntos_q2, p.local_q3 AS puntos_q3, p.local_q4 AS puntos_q4,
    p.local_total AS puntos_total,
    p.visitante_q1 AS recibidos_q1, p.visitante_q2 AS recibidos_q2, p.visitante_q3 AS recibidos_q3, p.visitante_q4 AS recibidos_q4,
    p.visitante_total AS recibidos_total,
    p.hubo_overtime,
    p.source,
    p.source_game_id
  FROM partidos_baloncesto p
  JOIN equipos e ON e.id = p.equipo_local_id
  JOIN nba ON nba.id = p.competicion_id
  UNION ALL
  SELECT
    e.id AS equipo_id,
    e.abreviatura,
    e.nombre AS equipo,
    p.id AS partido_id,
    p.fecha_partido,
    'VISITANTE' AS localia,
    p.tipo_partido,
    p.visitante_q1, p.visitante_q2, p.visitante_q3, p.visitante_q4,
    p.visitante_total,
    p.local_q1, p.local_q2, p.local_q3, p.local_q4,
    p.local_total,
    p.hubo_overtime,
    p.source,
    p.source_game_id
  FROM partidos_baloncesto p
  JOIN equipos e ON e.id = p.equipo_visitante_id
  JOIN nba ON nba.id = p.competicion_id
), ranked AS (
  SELECT *,
    row_number() OVER (PARTITION BY equipo_id ORDER BY fecha_partido DESC, partido_id DESC) AS rn_general,
    row_number() OVER (PARTITION BY equipo_id, localia ORDER BY fecha_partido DESC, partido_id DESC) AS rn_localia
  FROM apariciones
)
SELECT *
FROM ranked
WHERE rn_general <= :limite OR rn_localia <= :limite
ORDER BY equipo, fecha_partido DESC;
