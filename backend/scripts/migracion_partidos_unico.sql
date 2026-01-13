ALTER TABLE partidos
ADD CONSTRAINT partidos_llave_natural_unica
UNIQUE (fecha_partido, equipo_local_id, equipo_visitante_id, tipo_partido);
