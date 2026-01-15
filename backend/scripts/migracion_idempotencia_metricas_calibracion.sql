-- ===========================================================================
-- Migración: Idempotencia real para metricas_calibracion con modelo_version_id NULL
-- ===========================================================================
--
-- OBJETIVO:
-- Evitar duplicados cuando modelo_version_id es NULL mediante columna GENERATED
-- y constraint único nombrado.
--
-- EJECUTAR CON:
--   psql -U tu_usuario -d tu_bd -f migracion_idempotencia_metricas_calibracion.sql
-- ===========================================================================

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Iniciando migración de idempotencia para metricas_calibracion...';
END $$;

-- Paso 1: Agregar columna auxiliar efectiva para modelo_version_id
ALTER TABLE metricas_calibracion
ADD COLUMN IF NOT EXISTS modelo_version_id_efectivo INTEGER
GENERATED ALWAYS AS (COALESCE(modelo_version_id, -1)) STORED;

-- Paso 2: Eliminar constraint previo si existe
ALTER TABLE metricas_calibracion
DROP CONSTRAINT IF EXISTS uq_metricas_calibracion_llave_natural;

-- Paso 3: Deduplicar filas existentes usando llave natural efectiva
WITH duplicados AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY
                periodo_inicio,
                periodo_fin,
                mercado,
                origen_predicciones,
                modelo_version_id_efectivo
            ORDER BY
                timestamp_calculo DESC NULLS LAST,
                id DESC
        ) AS rn
    FROM metricas_calibracion
)
DELETE FROM metricas_calibracion AS m
USING duplicados AS d
WHERE m.id = d.id
  AND d.rn > 1;

-- Paso 3: Crear constraint único con nombre explícito
ALTER TABLE metricas_calibracion
ADD CONSTRAINT uq_metricas_calibracion_llave_natural
UNIQUE (periodo_inicio, periodo_fin, mercado, origen_predicciones, modelo_version_id_efectivo);

-- Paso 4: Índice auxiliar para búsquedas
CREATE INDEX IF NOT EXISTS idx_metricas_calibracion_busqueda
ON metricas_calibracion (mercado, origen_predicciones, periodo_inicio, periodo_fin);

DO $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM pg_constraint
    WHERE conname = 'uq_metricas_calibracion_llave_natural';

    IF v_count = 1 THEN
        RAISE NOTICE 'Constraint uq_metricas_calibracion_llave_natural creado.';
    ELSE
        RAISE EXCEPTION 'Error creando constraint uq_metricas_calibracion_llave_natural.';
    END IF;
END $$;

COMMIT;

-- ===========================================================================
-- ROLLBACK (si es necesario):
--
-- BEGIN;
-- ALTER TABLE metricas_calibracion DROP CONSTRAINT IF EXISTS uq_metricas_calibracion_llave_natural;
-- ALTER TABLE metricas_calibracion DROP COLUMN IF EXISTS modelo_version_id_efectivo;
-- COMMIT;
-- ===========================================================================
