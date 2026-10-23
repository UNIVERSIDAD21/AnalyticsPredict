"""Regresión Euroliga: aislamiento, cronología, probabilidades y persistencia."""
from copy import deepcopy
from datetime import date, timedelta
import importlib.util
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5, uuid4
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
import numpy as np
import pytest

from api import rutas_euroliga as rutas
from motor import euroliga as motor
from servicios import predictor_euroliga as servicio


def generar_filas():
    rng = np.random.default_rng(20261021)
    rows = []
    for inicio, n in ((date(2020, 1, 1), 500), (date(2024, 9, 1), 160), (date(2025, 9, 1), 160)):
        for i in range(n):
            h, a = i % 4, (i + 1 + (i // 4) % 3) % 4
            fecha = (inicio + timedelta(days=i)).isoformat()
            y = np.maximum(5, rng.normal(20, 4, (2, 4)).astype(int))
            if y[0].sum() == y[1].sum():
                y[0, 3] += 1
            rows.append({"id": str(uuid5(NAMESPACE_URL, fecha)), "fecha_partido": fecha,
                         "competicion_codigo": "euroleague", "valido": True, "tipo_partido": "REG",
                         "equipo_local_id": f"team-{h}", "equipo_visitante_id": f"team-{a}",
                         "local": f"Euro {h}", "visitante": f"Euro {a}", "temporada_id": str(inicio.year),
                         "temporada_nombre": str(inicio.year),
                         **{f"{lado}_q{j+1}": int(y[k,j]) for k,lado in enumerate(("local", "visitante")) for j in range(4)},
                         "local_ot": 0, "visitante_ot": 0, "local_total": int(y[0].sum()), "visitante_total": int(y[1].sum())})
    return rows


@pytest.fixture(scope="module")
def filas():
    return generar_filas()


@pytest.fixture(scope="module")
def modelo(filas):
    return motor.entrenar(filas, "2026-10-22")


def test_particiones_no_entrenan_con_eval(filas, modelo):
    alteradas = deepcopy(filas)
    for r in alteradas:
        if r["fecha_partido"] >= "2025-09-01":
            r["local_q1"] += 10
            r["local_total"] += 10
    otro = motor.entrenar(alteradas, "2026-10-22")
    assert otro["validacion"]["dataset_desarrollo_sha256"] == modelo["validacion"]["dataset_desarrollo_sha256"]
    assert otro["covarianza"] == modelo["covarianza"]
    assert otro["dataset_sha256"] != modelo["dataset_sha256"]
    assert otro["pesos_equipo"] != modelo["pesos_equipo"]  # refit sí incorpora EVAL explícitamente


@pytest.mark.parametrize("campo,valor", [("competicion_codigo", "nba"), ("valido", False), ("local_ot", None), ("local_q2", -1), ("local_total", 0), ("local_total", 999), ("tipo_partido", "PRE")])
def test_excluye_fuera_de_dominio_y_periodos_invalidos(filas, campo, valor):
    r = {**filas[0], campo: valor}
    assert not motor.final_valido(r)
    assert motor.preparar_filas([r], "2026-10-22") == []


def test_snapshot_cutoff_y_duplicados(filas):
    assert motor.preparar_filas([filas[0]], filas[0]["fecha_partido"]) == []
    with pytest.raises(ValueError, match="duplicado"):
        motor.preparar_filas([filas[0], filas[0]], "2026-10-22")


def test_publicacion_recarga_sin_entrenar(modelo, tmp_path, monkeypatch):
    ruta = tmp_path / "activo.json"
    motor.publicar(modelo, ruta)
    monkeypatch.setattr(motor, "entrenar", lambda *a, **k: pytest.fail("No se debe entrenar al recargar"))
    restaurado = motor.cargar(ruta)
    assert restaurado == modelo
    a = motor.predecir(modelo, "Euro 0", "Euro 1", "COMPLETO", 160.5)
    b = motor.predecir(restaurado, "Euro 0", "Euro 1", "COMPLETO", 160.5)
    for k in ("predicciones", "probabilidades", "modelo_version", "dataset_sha256"):
        assert a[k] == b[k]
    assert len(list((tmp_path / "versiones").glob("*.json"))) == 1
    motor.publicar(modelo, ruta)
    assert len(list((tmp_path / "versiones").glob("*.json"))) == 1


def test_artefacto_no_admite_nba_ni_corrupcion(modelo, tmp_path):
    for campo, valor in (("dominio", "nba"), ("covarianza", [[-1]]), ("pesos_equipo", [[float("nan")]])):
        copia = {**modelo, campo: valor}
        with pytest.raises(ValueError):
            motor.publicar(copia, tmp_path / "activo.json")
    with pytest.raises(RuntimeError):
        motor.cargar(tmp_path / "ausente.json")


@pytest.mark.parametrize("linea", [140, 140.5, 160, 160.5, 180.2])
def test_probabilidades_push_y_monotonia(modelo, linea):
    p = motor.predecir(modelo, "Euro 0", "Euro 1", "COMPLETO", linea)
    probs = p["probabilidades"]
    assert sum(probs.values()) == pytest.approx(1)
    assert all(0 <= x <= 1 for x in probs.values())
    assert (probs["push"] > 0) == float(linea).is_integer()
    mayor = motor.predecir(modelo, "Euro 0", "Euro 1", "COMPLETO", linea + 10)
    assert mayor["probabilidades"]["over"] <= probs["over"]
    assert p["ventaja_regulacion"]["visitante"] == pytest.approx(1-p["ventaja_regulacion"]["local"])
    assert p["calibrador_id"] is None and p["incluye_ot"] is False


def test_live_condiciona_cuartos_completos_no_reentrena(modelo):
    base = motor.predecir(modelo, "Euro 0", "Euro 1", "COMPLETO", 160.5)
    live = motor.predecir(modelo, "Euro 0", "Euro 1", "COMPLETO", 160.5, [[20, 19], [21, 18], [22, 20]])
    assert live["modo"] == "CIERRE_Q3"
    assert live["predicciones"]["Q1"]["media_total"] == 39
    assert live["predicciones"]["Q1"]["desviacion_total"] == 0
    assert live["predicciones"]["COMPLETO"]["desviacion_total"] < base["predicciones"]["COMPLETO"]["desviacion_total"]
    q1 = motor.predecir(modelo, "Euro 0", "Euro 1", "Q1", 39, [[20, 19]])
    assert q1["probabilidades"] == {"over": 0, "under": 0, "push": 1}


@pytest.mark.parametrize("parciales", [[[1, 2]]*4, [[-1, 2]], [[2.5, 3]], [[True, 3]], [[1]]])
def test_live_rechaza_parciales_no_soportados(modelo, parciales):
    with pytest.raises(ValueError):
        motor.predecir(modelo, "Euro 0", "Euro 1", "COMPLETO", 160.5, parciales)


def test_abstencion_equipos_nba_y_muestra_pequena(modelo):
    with pytest.raises(ValueError, match="Abstención"):
        motor.predecir(modelo, "Lakers", "Euro 1", "COMPLETO", 160.5)
    copia = deepcopy(modelo)
    copia["muestras_equipo"]["euro 0"] = 5
    with pytest.raises(ValueError, match="Abstención"):
        motor.predecir(copia, "Euro 0", "Euro 1", "COMPLETO", 160.5)
    copia["muestras_equipo"]["euro 0"] = 6
    p = motor.predecir(copia, "Euro 0", "Euro 1", "COMPLETO", 160.5)
    assert any("Muestra pequeña" in x for x in p["advertencias"])


@pytest.fixture
def cliente(modelo, filas, monkeypatch, tmp_path):
    futuro = {**filas[0], "id": str(uuid5(NAMESPACE_URL, "fixture-euro")), "fecha_partido": (date.today()+timedelta(days=2)).isoformat(), "local_total": None, "visitante_total": None}
    monkeypatch.setattr(rutas, "modelo_actual", lambda: modelo)
    monkeypatch.setattr(rutas, "leer_datos", lambda: filas + [futuro])
    monkeypatch.setenv("ANALYTICSPREDICT_EUROLIGA_JOURNAL", str(tmp_path / "journal"))
    app = FastAPI()
    app.include_router(rutas.router)
    return TestClient(app), futuro


def test_api_aislada_y_journal_inmutable(cliente, tmp_path, modelo):
    c, f = cliente
    p = {"equipo_local": f["local"], "equipo_visitante": f["visitante"], "mercado": "Q1", "linea": 40.5, "partido_id": f["id"], "cuota_over": 1.91, "cuota_under": 1.95, "lado": "UNDER"}
    r = c.post("/api/euroliga/analizar", json=p)
    assert r.status_code == 200, r.text
    resultado = r.json()["resultado"]
    assert resultado["analisis_integral"]["cuotas"] == {"over": 1.91, "under": 1.95}
    assert resultado["analisis_integral"]["lado"] == "UNDER"
    assert len(resultado["analisis_integral"]["periodos"]) == 5
    assert resultado["prospectiva_acreditada_por_fecha"]
    assert resultado["diagnostico_modelo"]["partidos_entrenamiento"] == modelo["partidos_entrenamiento"]
    assert resultado["validacion_historica"]["train_n"] == modelo["validacion"]["train_n"]
    assert set(resultado["validacion_historica"]["evaluacion"]["mercados"]) == set(motor.MERCADOS)
    assert resultado["contexto"]["corte_exclusivo"] == f["fecha_partido"]
    assert all(len(g["cuartos"]) == 4 for equipo in resultado["contexto"]["equipos"].values() for g in equipo["recientes"])
    archivos = list((tmp_path / "journal").glob("*.json"))
    assert len(archivos) == 1
    anterior = archivos[0].read_bytes()
    for ruta in ("estado", "equipos", "partidos", "historial"):
        assert c.get("/api/euroliga/" + ruta).status_code == 200
    assert archivos[0].read_bytes() == anterior
    assert len(list((tmp_path / "journal").glob("*.json"))) == 1
    assert c.get("/api/euroliga/historial").json()["analisis"][0]["analisis_id"] == resultado["analisis_id"]


@pytest.mark.parametrize("cambio", [{"equipo_local": "Lakers"}, {"partido_id": str(uuid5(NAMESPACE_URL, "nba-fixture"))}, {"linea": -1}, {"mercado": "OT"}, {"temporadas": ["nba"]}, {"parciales": [[True, 4]]}, {"parciales": [[10.5, 3]]}])
def test_api_no_admite_contaminacion_ni_payload_invalidos(cliente, cambio):
    c, f = cliente
    p = {"equipo_local": f["local"], "equipo_visitante": f["visitante"], "linea": 160.5, "partido_id": f["id"], **cambio}
    assert c.post("/api/euroliga/analizar", json=p).status_code == 422


def test_journal_no_sobrescribe_y_no_acredita_mismo_dia(modelo, tmp_path):
    p = motor.predecir(modelo, "Euro 0", "Euro 1", "Q1", 40.5)
    r = servicio.registrar(p, {"id": "fixture", "fecha_partido": date.today().isoformat()}, tmp_path)
    assert not r["prospectiva_acreditada_por_fecha"]
    with pytest.raises(FileExistsError):
        motor.escribir_nuevo(tmp_path / (r["analisis_id"] + ".json"), {})


def test_capturas_concurrentes_publican_un_json_completo(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    destino = tmp_path / 'captura.json'
    def escribir(n):
        try:
            motor.escribir_nuevo(destino, {'origen': n, 'datos': list(range(100))})
            return True
        except FileExistsError:
            return False
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(escribir, (1, 2)))
    assert sum(resultados) == 1
    assert json.loads(destino.read_text())['datos'] == list(range(100))
    assert len(list(tmp_path.iterdir())) == 1


def test_contexto_solo_euroliga_y_anterior_al_fixture(filas):
    c = servicio.contexto(filas, filas[0]["local"], filas[0]["visitante"], "2024-09-01")
    assert all(x["fecha"] < "2024-09-01" for d in c["equipos"].values() for x in d["recientes"])
    assert all(x["fecha"] < "2024-09-01" for x in c["h2h"])
    overtime = {**filas[-1], "id": "overtime-euro", "fecha_partido": "2026-10-20",
                "equipo_local_id": "team-0", "equipo_visitante_id": "team-1",
                "local": "Euro 0", "visitante": "Euro 1", "temporada_id": "2025",
                "temporada_nombre": "2025", "local_q1": 20, "local_q2": 20,
                "local_q3": 20, "local_q4": 20, "visitante_q1": 20,
                "visitante_q2": 20, "visitante_q3": 20, "visitante_q4": 20,
                "local_ot": 5, "visitante_ot": 4, "local_total": 85, "visitante_total": 84}
    detallado = servicio.contexto([*filas, overtime], "Euro 0", "Euro 1", "2026-10-22", "2025")
    for equipo in detallado["equipos"].values():
        assert len(equipo["recientes"]) <= 50
        assert all(len(g["cuartos"]) == 4 for g in equipo["recientes"])
        assert all(g["puntos_finales"] == g["puntos_regulacion"] + g["puntos_ot"] for g in equipo["recientes"])
        temporada = equipo["temporada_resumen"]
        assert temporada["nombre"] == "2025"
        assert temporada["total"]["partidos"] == sum(temporada[lado]["partidos"] for lado in ("como_local", "como_visitante"))
    assert len(detallado["equipos"]["euro 0"]["recientes"]) == 50
    partido_ot = next(g for g in detallado["equipos"]["euro 0"]["recientes"] if g["id"] == "overtime-euro")
    assert (partido_ot["resultado_regulacion"], partido_ot["puntos_ot"], partido_ot["puntos_rival_ot"],
            partido_ot["puntos_finales"], partido_ot["puntos_rival_finales"]) == ("E", 5, 4, 85, 84)


def test_cohorte_congela_no_regenera_y_detecta_tamper(modelo, filas, tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("euro_cli", Path(__file__).parents[1] / "scripts/gestionar_predictor_euroliga.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    futuro = {**filas[0], "id": "futuro", "fecha_partido": (date.today()+timedelta(days=2)).isoformat(), "local_total": None, "visitante_total": None}
    d = tmp_path / "cohorte"
    assert modulo.congelar(modelo, [futuro], d)["capturas"] == 1
    assert modulo.evaluar_cohorte(d, [futuro])["n"] == 0
    final = {**filas[0], 'id': 'futuro', 'fecha_partido': futuro['fecha_partido']}
    assert modulo.evaluar_cohorte(d, [final])["n"] == 0  # No aceptar final fechado en el futuro.
    from datetime import datetime, timezone
    class RelojPosterior(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now(timezone.utc) + timedelta(days=3)
    monkeypatch.setattr(modulo, 'datetime', RelojPosterior)
    evaluacion = modulo.evaluar_cohorte(d, [final])
    assert evaluacion['n'] == 1
    assert set(evaluacion['mercados']) == set(motor.MERCADOS)
    assert evaluacion['mercados']['Q1']['mae'] >= 0
    with pytest.raises(FileExistsError):
        modulo.congelar(modelo, [futuro], d)
    (d / "COHORTE.json").write_text("{}")
    with pytest.raises(ValueError, match="Hash"):
        modulo.evaluar_cohorte(d, [futuro])


@pytest.mark.integracion
def test_postgres_aisla_euro_nba_y_bloquea_escrituras(monkeypatch):
    """SQL real contra una base propia desechable, nunca Neon."""
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo
    from scripts.run_suite_global_testdb import validar_admin_local
    from api import rutas_partidos

    admin_url = os.getenv('TEST_PG_ADMIN_URL')
    if not admin_url:
        pytest.skip('Requiere PostgreSQL local desechable')
    validar_admin_local(admin_url)
    nombre = 'ap_euro_' + uuid4().hex
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
        try:
            url = make_conninfo(admin_url, dbname=nombre)
            with psycopg.connect(url, autocommit=True) as conn:
                conn.execute('''CREATE TABLE competiciones_baloncesto(id int,codigo text);
                    INSERT INTO competiciones_baloncesto VALUES(1,'nba'),(2,'euroleague');
                    CREATE TABLE equipos(id int,nombre text);
                    INSERT INTO equipos VALUES(1,'Equipo A'),(2,'Equipo B');
                    CREATE TABLE temporadas_baloncesto(id int,nombre text);
                    INSERT INTO temporadas_baloncesto VALUES(1,'2026-2027');
                    CREATE TABLE partidos_baloncesto(id int,competicion_id int,temporada_id int,
                        fecha_partido date,tipo_partido text,valido boolean,equipo_local_id int,equipo_visitante_id int,
                        local_q1 int,local_q2 int,local_q3 int,local_q4 int,local_ot int,local_total int,
                        visitante_q1 int,visitante_q2 int,visitante_q3 int,visitante_q4 int,visitante_ot int,visitante_total int,
                        espn_game_id text);
                    INSERT INTO partidos_baloncesto(id,competicion_id,temporada_id,fecha_partido,tipo_partido,valido,equipo_local_id,equipo_visitante_id)
                        VALUES(1,1,1,CURRENT_DATE,'REG',true,1,2),(2,2,1,CURRENT_DATE,'REG',true,1,2);
                ''')

            class Pool:
                def connection(self):
                    return psycopg.connect(url)

            pool = Pool()
            assert [r['id'] for r in servicio.leer_datos(pool)] == [2]
            from db import PoolAplicacion
            from lecturas_http import solo_lectura_http
            with PoolAplicacion(conninfo=url, min_size=1, max_size=1) as pool_http:
                token = solo_lectura_http.set(True)
                try:
                    assert [r['id'] for r in servicio.leer_datos(pool_http)] == [2]
                finally:
                    solo_lectura_http.reset(token)
            with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                with servicio.conexion_lectura(pool) as conn:
                    assert conn.read_only
                    conn.execute("INSERT INTO equipos VALUES(3,'No permitido')")
            monkeypatch.setattr(rutas_partidos, 'obtener_pool', lambda: pool)
            nba = rutas_partidos._consultar_partidos(fecha_desde=date.today(), fecha_hasta=date.today(), competicion='nba')
            euro = rutas_partidos._consultar_partidos(fecha_desde=date.today(), fecha_hasta=date.today(), competicion='euroleague')
            assert [p.id for p in nba.partidos] == ['1']
            assert [p.id for p in euro.partidos] == ['2']
        finally:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(nombre)))
