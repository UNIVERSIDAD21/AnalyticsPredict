-- Almacén paralelo: no modifica predicciones, apuestas ni outcomes históricos.
BEGIN;
SET LOCAL lock_timeout='5s';
SET LOCAL statement_timeout='30s';
CREATE TABLE predicciones_prospectivas (
    id uuid PRIMARY KEY,
    clave text NOT NULL UNIQUE,
    inicio_utc timestamptz NOT NULL,
    fit_completed_at timestamptz NOT NULL,
    congelado_en timestamptz NOT NULL DEFAULT clock_timestamp(),
    sha256 char(64) NOT NULL,
    snapshot jsonb NOT NULL,
    CHECK (fit_completed_at < congelado_en AND congelado_en < inicio_utc)
);
CREATE TABLE outcomes_prospectivos (
    prediccion_id uuid PRIMARY KEY REFERENCES predicciones_prospectivas(id),
    registrado_en timestamptz NOT NULL DEFAULT clock_timestamp(),
    sha256 char(64) NOT NULL,
    evidencia jsonb NOT NULL
);
CREATE FUNCTION impedir_cambio_prospectivo() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Registro prospectivo inmutable: reconciliar con evidencia separada';
END; $$;
CREATE TRIGGER prediccion_inmutable BEFORE UPDATE OR DELETE OR TRUNCATE ON predicciones_prospectivas
    FOR EACH STATEMENT EXECUTE FUNCTION impedir_cambio_prospectivo();
CREATE TRIGGER outcome_inmutable BEFORE UPDATE OR DELETE OR TRUNCATE ON outcomes_prospectivos
    FOR EACH STATEMENT EXECUTE FUNCTION impedir_cambio_prospectivo();
COMMIT;
