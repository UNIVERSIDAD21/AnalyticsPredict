-- Alta de catálogo, sin partidos, resultados ni modelos. Ejecutar en transacción.
-- El crosswalk de clubes ESPN es global: no se crean clubes ni se reutiliza Liga.
DO $copa$
DECLARE
    pais_col uuid;
    competicion uuid;
    temporada uuid;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtext('AnalyticsPredict:agenda:incremental'));
    SELECT id INTO STRICT pais_col FROM paises WHERE nombre = 'Colombia';

    INSERT INTO competiciones_futbol
        (id, nombre, nombre_corto, codigo, pais_id, tipo, activo, prioridad)
    VALUES ('d850f095-38cc-59f6-b9e2-8d42d07a818d', 'Copa BetPlay', 'Copa BetPlay',
            'COL_COPA', pais_col, 'COPA_NACIONAL', true, 111)
    ON CONFLICT DO NOTHING;
    SELECT id INTO STRICT competicion FROM competiciones_futbol
    WHERE codigo = 'COL_COPA' AND pais_id = pais_col AND tipo = 'COPA_NACIONAL'
      AND activo = true AND nombre = 'Copa BetPlay';

    IF NOT EXISTS (SELECT 1 FROM temporadas_futbol
                   WHERE competicion_id = competicion AND nombre = '2026') THEN
        INSERT INTO temporadas_futbol
            (id, competicion_id, nombre, anio_inicio, anio_fin, activa, finalizada)
        VALUES ('51377bd7-116d-51ef-b3df-5d8d15f460c4', competicion,
                '2026', 2026, 2026, true, false);
    END IF;
    SELECT id INTO STRICT temporada FROM temporadas_futbol
    WHERE competicion_id = competicion AND nombre = '2026'
      AND anio_inicio = 2026 AND anio_fin = 2026 AND activa AND NOT finalizada;

    INSERT INTO temporadas_fuente_espn_futbol(liga, anio, temporada_id, evidencia)
    VALUES ('col.copa', 2026, temporada, jsonb_build_object(
        'proveedor', 'ESPN_SOCCER', 'liga', 'col.copa', 'anio', 2026,
        'url', 'https://site.api.espn.com/apis/site/v2/sports/soccer/col.copa/scoreboard?dates=20261110&limit=500',
        'contraste_oficial', 'https://dimayor.com.co/2026/11/09/designaciones-arbitrales-semifinales-ida-de-la-copa-betplay-dimayor-2026/',
        'alcance', 'Catalogo 2026; no acredita historico ni modelo'))
    ON CONFLICT DO NOTHING;
    IF NOT EXISTS (SELECT 1 FROM temporadas_fuente_espn_futbol
                   WHERE liga = 'col.copa' AND anio = 2026 AND temporada_id = temporada) THEN
        RAISE EXCEPTION 'Crosswalk de temporada Copa Colombia incompatible';
    END IF;
END
$copa$;
