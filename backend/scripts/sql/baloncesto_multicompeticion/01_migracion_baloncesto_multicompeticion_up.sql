-- ============================================================================
-- MIGRACION: BALONCESTO MULTI-COMPETICION (NBA + EUROLIGA)
-- ============================================================================
-- Objetivo:
-- - Mantener compatibilidad total con NBA/ESPN.
-- - Habilitar Euroliga/Sofascore con competicion_id y sofascore_match_id.
-- - Migrar catalogo NBA historico a equipos_baloncesto.
--
-- Script idempotente: se puede ejecutar varias veces.
-- ============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- --------------------------------------------------------------------------
-- 0) Renombrar paises_futbol -> paises (si aplica)
-- --------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.paises') IS NULL
       AND to_regclass('public.paises_futbol') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE public.paises_futbol RENAME TO paises';
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 1) ENUM de tipo de competicion de baloncesto
-- --------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'public'
          AND t.typname = 'tipo_competicion_baloncesto'
    ) THEN
        EXECUTE $sql$
            CREATE TYPE public.tipo_competicion_baloncesto AS ENUM (
                'LIGA_PROFESIONAL',
                'EUROLIGA',
                'EUROCUP',
                'COPA_NACIONAL',
                'TORNEO_INTERNACIONAL',
                'PRETEMPORADA',
                'PLAY_IN'
            )
        $sql$;
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 2) Tabla competiciones_baloncesto
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.competiciones_baloncesto (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre varchar(120) NOT NULL,
    nombre_corto varchar(60) NOT NULL,
    codigo varchar(40) NOT NULL,
    tipo public.tipo_competicion_baloncesto NOT NULL DEFAULT 'LIGA_PROFESIONAL',
    pais_id uuid NULL,
    n_equipos integer NULL,
    formato_competicion varchar(50) NULL,
    tiene_playoffs boolean DEFAULT true,
    sofascore_id integer NULL,
    espn_league_id varchar(50) NULL,
    api_basketball_id integer NULL,
    activo boolean DEFAULT true,
    prioridad integer DEFAULT 100,
    creado_en timestamptz DEFAULT now(),
    actualizado_en timestamptz DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'competiciones_baloncesto_codigo_key'
          AND conrelid = 'public.competiciones_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.competiciones_baloncesto
            ADD CONSTRAINT competiciones_baloncesto_codigo_key UNIQUE (codigo);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_competiciones_baloncesto_codigo
    ON public.competiciones_baloncesto (codigo);
CREATE INDEX IF NOT EXISTS idx_competiciones_baloncesto_tipo
    ON public.competiciones_baloncesto (tipo);
CREATE INDEX IF NOT EXISTS idx_competiciones_baloncesto_activo
    ON public.competiciones_baloncesto (activo);
CREATE INDEX IF NOT EXISTS idx_competiciones_baloncesto_sofascore
    ON public.competiciones_baloncesto (sofascore_id)
    WHERE sofascore_id IS NOT NULL;

DO $$
BEGIN
    IF to_regclass('public.paises') IS NOT NULL
       AND NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'competiciones_baloncesto_pais_id_fkey'
              AND conrelid = 'public.competiciones_baloncesto'::regclass
       ) THEN
        ALTER TABLE public.competiciones_baloncesto
            ADD CONSTRAINT competiciones_baloncesto_pais_id_fkey
            FOREIGN KEY (pais_id) REFERENCES public.paises(id);
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 3) Tabla equipos_baloncesto
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.equipos_baloncesto (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre varchar(100) NOT NULL,
    nombre_corto varchar(50) NULL,
    nombre_comun varchar(50) NULL,
    abreviatura varchar(10) NULL,
    pais_id uuid NULL,
    ciudad varchar(100) NULL,
    estadio varchar(120) NULL,
    capacidad_estadio integer NULL,
    competicion_principal_id uuid NULL,
    conferencia varchar(20) NULL,
    division varchar(30) NULL,
    sofascore_id integer NULL,
    espn_team_id varchar(50) NULL,
    api_basketball_id integer NULL,
    logo_url text NULL,
    colores_primarios varchar(50) NULL,
    activo boolean DEFAULT true,
    creado_en timestamptz DEFAULT now(),
    actualizado_en timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_equipos_baloncesto_nombre
    ON public.equipos_baloncesto (nombre);
CREATE INDEX IF NOT EXISTS idx_equipos_baloncesto_activo
    ON public.equipos_baloncesto (activo);
CREATE INDEX IF NOT EXISTS idx_equipos_baloncesto_competicion
    ON public.equipos_baloncesto (competicion_principal_id);
CREATE INDEX IF NOT EXISTS idx_equipos_baloncesto_sofascore
    ON public.equipos_baloncesto (sofascore_id)
    WHERE sofascore_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_equipos_baloncesto_pais
    ON public.equipos_baloncesto (pais_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'equipos_baloncesto_sofascore_id_key'
          AND conrelid = 'public.equipos_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.equipos_baloncesto
            ADD CONSTRAINT equipos_baloncesto_sofascore_id_key UNIQUE (sofascore_id);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'equipos_baloncesto_competicion_principal_id_fkey'
          AND conrelid = 'public.equipos_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.equipos_baloncesto
            ADD CONSTRAINT equipos_baloncesto_competicion_principal_id_fkey
            FOREIGN KEY (competicion_principal_id)
            REFERENCES public.competiciones_baloncesto(id);
    END IF;
END $$;

DO $$
BEGIN
    IF to_regclass('public.paises') IS NOT NULL
       AND NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'equipos_baloncesto_pais_id_fkey'
              AND conrelid = 'public.equipos_baloncesto'::regclass
       ) THEN
        ALTER TABLE public.equipos_baloncesto
            ADD CONSTRAINT equipos_baloncesto_pais_id_fkey
            FOREIGN KEY (pais_id) REFERENCES public.paises(id);
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 4) Ajustes de compatibilidad en equipos legacy (tabla usada por ESPN/NBA)
-- --------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.equipos') IS NOT NULL THEN
        ALTER TABLE public.equipos
            ADD COLUMN IF NOT EXISTS competicion_principal_id uuid NULL;

        ALTER TABLE public.equipos
            ADD COLUMN IF NOT EXISTS sofascore_id integer NULL;

        -- conferencia/division opcionales para soportar equipos no NBA
        BEGIN
            ALTER TABLE public.equipos
                ALTER COLUMN conferencia DROP NOT NULL;
        EXCEPTION WHEN others THEN
            NULL;
        END;

        BEGIN
            ALTER TABLE public.equipos
                ALTER COLUMN division DROP NOT NULL;
        EXCEPTION WHEN others THEN
            NULL;
        END;

        IF EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'equipos_conferencia_check'
              AND conrelid = 'public.equipos'::regclass
        ) THEN
            ALTER TABLE public.equipos
                DROP CONSTRAINT equipos_conferencia_check;
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'equipos_conferencia_nullable_check'
              AND conrelid = 'public.equipos'::regclass
        ) THEN
            ALTER TABLE public.equipos
                ADD CONSTRAINT equipos_conferencia_nullable_check
                CHECK (
                    conferencia IS NULL
                    OR conferencia IN ('Este', 'Oeste')
                );
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'equipos_competicion_principal_id_fkey'
              AND conrelid = 'public.equipos'::regclass
        ) THEN
            ALTER TABLE public.equipos
                ADD CONSTRAINT equipos_competicion_principal_id_fkey
                FOREIGN KEY (competicion_principal_id)
                REFERENCES public.competiciones_baloncesto(id);
        END IF;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_equipos_sofascore_unique
            ON public.equipos (sofascore_id)
            WHERE sofascore_id IS NOT NULL;
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 5) Alta / correccion de competiciones NBA y Euroliga
-- --------------------------------------------------------------------------
INSERT INTO public.competiciones_baloncesto (
    nombre,
    nombre_corto,
    codigo,
    tipo,
    sofascore_id,
    espn_league_id,
    n_equipos,
    formato_competicion,
    tiene_playoffs,
    activo,
    prioridad
)
VALUES (
    'National Basketball Association',
    'NBA',
    'nba',
    'LIGA_PROFESIONAL',
    NULL,
    'nba',
    30,
    'regular+playoffs',
    true,
    true,
    1
)
ON CONFLICT (codigo) DO UPDATE
SET nombre = EXCLUDED.nombre,
    nombre_corto = EXCLUDED.nombre_corto,
    tipo = EXCLUDED.tipo,
    sofascore_id = NULL,
    espn_league_id = EXCLUDED.espn_league_id,
    n_equipos = EXCLUDED.n_equipos,
    formato_competicion = EXCLUDED.formato_competicion,
    tiene_playoffs = EXCLUDED.tiene_playoffs,
    activo = true,
    prioridad = LEAST(public.competiciones_baloncesto.prioridad, 1),
    actualizado_en = now();

