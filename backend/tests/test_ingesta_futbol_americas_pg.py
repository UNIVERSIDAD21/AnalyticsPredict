"""Contrato SQL sintético local; jamás conecta con el destino productivo."""
import os
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
import pytest

from ingesta_futbol_americas import aplicar, instante, planificar, preparar
from test_ingesta_futbol_americas import fila


@pytest.fixture
def db_local():
    url = os.environ.get("DATABASE_URL", "")
    if not url or conninfo_to_dict(url).get("host") not in {"localhost", "127.0.0.1"}:
        pytest.skip("Requiere PostgreSQL sintético local")
    schema = "test_ingesta_americas_" + uuid4().hex
    with psycopg.connect(url, autocommit=True, row_factory=dict_row) as c:
        c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        c.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        try:
            c.execute("""
                CREATE TABLE paises(id uuid PRIMARY KEY,codigo_iso text UNIQUE,nombre text,nombre_ingles text,zona_horaria text);
                CREATE TABLE competiciones_futbol(id uuid PRIMARY KEY,codigo text UNIQUE,nombre text,nombre_corto text,pais_id uuid REFERENCES paises,tipo text,prioridad int);
                CREATE TABLE temporadas_futbol(id uuid PRIMARY KEY,competicion_id uuid REFERENCES competiciones_futbol,nombre text,anio_inicio int,anio_fin int,activa bool,finalizada bool,UNIQUE(competicion_id,nombre));
                CREATE TABLE equipos_futbol(id uuid PRIMARY KEY,nombre text,nombre_corto text,pais_id uuid REFERENCES paises,competicion_principal_id uuid REFERENCES competiciones_futbol,UNIQUE(nombre,pais_id));
                CREATE TABLE partidos_futbol(id uuid PRIMARY KEY,competicion_id uuid NOT NULL REFERENCES competiciones_futbol,
                    temporada_id uuid NOT NULL REFERENCES temporadas_futbol,equipo_local_id uuid NOT NULL REFERENCES equipos_futbol,
                    equipo_visitante_id uuid NOT NULL REFERENCES equipos_futbol,fecha_partido timestamptz,fecha_partido_local date,hora_local time,estado text,ronda text,fuente_datos text,url_referencia text,
                    hubo_tiempo_extra bool,hubo_penales bool,valido bool,datos_completos bool,datos_corners_completos bool,datos_disparos_completos bool,
                    local_goles_total int,visitante_goles_total int,local_goles_1t int,local_goles_2t int,visitante_goles_1t int,visitante_goles_2t int,
                    local_goles_et int DEFAULT 0,visitante_goles_et int DEFAULT 0,local_penales int,visitante_penales int,
                    local_corners_total int,visitante_corners_total int,local_disparos_total int,visitante_disparos_total int,
                    local_disparos_arco int,visitante_disparos_arco int,local_tarjetas_amarillas int,visitante_tarjetas_amarillas int,
                    local_tarjetas_rojas int,visitante_tarjetas_rojas int,local_faltas int,visitante_faltas int,
                    ganador_id uuid REFERENCES equipos_futbol,diferencia_goles int,resultado_final text,actualizado_en timestamptz DEFAULT now(),
                    CHECK(equipo_local_id<>equipo_visitante_id),UNIQUE(competicion_id,equipo_local_id,equipo_visitante_id,fecha_partido));
                CREATE TABLE equipos_fuente_espn_futbol(id_fuente text PRIMARY KEY,equipo_id uuid UNIQUE REFERENCES equipos_futbol,evidencia jsonb);
                CREATE TABLE temporadas_fuente_espn_futbol(liga text,anio int,temporada_id uuid UNIQUE REFERENCES temporadas_futbol,evidencia jsonb,PRIMARY KEY(liga,anio));
                CREATE TABLE partidos_fuente_espn_futbol(liga text,id_fuente text,partido_id uuid UNIQUE REFERENCES partidos_futbol,sha256_evento text,observado_en timestamptz,evidencia jsonb,PRIMARY KEY(liga,id_fuente));
            """)
            yield c
        finally:
            c.read_only = False
            c.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def entrada(*rows):
    return preparar([{"filas": list(rows or [fila()]), "reporte": "/synthetic/reporte.json", "sha256": "b" * 64}],
                    desde_fixtures=instante("2026-10-26T05:00:00Z"), hasta_fixtures=instante("2026-12-27T05:00:00Z"))


