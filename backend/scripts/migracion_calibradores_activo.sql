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

-- Normalizar calibradores activos: dejar solo el más reciente por mercado
WITH ranking AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY mercado
            ORDER BY fecha_entrenamiento DESC NULLS LAST, id DESC
        ) AS rn
    FROM calibradores
    WHERE activo = true
)
UPDATE calibradores
SET activo = false
WHERE id IN (SELECT id FROM ranking WHERE rn > 1);

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