INSERT INTO public.competiciones_baloncesto (
    nombre,
    nombre_corto,
    codigo,
    tipo,
    sofascore_id,
    espn_league_id,
    n_equipos,
    formato_competicion,
    tiene_playoffs,
    activo,
    prioridad
)
VALUES (
    'Turkish Airlines Euroleague',
    'Euroliga',
    'euroleague',
    'EUROLIGA',
    138,
    NULL,
    18,
    'liga+playoffs+f4',
    true,
    true,
    2
)
ON CONFLICT (codigo) DO UPDATE
SET nombre = EXCLUDED.nombre,
    nombre_corto = EXCLUDED.nombre_corto,
    tipo = EXCLUDED.tipo,
    sofascore_id = 138,
    n_equipos = EXCLUDED.n_equipos,
    formato_competicion = EXCLUDED.formato_competicion,
    tiene_playoffs = EXCLUDED.tiene_playoffs,
    activo = true,
    prioridad = LEAST(public.competiciones_baloncesto.prioridad, 2),
    actualizado_en = now();

-- --------------------------------------------------------------------------
-- 6) Tabla temporadas_baloncesto + migracion desde temporadas (legacy)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.temporadas_baloncesto (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre varchar(20) NOT NULL,
    anio_inicio integer NOT NULL,
    anio_fin integer NOT NULL,
    fecha_inicio date NULL,
    fecha_fin date NULL,
    activa boolean DEFAULT false,
    finalizada boolean DEFAULT false,
    creado_en timestamptz DEFAULT now(),
    actualizado_en timestamptz DEFAULT now(),
    competicion_id uuid NULL,
    sofascore_season_id integer NULL
);

