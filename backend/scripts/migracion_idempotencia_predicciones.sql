-- ===========================================================================
-- Migración: Crear constraint único nombrado para idempotencia de predicciones
-- ===========================================================================
--
-- PROBLEMA:
-- El índice idx_pred_llave_natural usa COALESCE, que es un índice funcional.
-- Postgres NO puede inferir índices funcionales en ON CONFLICT.
--
-- SOLUCIÓN:
-- 1. Eliminar el índice existente
-- 2. Crear un UNIQUE CONSTRAINT con nombre explícito
-- 3. El código usará ON CONFLICT ON CONSTRAINT nombre_constraint
--
-- EJECUTAR CON:
--   psql -U tu_usuario -d tu_bd -f migracion_idempotencia_predicciones.sql
-- ===========================================================================

BEGIN;

-- Verificar estado actual
DO $$
BEGIN
    RAISE NOTICE 'Iniciando migración de idempotencia para predicciones_registradas...';
END $$;

-- Paso 1: Eliminar el índice funcional existente (si existe)
DROP INDEX IF EXISTS idx_pred_llave_natural;

-- Paso 2: Agregar columna auxiliar para calibrador_id (evita COALESCE en constraint)
-- Si calibrador_id es NULL, usamos UUID vacío para mantener unicidad
ALTER TABLE predicciones_registradas
ADD COLUMN IF NOT EXISTS calibrador_id_efectivo UUID
GENERATED ALWAYS AS (COALESCE(calibrador_id, '00000000-0000-0000-0000-000000000000'::uuid)) STORED;

-- Paso 3: Crear el constraint único con nombre explícito
-- Usamos la columna generada en lugar de expresión COALESCE
ALTER TABLE predicciones_registradas
DROP CONSTRAINT IF EXISTS uq_prediccion_llave_natural;

ALTER TABLE predicciones_registradas
ADD CONSTRAINT uq_prediccion_llave_natural
UNIQUE (partido_id, mercado, lado, linea, origen, modelo_version_id, calibrador_id_efectivo);

-- Paso 4: Crear índice para búsquedas rápidas (opcional pero recomendado)
CREATE INDEX IF NOT EXISTS idx_pred_llave_busqueda
ON predicciones_registradas (partido_id, mercado, lado, linea, origen);

-- Verificar resultado
DO $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM pg_constraint
    WHERE conname = 'uq_prediccion_llave_natural';

    IF v_count = 1 THEN
        RAISE NOTICE 'Migración completada exitosamente. Constraint uq_prediccion_llave_natural creado.';
    ELSE
        RAISE EXCEPTION 'Error: No se pudo crear el constraint';
    END IF;
END $$;

COMMIT;

-- ===========================================================================
-- ROLLBACK (en caso de necesitar revertir):
--
-- BEGIN;
-- ALTER TABLE predicciones_registradas DROP CONSTRAINT IF EXISTS uq_prediccion_llave_natural;
-- ALTER TABLE predicciones_registradas DROP COLUMN IF EXISTS calibrador_id_efectivo;
-- -- Recrear índice original si es necesario
-- CREATE UNIQUE INDEX idx_pred_llave_natural
-- ON predicciones_registradas (
--     partido_id, mercado, lado, linea, origen, modelo_version_id,
--     COALESCE(calibrador_id, '00000000-0000-0000-0000-000000000000'::uuid)
-- );
-- COMMIT;
-- ===========================================================================
