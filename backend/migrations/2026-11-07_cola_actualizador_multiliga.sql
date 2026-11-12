-- El operador ejecuta esta migración y la importación inicial en una transacción.
CREATE TABLE public.ap_m1_ejecuciones (
    id uuid PRIMARY KEY,
    estado text NOT NULL CHECK (estado IN ('SOLICITADA','EN_CURSO','TERMINADA','INTERRUMPIDA','ERROR')),
    solicitada_en timestamptz NOT NULL,
    iniciada_en timestamptz,
    finalizada_en timestamptz,
    detalle jsonb NOT NULL DEFAULT '{}'
);

CREATE UNIQUE INDEX ap_m1_una_ejecucion_activa ON public.ap_m1_ejecuciones ((true))
    WHERE estado IN ('SOLICITADA','EN_CURSO');

CREATE TABLE public.ap_m1_lotes (
    huella text PRIMARY KEY CHECK (huella ~ '^[0-9a-f]{64}$'),
    ejecucion_id uuid NOT NULL REFERENCES public.ap_m1_ejecuciones(id),
    etapa text NOT NULL CHECK (etapa IN ('INICIAL','RESULTADOS','ESTADISTICAS','RESUMEN')),
    confirmado_en timestamptz NOT NULL,
    recibo jsonb NOT NULL CHECK (jsonb_typeof(recibo)='object')
);

CREATE INDEX ap_m1_lotes_por_ejecucion ON public.ap_m1_lotes(ejecucion_id, confirmado_en);

CREATE TABLE public.ap_m1_obligaciones (
    clave text[] PRIMARY KEY,
    tipo text NOT NULL CHECK (tipo IN ('EVENTO','VENTANA')),
    estado text NOT NULL CHECK (estado IN ('PENDIENTE','ESPERA_FUENTE','REVISION_IDENTIDAD','CONFLICTO','RESUELTO','SIN_COBERTURA')),
    motivo text NOT NULL CHECK (length(motivo)>0),
    fecha_evento timestamptz,
    partido_id uuid,
    primero_en timestamptz NOT NULL,
    ultimo_en timestamptz NOT NULL CHECK (ultimo_en>=primero_en),
    intentos integer NOT NULL CHECK (intentos>=0),
    reintentar_en timestamptz,
    evidencia_inicial jsonb NOT NULL CHECK (jsonb_typeof(evidencia_inicial)='object'),
    evidencia_actual jsonb NOT NULL CHECK (jsonb_typeof(evidencia_actual)='object'),
    ultimo_lote text NOT NULL REFERENCES public.ap_m1_lotes(huella),
    CHECK (array_ndims(clave)=1 AND array_lower(clave,1)=1 AND array_position(clave,NULL) IS NULL
        AND array_position(clave,'') IS NULL),
    CHECK ((tipo='EVENTO' AND cardinality(clave)=8 AND fecha_evento IS NOT NULL)
        OR (tipo='VENTANA' AND cardinality(clave)=7 AND clave[5]='VENTANA' AND fecha_evento IS NULL AND partido_id IS NULL)),
    CHECK ((estado IN ('RESUELTO','SIN_COBERTURA')) = (reintentar_en IS NULL))
);

CREATE INDEX ap_m1_pendientes_por_turno ON public.ap_m1_obligaciones(reintentar_en, primero_en)
    WHERE reintentar_en IS NOT NULL;

CREATE TABLE public.ap_m1_tramos (
    deporte text NOT NULL,
    competicion text NOT NULL,
    proveedor text NOT NULL,
    fuente text NOT NULL,
    desde date NOT NULL,
    hasta date NOT NULL CHECK (hasta>=desde),
    evidencia jsonb NOT NULL CHECK (jsonb_typeof(evidencia)='array' AND jsonb_array_length(evidencia)>0),
    lote text NOT NULL REFERENCES public.ap_m1_lotes(huella),
    PRIMARY KEY (deporte, competicion, proveedor, fuente, desde, hasta)
);