ALTER TABLE public.temporadas_baloncesto
    ADD COLUMN IF NOT EXISTS competicion_id uuid NULL;
ALTER TABLE public.temporadas_baloncesto
    ADD COLUMN IF NOT EXISTS sofascore_season_id integer NULL;
ALTER TABLE public.temporadas_baloncesto
    ADD COLUMN IF NOT EXISTS finalizada boolean DEFAULT false;

DO $$
DECLARE
    v_nba uuid;
BEGIN
    SELECT id INTO v_nba
    FROM public.competiciones_baloncesto
    WHERE codigo = 'nba'
    LIMIT 1;

    IF to_regclass('public.temporadas') IS NOT NULL THEN
        EXECUTE format($sql$
            INSERT INTO public.temporadas_baloncesto (
                id, nombre, anio_inicio, anio_fin,
                fecha_inicio, fecha_fin, activa,
                creado_en, actualizado_en, competicion_id
            )
            SELECT
                t.id,
                t.nombre,
                t.anio_inicio,
                t.anio_fin,
                t.fecha_inicio,
                t.fecha_fin,
                COALESCE(t.activa, false),
                COALESCE(t.creado_en, now()),
                COALESCE(t.actualizado_en, now()),
                %L::uuid
            FROM public.temporadas t
            ON CONFLICT (id) DO NOTHING
        $sql$, v_nba);
    END IF;

    UPDATE public.temporadas_baloncesto
    SET competicion_id = v_nba
    WHERE competicion_id IS NULL;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'temporadas_baloncesto_competicion_id_fkey'
          AND conrelid = 'public.temporadas_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.temporadas_baloncesto
            ADD CONSTRAINT temporadas_baloncesto_competicion_id_fkey
            FOREIGN KEY (competicion_id)
            REFERENCES public.competiciones_baloncesto(id);
    END IF;
END $$;

ALTER TABLE public.temporadas_baloncesto
    ALTER COLUMN competicion_id SET NOT NULL;

DO $$
DECLARE
    r record;
