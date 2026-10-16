-- Identidades acreditadas y procedencia ESPN sin reutilizar IDs Sofascore/API-Football.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
CREATE TABLE IF NOT EXISTS equipos_fuente_espn_futbol (
    id_fuente text PRIMARY KEY,
    equipo_id uuid NOT NULL UNIQUE REFERENCES equipos_futbol(id),
    evidencia jsonb NOT NULL,
    verificado_en timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS temporadas_fuente_espn_futbol (
    liga text NOT NULL,
    anio integer NOT NULL,
    temporada_id uuid NOT NULL UNIQUE REFERENCES temporadas_futbol(id),
    evidencia jsonb NOT NULL,
    PRIMARY KEY(liga,anio)
);
CREATE TABLE IF NOT EXISTS partidos_fuente_espn_futbol (
    liga text NOT NULL,
    id_fuente text NOT NULL,
    partido_id uuid NOT NULL UNIQUE REFERENCES partidos_futbol(id),
    sha256_evento char(64) NOT NULL,
    observado_en timestamptz NOT NULL,
    evidencia jsonb NOT NULL,
    PRIMARY KEY(liga,id_fuente)
);
COMMIT;
