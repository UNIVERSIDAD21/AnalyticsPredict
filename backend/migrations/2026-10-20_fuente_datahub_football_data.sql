-- Expande la allowlist de proveedores conservando las fuentes habilitadas por
-- las migraciones hermanas (orden lexicográfico no debe reducir el CHECK).
-- DataHub atribuye su CSV abierto a football-data.co.uk. No crea datos ni altera partidos.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

ALTER TABLE vinculos_multifuente_partidos_futbol
    DROP CONSTRAINT vinculos_multifuente_partidos_futbol_fuente_check,
    ADD CONSTRAINT vinculos_multifuente_partidos_futbol_fuente_check
        CHECK (fuente IN (
            'PITCHAPI', 'ESPN_SOCCER', 'SOFASCORE', 'THESTATSAPI',
            'DATAHUB_FOOTBALL_DATA', 'KAGGLE_GOKHANERGUL', 'HF_EATPIZZANOT'
        ));

ALTER TABLE observaciones_multifuente_estadisticas_futbol
    DROP CONSTRAINT observaciones_multifuente_estadisticas_futbol_fuente_check,
    ADD CONSTRAINT observaciones_multifuente_estadisticas_futbol_fuente_check
        CHECK (fuente IN (
            'PITCHAPI', 'ESPN_SOCCER', 'SOFASCORE', 'THESTATSAPI',
            'DATAHUB_FOOTBALL_DATA', 'KAGGLE_GOKHANERGUL', 'HF_EATPIZZANOT'
        ));

COMMIT;
