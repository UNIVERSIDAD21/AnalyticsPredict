-- Procedencia campo-a-campo para recuperaciones estadísticas autorizadas.
-- No se ejecuta de forma implícita por la aplicación.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

CREATE TABLE vinculos_multifuente_partidos_futbol (
    fuente text NOT NULL CHECK (fuente IN ('PITCHAPI', 'ESPN_SOCCER', 'SOFASCORE', 'THESTATSAPI')),
    id_evento_fuente text NOT NULL CHECK (length(id_evento_fuente) BETWEEN 1 AND 128),
    partido_id uuid NOT NULL REFERENCES partidos_futbol(id),
    registrado_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (fuente, id_evento_fuente),
    UNIQUE (fuente, id_evento_fuente, partido_id)
);

CREATE TABLE observaciones_multifuente_estadisticas_futbol (
    fuente text NOT NULL CHECK (fuente IN ('PITCHAPI', 'ESPN_SOCCER', 'SOFASCORE', 'THESTATSAPI')),
    id_evento_fuente text NOT NULL CHECK (length(id_evento_fuente) BETWEEN 1 AND 128),
    partido_id uuid NOT NULL,
    campo text NOT NULL CHECK (campo IN (
        'local_goles_1t', 'local_goles_2t', 'local_goles_et',
        'visitante_goles_1t', 'visitante_goles_2t', 'visitante_goles_et',
        'local_penales', 'visitante_penales',
        'local_corners_total', 'visitante_corners_total',
        'local_corners_1t', 'visitante_corners_1t',
        'local_corners_2t', 'visitante_corners_2t',
        'local_disparos_total', 'visitante_disparos_total',
        'local_disparos_arco', 'visitante_disparos_arco',
        'local_disparos_fuera', 'visitante_disparos_fuera',
        'local_disparos_bloqueados', 'visitante_disparos_bloqueados',
        'local_posesion', 'visitante_posesion',
        'local_faltas', 'visitante_faltas',
        'local_tarjetas_amarillas', 'visitante_tarjetas_amarillas',
        'local_tarjetas_rojas', 'visitante_tarjetas_rojas',
        'local_fueras_juego', 'visitante_fueras_juego',
        'local_xg', 'visitante_xg', 'local_xg_1t', 'visitante_xg_1t'
    )),
    valor numeric NOT NULL
        CHECK (valor >= 0 AND valor::text NOT IN ('NaN', 'Infinity', '-Infinity')),
    CHECK (
        campo IN ('local_posesion', 'visitante_posesion', 'local_xg', 'visitante_xg',
                  'local_xg_1t', 'visitante_xg_1t')
        OR valor = trunc(valor)
    ),
    CHECK (
        campo NOT IN ('local_posesion', 'visitante_posesion') OR valor <= 100
    ),
    clave_proveedor text NOT NULL CHECK (length(clave_proveedor) BETWEEN 1 AND 128),
    periodo_proveedor text NOT NULL CHECK (periodo_proveedor IN ('All', 'FirstHalf', 'SecondHalf', 'ExtraTime')),
    sha256_payload char(64) NOT NULL CHECK (sha256_payload ~ '^[0-9a-f]{64}$'),
    contrato text NOT NULL CHECK (contrato ~ '^[A-Z0-9_]{3,80}$'),
    evidencia_identidad jsonb NOT NULL CHECK (jsonb_typeof(evidencia_identidad) = 'object'),
    observado_en timestamptz NOT NULL,
    registrado_en timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (fuente, id_evento_fuente, campo, clave_proveedor, periodo_proveedor, sha256_payload, contrato),
    FOREIGN KEY (fuente, id_evento_fuente, partido_id)
        REFERENCES vinculos_multifuente_partidos_futbol (fuente, id_evento_fuente, partido_id)
);

CREATE INDEX idx_observaciones_multifuente_partido
    ON observaciones_multifuente_estadisticas_futbol (partido_id, fuente, campo);

COMMIT;