BEGIN
    -- eliminar UNIQUE(nombre) legacy para permitir NBA 2025-26 y Euroliga 2025-26
    FOR r IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'public.temporadas_baloncesto'::regclass
          AND contype = 'u'
          AND pg_get_constraintdef(oid) = 'UNIQUE (nombre)'
    LOOP
        EXECUTE format(
            'ALTER TABLE public.temporadas_baloncesto DROP CONSTRAINT %I',
            r.conname
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_temporada_baloncesto_competicion'
          AND conrelid = 'public.temporadas_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.temporadas_baloncesto
            ADD CONSTRAINT uq_temporada_baloncesto_competicion
            UNIQUE (competicion_id, nombre);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_anios'
          AND conrelid = 'public.temporadas_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.temporadas_baloncesto
            ADD CONSTRAINT check_anios
            CHECK (anio_fin = anio_inicio + 1);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_temporadas_baloncesto_competicion
    ON public.temporadas_baloncesto (competicion_id);
CREATE INDEX IF NOT EXISTS idx_temporadas_baloncesto_activa
    ON public.temporadas_baloncesto (activa)
    WHERE activa = true;
CREATE INDEX IF NOT EXISTS idx_temporadas_baloncesto_sofascore
    ON public.temporadas_baloncesto (sofascore_season_id)
    WHERE sofascore_season_id IS NOT NULL;

-- --------------------------------------------------------------------------
-- 7) Tabla partidos_baloncesto + migracion desde partidos (legacy)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.partidos_baloncesto (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    temporada_id uuid NULL,
    fecha_partido date NOT NULL,
    tipo_partido varchar(10) NOT NULL DEFAULT 'REG',
    equipo_local_id uuid NOT NULL,
    equipo_visitante_id uuid NOT NULL,
    local_q1 integer NOT NULL DEFAULT 0,
    local_q2 integer NOT NULL DEFAULT 0,
    local_q3 integer NOT NULL DEFAULT 0,
    local_q4 integer NOT NULL DEFAULT 0,
    local_ot integer DEFAULT 0,
    local_total integer NOT NULL DEFAULT 0,
    visitante_q1 integer NOT NULL DEFAULT 0,
    visitante_q2 integer NOT NULL DEFAULT 0,
    visitante_q3 integer NOT NULL DEFAULT 0,
    visitante_q4 integer NOT NULL DEFAULT 0,
    visitante_ot integer DEFAULT 0,
    visitante_total integer NOT NULL DEFAULT 0,
    ganador_id uuid NULL,
    diferencia_puntos integer NULL,
    hubo_overtime boolean DEFAULT false,
    fuente_datos varchar(30) DEFAULT 'ESPN',
    url_referencia text NULL,
    valido boolean DEFAULT true,
    notas text NULL,
    creado_en timestamptz DEFAULT now(),
    actualizado_en timestamptz DEFAULT now(),
    espn_game_id text NULL,
    source text NULL,
    source_game_id text NULL,
    sofascore_match_id integer NULL,
    competicion_id uuid NULL
);

ALTER TABLE public.partidos_baloncesto
    ADD COLUMN IF NOT EXISTS competicion_id uuid NULL;
ALTER TABLE public.partidos_baloncesto
    ADD COLUMN IF NOT EXISTS sofascore_match_id integer NULL;
ALTER TABLE public.partidos_baloncesto
    ADD COLUMN IF NOT EXISTS source text NULL;
ALTER TABLE public.partidos_baloncesto
    ADD COLUMN IF NOT EXISTS source_game_id text NULL;
ALTER TABLE public.partidos_baloncesto
    ADD COLUMN IF NOT EXISTS espn_game_id text NULL;
ALTER TABLE public.partidos_baloncesto
    ADD COLUMN IF NOT EXISTS fuente_datos varchar(30) DEFAULT 'ESPN';

DO $$
DECLARE
    v_nba uuid;
