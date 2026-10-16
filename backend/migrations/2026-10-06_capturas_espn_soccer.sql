-- Capturas independientes del catálogo Sofascore. No enlazan ni corrigen
-- partidos_futbol; una revisión posterior debe acreditar identidades.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

CREATE TABLE IF NOT EXISTS capturas_espn_soccer_lotes (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    liga text NOT NULL CHECK (liga IN ('eng.1', 'esp.1', 'ita.1', 'ger.1', 'fra.1')),
    mes char(6) NOT NULL CHECK (mes ~ '^[0-9]{4}(0[1-9]|1[0-2])$' AND left(mes, 4) <> '0000'),
    estado text NOT NULL CHECK (estado IN ('OK', 'NO_DATA')),
    n_eventos integer NOT NULL CHECK (n_eventos >= 0),
    n_finales integer NOT NULL CHECK (n_finales >= 0 AND n_finales <= n_eventos),
    sha256_scoreboard char(64) NOT NULL CHECK (sha256_scoreboard ~ '^[0-9a-f]{64}$'),
    sha256_lote char(64) NOT NULL CHECK (sha256_lote ~ '^[0-9a-f]{64}$'),
    observado_en timestamptz NOT NULL,
    ingestado_en timestamptz NOT NULL DEFAULT now(),
    CHECK ((estado = 'NO_DATA') = (n_eventos = 0)),
    UNIQUE (liga, mes, sha256_lote)
);

CREATE TABLE IF NOT EXISTS capturas_espn_soccer_eventos (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lote_id bigint NOT NULL REFERENCES capturas_espn_soccer_lotes(id),
    liga text NOT NULL,
    id_fuente text NOT NULL,
    inicio_utc timestamptz NOT NULL,
    final_acreditado boolean NOT NULL,
    sha256_evento char(64) NOT NULL CHECK (sha256_evento ~ '^[0-9a-f]{64}$'),
    evento jsonb NOT NULL CHECK (jsonb_typeof(evento) = 'object'),
    UNIQUE (lote_id, id_fuente)
);

CREATE INDEX IF NOT EXISTS idx_capturas_espn_soccer_lotes_mes
    ON capturas_espn_soccer_lotes (liga, mes, observado_en DESC, id DESC);

COMMIT;
