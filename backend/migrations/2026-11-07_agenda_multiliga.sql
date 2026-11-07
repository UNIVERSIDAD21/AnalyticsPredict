-- Requiere fase 1; el operador, no un GET, aplica esta migración aditiva.
ALTER TABLE public.ap_m1_lotes DROP CONSTRAINT ap_m1_lotes_etapa_check;
ALTER TABLE public.ap_m1_lotes ADD CONSTRAINT ap_m1_lotes_etapa_check
    CHECK (etapa IN ('INICIAL','AGENDA','RESULTADOS','ESTADISTICAS','RESUMEN'));

-- Separada de ap_m1_tramos: una agenda futura no acredita resultados futuros.
CREATE TABLE public.ap_m2_agenda_consultas (
    clave text PRIMARY KEY CHECK (clave ~ '^[0-9a-f]{64}$'),
    competicion text NOT NULL,
    solicitud jsonb NOT NULL CHECK (jsonb_typeof(solicitud)='object'),
    desde date NOT NULL,
    hasta date NOT NULL CHECK (hasta>=desde),
    estado text NOT NULL CHECK (estado IN ('PENDIENTE','ERROR','OBSERVADA')),
    primero_en timestamptz NOT NULL,
    ultimo_en timestamptz NOT NULL CHECK (ultimo_en>=primero_en),
    intentos integer NOT NULL DEFAULT 0 CHECK (intentos>=0),
    reintentar_en timestamptz NOT NULL,
    evidencia jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(evidencia)='object'),
    lote text NOT NULL REFERENCES public.ap_m1_lotes(huella)
);
CREATE INDEX ap_m2_agenda_pendientes ON public.ap_m2_agenda_consultas(reintentar_en,primero_en)
    WHERE estado IN ('PENDIENTE','ERROR');
