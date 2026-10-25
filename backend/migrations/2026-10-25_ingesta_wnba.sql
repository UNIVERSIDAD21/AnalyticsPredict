-- Ejecutar dentro de la transacción del importador. No registra datos ni modelos.
ALTER TABLE public.temporadas_baloncesto
    ADD COLUMN IF NOT EXISTS es_anual boolean NOT NULL DEFAULT false;
ALTER TABLE public.temporadas_baloncesto DROP CONSTRAINT IF EXISTS check_anios;
ALTER TABLE public.temporadas_baloncesto ADD CONSTRAINT check_anios
    CHECK (anio_fin = anio_inicio + CASE WHEN es_anual THEN 0 ELSE 1 END);

ALTER TABLE public.partidos_baloncesto DROP CONSTRAINT IF EXISTS partidos_tipo_partido_check;
ALTER TABLE public.partidos_baloncesto ADD CONSTRAINT partidos_tipo_partido_check
    CHECK (tipo_partido IN ('PRE', 'REG', 'POST', 'COPA'));

CREATE TABLE IF NOT EXISTS public.lotes_ingesta_wnba (
    sha256 text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    archivos jsonb NOT NULL,
    reporte_fuente jsonb NOT NULL,
    cuarentena jsonb NOT NULL,
    pendientes_fuente jsonb NOT NULL,
    advertencias_estadisticas jsonb NOT NULL,
    creado_en timestamptz NOT NULL DEFAULT now()
);

-- Un registro fuente no final no es un resultado canónico con puntos cero.
-- El JSON original conserva NULL, métricas válidas, cada OT y todas sus evidencias.
CREATE TABLE IF NOT EXISTS public.partidos_fuente_wnba (
    competicion_id uuid NOT NULL REFERENCES public.competiciones_baloncesto(id),
    source text NOT NULL CHECK (source = 'ESPN'),
    source_game_id text NOT NULL,
    temporada_id uuid NOT NULL REFERENCES public.temporadas_baloncesto(id),
    equipo_local_id uuid NOT NULL REFERENCES public.equipos(id),
    equipo_visitante_id uuid NOT NULL REFERENCES public.equipos(id),
    partido_id uuid UNIQUE REFERENCES public.partidos_baloncesto(id),
    inicio_utc timestamptz NOT NULL,
    estado text NOT NULL CHECK (estado IN ('FINALIZADO', 'PROGRAMADO', 'POSPUESTO',
        'CANCELADO', 'EN_VIVO', 'DEMORADO', 'SUSPENDIDO')),
    fase text NOT NULL CHECK (fase IN ('PRE', 'REG', 'POST', 'COPA')),
    registro jsonb NOT NULL,
    registro_sha256 text NOT NULL CHECK (registro_sha256 ~ '^[0-9a-f]{64}$'),
    lote_sha256 text NOT NULL REFERENCES public.lotes_ingesta_wnba(sha256),
    creado_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (competicion_id, source, source_game_id),
    CHECK (equipo_local_id <> equipo_visitante_id),
    CHECK ((estado = 'FINALIZADO') = (partido_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_wnba_fuente_temporada
    ON public.partidos_fuente_wnba(temporada_id, inicio_utc);
