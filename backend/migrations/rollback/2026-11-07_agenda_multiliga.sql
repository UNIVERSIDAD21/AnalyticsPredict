DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM public.ap_m2_agenda_consultas)
        OR EXISTS(SELECT 1 FROM public.ap_m1_lotes WHERE etapa='AGENDA') THEN
        RAISE EXCEPTION 'Conservar evidencia de agenda; no revertir el esquema poblado';
    END IF;
END $$;
DROP TABLE public.ap_m2_agenda_consultas;
ALTER TABLE public.ap_m1_lotes DROP CONSTRAINT ap_m1_lotes_etapa_check;
ALTER TABLE public.ap_m1_lotes ADD CONSTRAINT ap_m1_lotes_etapa_check
    CHECK (etapa IN ('INICIAL','RESULTADOS','ESTADISTICAS','RESUMEN'));
