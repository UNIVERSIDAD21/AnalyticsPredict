-- Calendario WNBA sin resultados ficticios. Aplicar con respaldo y ensayo.
CREATE TABLE IF NOT EXISTS fixtures_wnba (
 id uuid PRIMARY KEY,
 competicion_id uuid NOT NULL REFERENCES competiciones_baloncesto(id),
 temporada_id uuid NOT NULL REFERENCES temporadas_baloncesto(id),
 equipo_local_id uuid NOT NULL REFERENCES equipos(id),
 equipo_visitante_id uuid NOT NULL REFERENCES equipos(id),
 source_game_id text NOT NULL UNIQUE,
 inicio_utc timestamptz,
 fecha_local date,
 precision_fecha text NOT NULL CHECK (precision_fecha IN ('HORA','DIA','PENDIENTE')),
 estado text NOT NULL CHECK (estado IN ('PROGRAMADO','EN_VIVO','POSPUESTO','CANCELADO','DEMORADO','SUSPENDIDO','FINALIZADO')),
 fase text NOT NULL CHECK (fase IN ('PRE','REG','POST','COPA')),
 resultado_id uuid UNIQUE REFERENCES partidos_baloncesto(id),
 revision_sha256 text NOT NULL,
 registro jsonb NOT NULL,
 creado_en timestamptz NOT NULL DEFAULT now(),
 actualizado_en timestamptz NOT NULL DEFAULT now(),
 CHECK(equipo_local_id <> equipo_visitante_id),
 CHECK((precision_fecha = 'HORA') = (inicio_utc IS NOT NULL)),
 CHECK(resultado_id IS NULL OR estado='FINALIZADO')
);
CREATE INDEX IF NOT EXISTS fixtures_wnba_fecha ON fixtures_wnba(fecha_local,estado);
CREATE TABLE IF NOT EXISTS revisiones_fixtures_wnba (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 fixture_id uuid NOT NULL REFERENCES fixtures_wnba(id),
 sha256 text NOT NULL,
 registro jsonb NOT NULL,
 observado_utc timestamptz NOT NULL,
 procedencia jsonb NOT NULL,
 UNIQUE(fixture_id,sha256)
);
CREATE TABLE IF NOT EXISTS comprobaciones_calendario_wnba (
 id uuid PRIMARY KEY,
 desde date NOT NULL,
 hasta date NOT NULL,
 comprobado_utc timestamptz NOT NULL,
 reporte jsonb NOT NULL,
 CHECK(hasta>=desde)
);
ALTER TABLE apuestas ADD COLUMN IF NOT EXISTS fixture_wnba_id uuid REFERENCES fixtures_wnba(id);
CREATE INDEX IF NOT EXISTS apuestas_fixture_wnba ON apuestas(fixture_wnba_id) WHERE fixture_wnba_id IS NOT NULL;
