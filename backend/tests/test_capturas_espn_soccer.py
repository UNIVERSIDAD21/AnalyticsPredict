"""Capturas aisladas: contrato estricto, revisiones y GET sin efectos laterales."""

from copy import deepcopy
from uuid import uuid4

import os
import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

from api import rutas_fuentes_futbol as rutas
from scripts.auditar_fuente_espn_soccer import FuenteNoDisponible
from scripts.ingerir_espn_soccer_capturas import aplicar_lotes, validar_lote, MIGRACION
from scripts.run_suite_global_testdb import validar_admin_local


def lote_sintetico(*, observado="2026-03-02T12:00:00Z", eventos=True):
    evento = {
        "fuente": "ESPN_SOCCER", "liga": "esp.1", "id_fuente": "123",
        "inicio_utc": "2026-03-01T13:00Z", "estado_fuente": "STATUS_FULL_TIME",
        "final_acreditado": True, "local_id_fuente": "1", "visitante_id_fuente": "2",
        "local_nombre": "Local", "visitante_nombre": "Visitante",
        "local_goles": 0, "visitante_goles": 2,
        "corners_completos": True, "local_corners": 0, "visitante_corners": 3,
        "sha256_boxscore": "b" * 64,
    }
    return {"fuente": "ESPN_SOCCER", "liga": "esp.1", "mes": "202603",
            "observado_en": observado, "estado": "OK" if eventos else "NO_DATA",
            "n_eventos": int(eventos), "n_finales": int(eventos),
            "sha256_scoreboard": "a" * 64, "eventos": [evento] if eventos else []}


def test_normaliza_utc_y_no_confunde_ingesta_con_observacion():
    lote = validar_lote(lote_sintetico(observado="2026-03-02T07:00:00-05:00"))
    assert lote["observado_en"] == "2026-03-02T12:00:00+00:00"
    assert lote["eventos"][0]["local_goles"] == 0
    assert lote["eventos"][0]["local_disparos"] is None
    assert validar_lote(lote) == lote
    assert validar_lote(lote_sintetico())["sha256_lote"] == lote["sha256_lote"]


@pytest.mark.parametrize("campo,valor", [
    ("fuente", "OTRA"), ("liga", "otra"), ("mes", "202600"), ("mes", "000003"),
    ("n_eventos", True), ("n_eventos", 2), ("n_finales", True),
    ("n_finales", 0), ("estado", "NO_DATA"), ("eventos", {}),
    ("sha256_scoreboard", "z" * 64), ("observado_en", None),
    ("observado_en", "2026-03-02T12:00:00"), ("observado_en", "2999-01-01T00:00Z"),
])
def test_rechaza_metadatos_ambiguos(campo, valor):
    lote = lote_sintetico()
    lote[campo] = valor
    with pytest.raises((ValueError, FuenteNoDisponible)):
        validar_lote(lote)


@pytest.mark.parametrize("campo,valor", [
    ("fuente", "OTRA"), ("liga", "eng.1"), ("id_fuente", []),
    ("local_id_fuente", "2"), ("local_nombre", ""), ("final_acreditado", 1),
    ("estado_fuente", "STATUS_SCHEDULED"), ("local_goles", None),
    ("local_goles", True), ("local_goles", -1), ("local_corners", None),
    ("corners_completos", "true"), ("corners_completos", False),
    ("sha256_boxscore", None), ("inicio_utc", "2026-04-01T00:00Z"),
    ("inicio_utc", "2026-03-03T00:00Z"),
])
def test_rechaza_eventos_sin_identidad_o_outcome_acreditado(campo, valor):
    lote = lote_sintetico()
    lote["eventos"][0][campo] = valor
    with pytest.raises((ValueError, FuenteNoDisponible)):
        validar_lote(lote)


def test_rechaza_ids_duplicados_y_programados_con_goles():
    lote = lote_sintetico()
    lote["eventos"] *= 2
    lote.update(n_eventos=2, n_finales=2)
    with pytest.raises(ValueError, match="repetido"):
        validar_lote(lote)
    lote = lote_sintetico()
    lote["eventos"][0].update(final_acreditado=False, estado_fuente="STATUS_SCHEDULED")
    lote["n_finales"] = 0
    with pytest.raises(ValueError, match="marcador"):
        validar_lote(lote)


