-- Evidencia separada de las capturas FT originales. Ejecutar solo explícitamente.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
CREATE TABLE observaciones_tiempos_espn_futbol (
    liga text NOT NULL,
    id_fuente text NOT NULL,
    partido_id uuid NOT NULL REFERENCES partidos_futbol(id),
    observado_en timestamptz NOT NULL,
    sha256_payload char(64) NOT NULL CHECK (sha256_payload ~ '^[0-9a-f]{64}$'),
    contrato text NOT NULL CHECK (contrato = 'ESPN_REGULATION_TWO_HALVES_EXPLICIT_LINESCORES_V1'),
    evidencia jsonb NOT NULL,
    registrado_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (liga,id_fuente,sha256_payload),
    FOREIGN KEY (liga,id_fuente) REFERENCES partidos_fuente_espn_futbol(liga,id_fuente)
);
COMMIT;
