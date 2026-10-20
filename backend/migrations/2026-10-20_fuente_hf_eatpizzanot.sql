-- Registra explícitamente la fuente publicada eatpizzanot en Hugging Face.
-- El dataset declara CC-BY-4.0 y atribuye contenido upstream; la advertencia de
-- derechos sobre upstream queda documentada en la procedencia de cada campo.
-- Este DDL no inserta filas ni altera estadísticas canónicas.
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