def test_no_data_y_orden_no_cambian_identidad_del_lote():
    assert validar_lote(lote_sintetico(eventos=False))["estado"] == "NO_DATA"
    lote = lote_sintetico()
    otro = deepcopy(lote["eventos"][0])
    otro["id_fuente"] = "456"
    lote["eventos"].append(otro)
    lote.update(n_eventos=2, n_finales=2)
    digest = validar_lote(lote)["sha256_lote"]
    lote["eventos"].reverse()
    assert validar_lote(lote)["sha256_lote"] == digest


def cliente():
    app = FastAPI()
    app.include_router(rutas.router)
    return TestClient(app)


@pytest.mark.parametrize("query", ["liga=otra&mes=202603", "liga=laliga&mes=202613",
                                  "liga=laliga&mes=000003", "liga=laliga&mes=2026"])
def test_api_rechaza_query_sin_abrir_bd(monkeypatch, query):
    monkeypatch.setattr(rutas, "obtener_pool", lambda: pytest.fail("No abrir BD"))
    assert cliente().get("/api/futbol/fuentes/espn-soccer?" + query).status_code == 422


def test_api_almacen_caido_no_es_no_data_ni_revela_excepcion(monkeypatch):
    def fallo():
        raise RuntimeError("detalle privado que no debe publicarse")
    monkeypatch.setattr(rutas, "obtener_pool", fallo)
    respuesta = cliente().get("/api/futbol/fuentes/espn-soccer?liga=laliga&mes=202603")
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"]["estado"] == "CAPTURAS_NO_DISPONIBLES"
    assert "privado" not in respuesta.text


@pytest.fixture
def captura_db():
    admin_url = os.environ.get("TEST_PG_ADMIN_URL")
    if not admin_url:
        pytest.skip("TEST_PG_ADMIN_URL requiere PostgreSQL local desechable")
    validar_admin_local(admin_url)
    nombre = f"ap_capturas_test_{uuid4().hex}"
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nombre)))
        try:
            url = make_conninfo(admin_url, dbname=nombre)
            with psycopg.connect(url, autocommit=True) as conn:
                conn.execute(MIGRACION.read_text())
                conn.execute(MIGRACION.read_text())  # DDL repetible
            yield url
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(nombre)))


@pytest.mark.integracion
def test_pg_idempotencia_revisiones_y_retorno_a_contenido_anterior(captura_db):
    lote = lote_sintetico()
    with psycopg.connect(captura_db) as conn:
        assert aplicar_lotes(conn, [lote]) == (1, 1)
        assert aplicar_lotes(conn, [lote]) == (0, 0)
        revisado = deepcopy(lote)
        revisado["observado_en"] = "2026-03-03T00:00Z"
        revisado["eventos"][0]["local_goles"] = 1
        assert aplicar_lotes(conn, [revisado]) == (1, 1)
        assert rutas.leer_captura_mes(conn, "esp.1", "202603")["eventos"][0]["local_goles"] == 1
        lote["observado_en"] = "2026-03-04T00:00Z"
        assert aplicar_lotes(conn, [lote]) == (1, 1)
        assert rutas.leer_captura_mes(conn, "esp.1", "202603")["eventos"][0]["local_goles"] == 0
        # Importar después una observación antigua no sustituye el último lote.
        antiguo = lote_sintetico(observado="2026-03-02T13:00Z")
        antiguo["eventos"][0]["local_goles"] = 9
        assert aplicar_lotes(conn, [antiguo]) == (1, 1)
        assert rutas.leer_captura_mes(conn, "esp.1", "202603")["eventos"][0]["local_goles"] == 0
        assert conn.execute("SELECT count(*) FROM capturas_espn_soccer_lotes").fetchone() == (4,)


@pytest.mark.integracion
def test_pg_ultimo_lote_vacio_no_republica_eventos_viejos(captura_db):
    with psycopg.connect(captura_db) as conn:
        assert rutas.leer_captura_mes(conn, "esp.1", "202603")["estado"] == "SIN_CAPTURA"
        aplicar_lotes(conn, [lote_sintetico()])
        aplicar_lotes(conn, [lote_sintetico(observado="2026-03-04T00:00Z", eventos=False)])
        datos = rutas.leer_captura_mes(conn, "esp.1", "202603")
        assert datos["estado"] == "NO_DATA"
        assert datos["eventos"] == []
        assert datos["n_eventos"] == datos["n_finales"] == datos["n_1x2"] == 0
        assert conn.execute("SELECT count(*) FROM capturas_espn_soccer_eventos").fetchone() == (1,)


