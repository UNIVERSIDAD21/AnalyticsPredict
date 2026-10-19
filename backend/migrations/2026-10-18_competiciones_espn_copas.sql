-- Ampliación a competiciones YA existentes en el catálogo. No ingiere partidos.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
ALTER TABLE capturas_espn_soccer_lotes
    DROP CONSTRAINT IF EXISTS capturas_espn_soccer_lotes_liga_check;
ALTER TABLE capturas_espn_soccer_lotes
    ADD CONSTRAINT capturas_espn_soccer_lotes_liga_check CHECK (liga IN (
        'eng.1', 'esp.1', 'ita.1', 'ger.1', 'fra.1', 'eng.fa',
        'esp.copa_del_rey', 'ita.coppa_italia', 'fra.coupe_de_france',
        'uefa.champions', 'uefa.europa', 'uefa.europa.conf'
    ));
COMMIT;