BEGIN
    SELECT id INTO v_nba
    FROM public.competiciones_baloncesto
    WHERE codigo = 'nba'
    LIMIT 1;

    IF to_regclass('public.partidos') IS NOT NULL THEN
        EXECUTE format($sql$
            INSERT INTO public.partidos_baloncesto (
                id, temporada_id, fecha_partido, tipo_partido,
                equipo_local_id, equipo_visitante_id,
                local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
                visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
                ganador_id, diferencia_puntos, hubo_overtime,
                creado_en, actualizado_en,
                espn_game_id, source, source_game_id, competicion_id
            )
            SELECT
                p.id, p.temporada_id, p.fecha_partido, p.tipo_partido,
                p.equipo_local_id, p.equipo_visitante_id,
                p.local_q1, p.local_q2, p.local_q3, p.local_q4, p.local_ot, p.local_total,
                p.visitante_q1, p.visitante_q2, p.visitante_q3, p.visitante_q4, p.visitante_ot, p.visitante_total,
                p.ganador_id, p.diferencia_puntos, p.hubo_overtime,
                COALESCE(p.creado_en, now()), COALESCE(p.actualizado_en, now()),
                p.espn_game_id,
                COALESCE(p.source, 'ESPN'),
                COALESCE(p.source_game_id, p.espn_game_id),
                %L::uuid
            FROM public.partidos p
            ON CONFLICT (id) DO NOTHING
        $sql$, v_nba);
    END IF;

    UPDATE public.partidos_baloncesto pb
    SET competicion_id = COALESCE(pb.competicion_id, t.competicion_id, v_nba)
    FROM public.temporadas_baloncesto t
    WHERE pb.temporada_id = t.id
      AND pb.competicion_id IS NULL;

    UPDATE public.partidos_baloncesto pb
    SET competicion_id = v_nba
    WHERE pb.competicion_id IS NULL;

    UPDATE public.partidos_baloncesto
    SET source = COALESCE(NULLIF(source, ''), CASE WHEN espn_game_id IS NOT NULL THEN 'ESPN' END),
        source_game_id = COALESCE(NULLIF(source_game_id, ''), espn_game_id),
        fuente_datos = COALESCE(fuente_datos, CASE WHEN source = 'SOFASCORE' THEN 'SOFASCORE' ELSE 'ESPN' END)
    WHERE source_game_id IS NULL OR source IS NULL OR fuente_datos IS NULL;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'partidos_baloncesto_competicion_id_fkey'
          AND conrelid = 'public.partidos_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.partidos_baloncesto
            ADD CONSTRAINT partidos_baloncesto_competicion_id_fkey
            FOREIGN KEY (competicion_id)
            REFERENCES public.competiciones_baloncesto(id);
    END IF;
END $$;

ALTER TABLE public.partidos_baloncesto
    ALTER COLUMN competicion_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'partidos_baloncesto_temporada_fkey'
          AND conrelid = 'public.partidos_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.partidos_baloncesto
            ADD CONSTRAINT partidos_baloncesto_temporada_fkey
            FOREIGN KEY (temporada_id)
            REFERENCES public.temporadas_baloncesto(id)
            ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF to_regclass('public.equipos') IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'partidos_baloncesto_equipo_local_fkey'
              AND conrelid = 'public.partidos_baloncesto'::regclass
        ) THEN
            ALTER TABLE public.partidos_baloncesto
                ADD CONSTRAINT partidos_baloncesto_equipo_local_fkey
                FOREIGN KEY (equipo_local_id)
                REFERENCES public.equipos(id)
                ON DELETE RESTRICT;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'partidos_baloncesto_equipo_visitante_fkey'
              AND conrelid = 'public.partidos_baloncesto'::regclass
        ) THEN
            ALTER TABLE public.partidos_baloncesto
                ADD CONSTRAINT partidos_baloncesto_equipo_visitante_fkey
                FOREIGN KEY (equipo_visitante_id)
                REFERENCES public.equipos(id)
                ON DELETE RESTRICT;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'partidos_baloncesto_ganador_fkey'
              AND conrelid = 'public.partidos_baloncesto'::regclass
        ) THEN
            ALTER TABLE public.partidos_baloncesto
                ADD CONSTRAINT partidos_baloncesto_ganador_fkey
                FOREIGN KEY (ganador_id)
                REFERENCES public.equipos(id);
        END IF;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'partidos_baloncesto_partido_exacto_key'
          AND conrelid = 'public.partidos_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.partidos_baloncesto
            ADD CONSTRAINT partidos_baloncesto_partido_exacto_key
            UNIQUE (
                temporada_id,
                fecha_partido,
                tipo_partido,
                equipo_local_id,
                equipo_visitante_id
            );
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_partidos_baloncesto_source_game
    ON public.partidos_baloncesto (source, source_game_id)
    WHERE source IS NOT NULL AND source_game_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_partidos_baloncesto_sofascore
    ON public.partidos_baloncesto (sofascore_match_id)
    WHERE sofascore_match_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_partidos_baloncesto_competicion
    ON public.partidos_baloncesto (competicion_id);