@pytest.mark.integracion
def test_pg_fallo_intermedio_revierte_todos_los_lotes(captura_db):
    with psycopg.connect(captura_db, autocommit=True) as conn:
        conn.execute("ALTER TABLE capturas_espn_soccer_eventos ADD CHECK (id_fuente <> 'rechazado')")
        otro = lote_sintetico(observado="2026-03-03T00:00Z")
        otro["eventos"][0]["id_fuente"] = "rechazado"
        with pytest.raises(psycopg.errors.CheckViolation):
            aplicar_lotes(conn, [lote_sintetico(), otro])
        assert conn.execute("SELECT count(*) FROM capturas_espn_soccer_lotes").fetchone() == (0,)
        assert conn.execute("SELECT count(*) FROM capturas_espn_soccer_eventos").fetchone() == (0,)


@pytest.mark.integracion
def test_pg_get_read_only_cobertura_y_mes_aislado(captura_db, monkeypatch):
    with psycopg.connect(captura_db) as conn:
        aplicar_lotes(conn, [lote_sintetico()])

    class Pool:
        def connection(self):
            return psycopg.connect(captura_db)

    leer_original = rutas.leer_captura_mes

    def leer_readonly(conn, liga, mes):
        assert conn.execute("SHOW transaction_read_only").fetchone() == ("on",)
        return leer_original(conn, liga, mes)

    monkeypatch.setattr(rutas, "obtener_pool", lambda: Pool())
    monkeypatch.setattr(rutas, "leer_captura_mes", leer_readonly)
    monkeypatch.setattr("requests.Session.get", lambda *a, **k: pytest.fail("GET sin HTTP remoto"))
    respuesta = cliente().get("/api/futbol/fuentes/espn-soccer?liga=laliga&mes=202603")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert (datos["n_finales"], datos["n_corners"], datos["n_disparos"], datos["n_1x2"]) == (1, 1, 0, 1)
    assert datos["observado_en"] == "2026-03-02T12:00:00+00:00"
    assert datos["ingestado_en"] > datos["observado_en"]
    assert datos["vinculo_partidos_futbol"] == "NO_VERIFICADO"
    otro_mes = cliente().get("/api/futbol/fuentes/espn-soccer?liga=laliga&mes=202604")
    assert otro_mes.json()["estado"] == "SIN_CAPTURA"
    with psycopg.connect(captura_db) as conn:
        assert conn.execute("SELECT count(*) FROM capturas_espn_soccer_lotes").fetchone() == (1,)
        assert conn.execute("SELECT count(*) FROM capturas_espn_soccer_eventos").fetchone() == (1,)


@pytest.mark.integracion
def test_migracion_copas_preserva_lotes_y_revierte_constraint(captura_db):
    migracion=MIGRACION.parent/'2026-10-18_competiciones_espn_copas.sql'
    ddl='\n'.join(l for l in migracion.read_text().splitlines() if l.strip() not in {'BEGIN;','COMMIT;'})
    with psycopg.connect(captura_db,autocommit=True) as conn:
        aplicar_lotes(conn,[lote_sintetico()])
        consulta="SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='capturas_espn_soccer_lotes'::regclass AND conname='capturas_espn_soccer_lotes_liga_check'"
        antes=conn.execute(consulta).fetchone()[0]
        with conn.transaction(force_rollback=True):
            conn.execute(ddl)
            copa=lote_sintetico();copa['liga']='eng.fa';copa['eventos'][0]['liga']='eng.fa'
            assert aplicar_lotes(conn,[copa])==(1,1)
            assert conn.execute('SELECT count(*) FROM capturas_espn_soccer_lotes').fetchone()[0]==2
        assert conn.execute(consulta).fetchone()[0]==antes
        assert conn.execute('SELECT count(*) FROM capturas_espn_soccer_lotes').fetchone()[0]==1