def test_aplicacion_rollback_y_repeticion_en_readonly(db_local):
    c = db_local
    p = entrada()
    with c.transaction(force_rollback=True):
        q = planificar(c, p)
        assert aplicar(c, q)["insertados"] == 1
        assert c.execute("SELECT local_corners_total FROM partidos_futbol").fetchone()["local_corners_total"] == 0
    assert c.execute("SELECT count(*) AS n FROM partidos_futbol").fetchone()["n"] == 0
    with c.transaction():
        aplicar(c, planificar(c, p))
    c.read_only = True
    with c.transaction():
        q = planificar(c, p)
        assert q["resumen_acciones"] == {"EXISTENTE": 1}
        assert aplicar(c, q) == {"insertados": 0, "actualizados": 0, "existentes": 1}


def test_fallo_segunda_fila_revierte_catalogo_y_primera(db_local):
    c = db_local
    p = entrada(fila(), fila(source_game_id="1235", local_id_fuente="300", local_nombre="Equipo C"))
    with pytest.raises(psycopg.errors.RaiseException):
        with c.transaction():
            q = planificar(c, p)
            # Error SQL real durante pipeline, después de las primeras inserciones.
            c.execute("""CREATE FUNCTION fallo() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
                IF (SELECT count(*) FROM partidos_futbol)>0 THEN RAISE EXCEPTION 'Fallo de ensayo'; END IF;
                RETURN NEW; END; $$;
                CREATE TRIGGER fallo_ingesta BEFORE INSERT ON partidos_futbol FOR EACH ROW EXECUTE FUNCTION fallo();""")
            aplicar(c, q)
    assert c.execute("SELECT count(*) AS n FROM partidos_futbol").fetchone()["n"] == 0
    assert c.execute("SELECT count(*) AS n FROM competiciones_futbol").fetchone()["n"] == 0


def test_parcial_no_imputa_y_nunca_reemplaza_final(db_local):
    c = db_local
    p = entrada(fila(local_corners=None, estadisticas_completas=False, local_goles_1t=None, local_goles_2t=None))
    with c.transaction():
        aplicar(c, planificar(c, p))
    row = c.execute("SELECT * FROM partidos_futbol").fetchone()
    assert row["local_corners_total"] is None and row["visitante_corners_total"] == 0
    assert row["local_goles_1t"] is None and row["local_goles_total"] == 1
    assert row["datos_corners_completos"] is False and row["datos_completos"] is True  # legacy: FT de goles
    with pytest.raises(ValueError, match="conciliación"):
        planificar(c, entrada(fila(local_goles=2, local_goles_2t=2, local_goles_90=2)))


def test_beforeimage_alterada_rechaza_sin_tocar_fuente(db_local):
    c = db_local
    p = entrada()
    with c.transaction(): aplicar(c, planificar(c, p))
    q = planificar(c, p)
    c.execute("UPDATE partidos_futbol SET local_goles_total=2")
    with pytest.raises(ValueError, match="Antes-imagen"):
        with c.transaction(): aplicar(c, q)
    assert c.execute("SELECT local_goles_total FROM partidos_futbol").fetchone()["local_goles_total"] == 2


def test_ids_de_copas_no_se_mezclan(db_local):
    c = db_local
    p = entrada(fila(), fila(source_game_id="1235", codigo_liga="arg.copa_lpf"),
                fila(source_game_id="1236", fase_fuente="copa-diego-armando-maradona---group-stage"))
    with c.transaction(): aplicar(c, planificar(c, p))
    rows = c.execute("SELECT c.codigo,count(*) AS n FROM partidos_futbol p JOIN competiciones_futbol c ON c.id=p.competicion_id GROUP BY c.codigo").fetchall()
    assert {r["codigo"]: r["n"] for r in rows} == {"ARG_PRIMERA": 1, "ARG_COPA_LPF": 1, "ARG_MARADONA": 1}