CREATE INDEX IF NOT EXISTS idx_partidos_baloncesto_fecha
    ON public.partidos_baloncesto (fecha_partido DESC);
CREATE INDEX IF NOT EXISTS idx_partidos_baloncesto_temp_comp
    ON public.partidos_baloncesto (temporada_id, competicion_id);
CREATE INDEX IF NOT EXISTS idx_partidos_baloncesto_sofascore
    ON public.partidos_baloncesto (sofascore_match_id)
    WHERE sofascore_match_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_partidos_baloncesto_busqueda
    ON public.partidos_baloncesto (
        competicion_id,
        fecha_partido DESC,
        equipo_local_id,
        equipo_visitante_id
    );

-- --------------------------------------------------------------------------
-- 8) Tabla ingestion_state_baloncesto
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ingestion_state_baloncesto (
    clave varchar(100) PRIMARY KEY,
    competicion_id uuid NULL,
    ultima_sincronizacion timestamptz NULL,
    ultima_exito timestamptz NULL,
    ultima_error timestamptz NULL,
    ultimo_error text NULL,
    ultimo_insertados integer DEFAULT 0,
    ultimo_actualizados integer DEFAULT 0,
    cursor_fecha date NULL,
    cursor_sofascore_id integer NULL,
    ventana_dias integer DEFAULT 7,
    metadata jsonb NULL,
    creado_en timestamptz DEFAULT now(),
    actualizado_en timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_state_baloncesto_clave
    ON public.ingestion_state_baloncesto (clave);
CREATE INDEX IF NOT EXISTS idx_ingestion_state_baloncesto_comp
    ON public.ingestion_state_baloncesto (competicion_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ingestion_state_baloncesto_competicion_id_fkey'
          AND conrelid = 'public.ingestion_state_baloncesto'::regclass
    ) THEN
        ALTER TABLE public.ingestion_state_baloncesto
            ADD CONSTRAINT ingestion_state_baloncesto_competicion_id_fkey
            FOREIGN KEY (competicion_id)
            REFERENCES public.competiciones_baloncesto(id);
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- 9) Ajustes en predicciones_registradas
-- --------------------------------------------------------------------------
DO $$
DECLARE
    v_nba uuid;
BEGIN
    IF to_regclass('public.predicciones_registradas') IS NULL THEN
        RETURN;
    END IF;

    SELECT id INTO v_nba
    FROM public.competiciones_baloncesto
    WHERE codigo = 'nba'
    LIMIT 1;

    ALTER TABLE public.predicciones_registradas
        ADD COLUMN IF NOT EXISTS competicion_id uuid NULL;

    UPDATE public.predicciones_registradas pr
    SET competicion_id = pb.competicion_id
    FROM public.partidos_baloncesto pb
    WHERE pr.partido_id = pb.id
      AND pr.competicion_id IS NULL;

    UPDATE public.predicciones_registradas pr
    SET competicion_id = t.competicion_id
    FROM public.temporadas_baloncesto t
    WHERE pr.temporada_id = t.id
      AND pr.competicion_id IS NULL;

    UPDATE public.predicciones_registradas
    SET competicion_id = v_nba
    WHERE competicion_id IS NULL;

    ALTER TABLE public.predicciones_registradas
        ALTER COLUMN competicion_id SET NOT NULL;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'predicciones_registradas_competicion_id_fkey'
          AND conrelid = 'public.predicciones_registradas'::regclass
    ) THEN
        ALTER TABLE public.predicciones_registradas
            ADD CONSTRAINT predicciones_registradas_competicion_id_fkey
            FOREIGN KEY (competicion_id)
            REFERENCES public.competiciones_baloncesto(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_predicciones_registradas_competicion
    ON public.predicciones_registradas (competicion_id);
CREATE INDEX IF NOT EXISTS idx_predicciones_registradas_comp_mercado
    ON public.predicciones_registradas (competicion_id, mercado, fecha_partido DESC);

-- --------------------------------------------------------------------------
-- 10) Ajustes en apuestas
-- --------------------------------------------------------------------------
DO $$
DECLARE
    v_nba uuid;
