-- ============================================================================
-- ROLLBACK: BALONCESTO MULTI-COMPETICION -> MODO NBA MONOLITICO
-- ============================================================================
-- Este rollback revierte de forma segura a modo NBA:
-- - Elimina datos no-NBA en tablas de baloncesto.
-- - Restaura restricciones legacy de equipos (conferencia/division obligatorias).
-- - Restaura unique de temporadas por nombre global.
--
-- Nota:
-- - No elimina tablas nuevas para no romper dependencias de la aplicacion.
-- - Se conserva competiciones_baloncesto con NBA activa.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    v_nba uuid;
BEGIN
    SELECT id INTO v_nba
    FROM public.competiciones_baloncesto
    WHERE codigo = 'nba'
    LIMIT 1;

    IF v_nba IS NULL THEN
        RAISE EXCEPTION 'No existe competicion NBA (codigo=nba). No se puede rollback.';
    END IF;

    -- ----------------------------------------------------------------------
    -- 1) Limpiar datos de competiciones no-NBA (hijos -> padres)
    -- ----------------------------------------------------------------------
    IF to_regclass('public.apuestas') IS NOT NULL THEN
        DELETE FROM public.apuestas
        WHERE competicion_id IS NOT NULL
          AND competicion_id <> v_nba;

        UPDATE public.apuestas
        SET competicion_id = v_nba,
            competicion_nombre = 'NBA'
        WHERE competicion_id IS NULL;
    END IF;

    IF to_regclass('public.predicciones_registradas') IS NOT NULL THEN
        DELETE FROM public.predicciones_registradas
        WHERE competicion_id <> v_nba;

        UPDATE public.predicciones_registradas
        SET competicion_id = v_nba
        WHERE competicion_id IS NULL;
    END IF;

    IF to_regclass('public.partidos_baloncesto') IS NOT NULL THEN
        DELETE FROM public.partidos_baloncesto
        WHERE competicion_id <> v_nba;

        UPDATE public.partidos_baloncesto
        SET competicion_id = v_nba,
            sofascore_match_id = NULL
        WHERE competicion_id IS NULL;
    END IF;

    IF to_regclass('public.temporadas_baloncesto') IS NOT NULL THEN
        DELETE FROM public.temporadas_baloncesto
        WHERE competicion_id <> v_nba;

        UPDATE public.temporadas_baloncesto
        SET competicion_id = v_nba,
            sofascore_season_id = NULL
        WHERE competicion_id IS NULL;
    END IF;

    IF to_regclass('public.equipos_baloncesto') IS NOT NULL THEN
        DELETE FROM public.equipos_baloncesto
        WHERE competicion_principal_id IS NOT NULL
          AND competicion_principal_id <> v_nba;

        UPDATE public.equipos_baloncesto
        SET competicion_principal_id = v_nba,
            sofascore_id = NULL
        WHERE competicion_principal_id IS NULL
           OR competicion_principal_id = v_nba;
    END IF;

    IF to_regclass('public.ingestion_state_baloncesto') IS NOT NULL THEN
        DELETE FROM public.ingestion_state_baloncesto
        WHERE competicion_id IS NOT NULL
          AND competicion_id <> v_nba;

        DELETE FROM public.ingestion_state_baloncesto
        WHERE clave = 'euroliga_sync';
    END IF;

    -- ----------------------------------------------------------------------
    -- 2) Competiciones: solo NBA activa
    -- ----------------------------------------------------------------------
    UPDATE public.competiciones_baloncesto
    SET activo = CASE WHEN id = v_nba THEN true ELSE false END,
        sofascore_id = CASE WHEN id = v_nba THEN NULL ELSE sofascore_id END,
        actualizado_en = now();

    -- valor historico pre-migracion en este entorno: 7
    UPDATE public.competiciones_baloncesto
    SET sofascore_id = 7,
        activo = false,
        actualizado_en = now()
    WHERE codigo = 'euroleague';

    -- ----------------------------------------------------------------------
    -- 3) Restaurar unique global en temporadas (legacy)
    -- ----------------------------------------------------------------------
    IF to_regclass('public.temporadas_baloncesto') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_temporada_baloncesto_competicion'
              AND conrelid = 'public.temporadas_baloncesto'::regclass
        ) THEN
            ALTER TABLE public.temporadas_baloncesto
                DROP CONSTRAINT uq_temporada_baloncesto_competicion;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'temporadas_nombre_key'
              AND conrelid = 'public.temporadas_baloncesto'::regclass
        ) THEN
            ALTER TABLE public.temporadas_baloncesto
                ADD CONSTRAINT temporadas_nombre_key UNIQUE (nombre);
        END IF;
    END IF;

    -- ----------------------------------------------------------------------
    -- 4) Restaurar restricciones legacy de equipos
    -- ----------------------------------------------------------------------
    IF to_regclass('public.equipos') IS NOT NULL THEN
        UPDATE public.equipos
        SET competicion_principal_id = v_nba
        WHERE competicion_principal_id IS NULL;

        UPDATE public.equipos
        SET sofascore_id = NULL;

        UPDATE public.equipos
        SET conferencia = 'Este'
        WHERE conferencia IS NULL;

        UPDATE public.equipos
        SET division = 'Sin division'
        WHERE division IS NULL OR btrim(division) = '';

        IF EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'equipos_conferencia_nullable_check'
              AND conrelid = 'public.equipos'::regclass
        ) THEN
            ALTER TABLE public.equipos
                DROP CONSTRAINT equipos_conferencia_nullable_check;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'equipos_conferencia_check'
              AND conrelid = 'public.equipos'::regclass
        ) THEN
            ALTER TABLE public.equipos
                ADD CONSTRAINT equipos_conferencia_check
                CHECK (conferencia IN ('Este', 'Oeste'));
        END IF;

        ALTER TABLE public.equipos
            ALTER COLUMN conferencia SET NOT NULL;
        ALTER TABLE public.equipos
            ALTER COLUMN division SET NOT NULL;
    END IF;
END $$;

COMMIT;

