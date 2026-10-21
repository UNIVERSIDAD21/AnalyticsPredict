-- Añade WEB como categoría de procedencia para evidencia manual, individual y
-- trazable obtenida de páginas públicas. No implica permiso de redistribución.
-- No crea observaciones ni modifica partidos por sí sola.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

ALTER TABLE vinculos_multifuente_partidos_futbol
    DROP CONSTRAINT vinculos_multifuente_partidos_futbol_fuente_check,
    ADD CONSTRAINT vinculos_multifuente_partidos_futbol_fuente_check
        CHECK (fuente IN (
            'PITCHAPI', 'ESPN_SOCCER', 'SOFASCORE', 'THESTATSAPI',
            'DATAHUB_FOOTBALL_DATA', 'KAGGLE_GOKHANERGUL', 'HF_EATPIZZANOT', 'WEB'
        ));

ALTER TABLE observaciones_multifuente_estadisticas_futbol
    DROP CONSTRAINT observaciones_multifuente_estadisticas_futbol_fuente_check,
    ADD CONSTRAINT observaciones_multifuente_estadisticas_futbol_fuente_check
        CHECK (fuente IN (
            'PITCHAPI', 'ESPN_SOCCER', 'SOFASCORE', 'THESTATSAPI',
            'DATAHUB_FOOTBALL_DATA', 'KAGGLE_GOKHANERGUL', 'HF_EATPIZZANOT', 'WEB'
        ));

COMMIT;