BEGIN
    IF to_regclass('public.apuestas') IS NULL THEN
        RETURN;
    END IF;

    SELECT id INTO v_nba
    FROM public.competiciones_baloncesto
    WHERE codigo = 'nba'
    LIMIT 1;

    ALTER TABLE public.apuestas
        ADD COLUMN IF NOT EXISTS competicion_id uuid NULL;

    ALTER TABLE public.apuestas
        ADD COLUMN IF NOT EXISTS competicion_nombre varchar(120) NULL;

    UPDATE public.apuestas a
    SET competicion_id = pb.competicion_id
    FROM public.partidos_baloncesto pb
    WHERE a.partido_id = pb.id
      AND a.competicion_id IS NULL;

    UPDATE public.apuestas
    SET competicion_id = v_nba
    WHERE competicion_id IS NULL;

    UPDATE public.apuestas a
    SET competicion_nombre = c.nombre_corto
    FROM public.competiciones_baloncesto c
    WHERE a.competicion_id = c.id
      AND (a.competicion_nombre IS NULL OR a.competicion_nombre = '');

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'apuestas_competicion_id_fkey'
          AND conrelid = 'public.apuestas'::regclass
    ) THEN
        ALTER TABLE public.apuestas
            ADD CONSTRAINT apuestas_competicion_id_fkey
            FOREIGN KEY (competicion_id)
            REFERENCES public.competiciones_baloncesto(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_apuestas_competicion
    ON public.apuestas (competicion_id);
CREATE INDEX IF NOT EXISTS idx_apuestas_usuario_competicion
    ON public.apuestas (usuario_id, competicion_id, creado_en DESC);

-- --------------------------------------------------------------------------
-- 11) Migrar catalogo NBA a equipos_baloncesto
-- --------------------------------------------------------------------------
DO $$
DECLARE
    v_nba uuid;
BEGIN
    IF to_regclass('public.equipos') IS NULL THEN
        RETURN;
    END IF;

    SELECT id INTO v_nba
    FROM public.competiciones_baloncesto
    WHERE codigo = 'nba'
    LIMIT 1;

    UPDATE public.equipos
    SET competicion_principal_id = v_nba
    WHERE competicion_principal_id IS NULL;

    UPDATE public.equipos
    SET sofascore_id = NULL
    WHERE competicion_principal_id = v_nba;

    INSERT INTO public.equipos_baloncesto (
        id,
        nombre,
        nombre_corto,
        nombre_comun,
        abreviatura,
        ciudad,
        competicion_principal_id,
        conferencia,
        division,
        sofascore_id,
        activo,
        creado_en,
        actualizado_en
    )
    SELECT
        e.id,
        e.nombre,
        e.nombre_corto,
        lower(e.nombre),
        e.abreviatura,
        e.ciudad,
        COALESCE(e.competicion_principal_id, v_nba),
        e.conferencia,
        e.division,
        NULL,
        COALESCE(e.activo, true),
        COALESCE(e.creado_en, now()),
        COALESCE(e.actualizado_en, now())
    FROM public.equipos e
    ON CONFLICT (id) DO UPDATE
    SET nombre = EXCLUDED.nombre,
        nombre_corto = EXCLUDED.nombre_corto,
        nombre_comun = EXCLUDED.nombre_comun,
        abreviatura = EXCLUDED.abreviatura,
        ciudad = EXCLUDED.ciudad,
        competicion_principal_id = EXCLUDED.competicion_principal_id,
        conferencia = EXCLUDED.conferencia,
        division = EXCLUDED.division,
        activo = EXCLUDED.activo,
        actualizado_en = now();
END $$;

-- --------------------------------------------------------------------------
-- 12) Estado de ingesta inicial para Euroliga
-- --------------------------------------------------------------------------
INSERT INTO public.ingestion_state_baloncesto (
    clave,
    competicion_id,
    ventana_dias,
    metadata
)
SELECT
    'euroliga_sync',
    c.id,
    7,
    '{}'::jsonb
FROM public.competiciones_baloncesto c
WHERE c.codigo = 'euroleague'
ON CONFLICT (clave) DO NOTHING;

COMMIT;

