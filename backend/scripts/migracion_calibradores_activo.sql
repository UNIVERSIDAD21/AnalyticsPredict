-- ===========================================================================
-- Migración: Un solo calibrador activo por mercado
-- ===========================================================================
--
-- EJECUTAR CON:
--   psql -U tu_usuario -d tu_bd -f migracion_calibradores_activo.sql
-- ===========================================================================

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Creando constraint único para calibradores activos...';
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_calibradores_activo_mercado
ON calibradores (mercado)
WHERE activo;

COMMIT;

-- ===========================================================================
-- ROLLBACK (si es necesario):
--
-- BEGIN;
-- DROP INDEX IF EXISTS uq_calibradores_activo_mercado;
-- COMMIT;
-- ===========================================================================
