-- ===========================================================================
-- Migración: Idempotencia y trazabilidad para alertas_calibracion
-- ===========================================================================
--
-- Agrega columnas de periodo y modelo_version_id para llave natural.
-- Crea columna GENERATED para modelo_version_id_efectivo y constraint único.
--
-- EJECUTAR CON:
--   psql -U tu_usuario -d tu_bd -f migracion_alertas_calibracion.sql
-- ===========================================================================

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Iniciando migración para alertas_calibracion...';
END $$;

ALTER TABLE alertas_calibracion
ADD COLUMN IF NOT EXISTS periodo_inicio DATE,
ADD COLUMN IF NOT EXISTS periodo_fin DATE,
ADD COLUMN IF NOT EXISTS modelo_version_id INTEGER;

ALTER TABLE alertas_calibracion
ADD COLUMN IF NOT EXISTS modelo_version_id_efectivo INTEGER
GENERATED ALWAYS AS (COALESCE(modelo_version_id, -1)) STORED;

ALTER TABLE alertas_calibracion
DROP CONSTRAINT IF EXISTS uq_alerta_calibracion_llave_natural;

ALTER TABLE alertas_calibracion
ADD CONSTRAINT uq_alerta_calibracion_llave_natural
UNIQUE (periodo_inicio, periodo_fin, mercado, origen, tipo_alerta, modelo_version_id_efectivo);

CREATE INDEX IF NOT EXISTS idx_alertas_calibracion_busqueda
ON alertas_calibracion (mercado, origen, severidad, resuelta);

COMMIT;

-- ===========================================================================
-- ROLLBACK (si es necesario):
--
-- BEGIN;
-- ALTER TABLE alertas_calibracion DROP CONSTRAINT IF EXISTS uq_alerta_calibracion_llave_natural;
-- ALTER TABLE alertas_calibracion DROP COLUMN IF EXISTS modelo_version_id_efectivo;
-- ALTER TABLE alertas_calibracion DROP COLUMN IF EXISTS modelo_version_id;
-- ALTER TABLE alertas_calibracion DROP COLUMN IF EXISTS periodo_inicio;
-- ALTER TABLE alertas_calibracion DROP COLUMN IF EXISTS periodo_fin;
-- COMMIT;
-- ===========================================================================
