"""Contratos WNBA: pasado, alcances, RAW, persistencia y aislamiento."""

from copy import deepcopy
from datetime import date, timedelta, datetime, timezone
import json
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
import numpy as np
import pytest

from motor import wnba as motor
from servicios import predictor_wnba as svc
from api import rutas_wnba as rutas


def uid(s):
    return str(uuid5(NAMESPACE_URL, s))


@pytest.fixture(scope="module", autouse=True)
def reloj():
    """Las pruebas no dependen del reloj del runner ni simulan fixtures reales."""

    class Reloj(datetime):
        @classmethod
        def now(cls, tz=None):
            fijo = datetime(2026, 10, 25, 17, tzinfo=timezone.utc)
            return fijo.astimezone(tz) if tz else fijo.replace(tzinfo=None)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(svc, "datetime", Reloj)
        mp.setattr(rutas, "datetime", Reloj)
        yield


@pytest.fixture(scope="module")
def filas():
    rng = np.random.default_rng(91286)
    rows = []
    for year, n in (
        (2019, 180),
        (2020, 180),
        (2023, 180),
        (2024, 300),
        (2025, 180),
        (2026, 180),
    ):
        for i in range(n):
            h = i % 4
            a = (h + 1 + (i // 4) % 3) % 4
            d = date(year, 1, 1) + timedelta(days=i)
            q = np.maximum(
                0, rng.normal(18 + (year - 2019) * 0.6, 3, (2, 4)).astype(int)
            )
            if q[0].sum() == q[1].sum():
                q[0, 3] += 1
            r = dict(
                competicion_codigo="wnba",
                estado="FINALIZADO",
                valido=True,
                fase="REG",
                tipo_partido="REG",
                partido_id=uid(str(d)),
                source_game_id=str(d),
                inicio_utc=str(d) + "T20:00:00+00:00",
                equipo_local_id=uid("team" + str(h)),
                equipo_visitante_id=uid("team" + str(a)),
                local=f"WNBA {h}",
                visitante=f"WNBA {a}",
                temporada_id=uid(str(year)),
                temporada_nombre=str(year),
                local_ot=0,
                visitante_ot=0,
                local_total=int(q[0].sum()),
                visitante_total=int(q[1].sum()),
            )
            r.update(
                {
                    f"{side}_q{j+1}": int(q[k, j])
                    for k, side in enumerate(("local", "visitante"))
                    for j in range(4)
                }
            )
            r["registro"] = {
                **{
                    k: v for k, v in r.items() if k.startswith(("local_", "visitante_"))
                },
                "competicion": "wnba",
                "fuente": "ESPN",
                "final_completo": True,
            }
            rows.append(r)
    return rows


@pytest.fixture(scope="module")
def modelo(filas, reloj):
    return svc.construir(filas, "2026-10-25")


@pytest.mark.parametrize(
    "k,v",
    [
        ("competicion_codigo", "nba"),
        ("competicion_codigo", "euroleague"),
        ("estado", "PROGRAMADO"),
        ("estado", "CANCELADO"),
        ("estado", "POSPUESTO"),
        ("fase", "PRE"),
        ("fase", "COPA"),
        ("valido", False),
        ("local_q1", None),
        ("local_q2", -1),
        ("local_q3", True),
        ("local_ot", None),
        ("local_total", 999),
        ("partido_id", None),
    ],
)
def test_no_admite_dominio_invalido_ni_imputa_null(filas, k, v):
    assert motor.normalizar([{**filas[0], k: v}]) == []


def test_cero_real_y_ot_no_cambian_objetivo_regulacion(filas):
    r = deepcopy(filas[0])
    r["local_total"] -= r["local_q1"]
    r["local_q1"] = 0
    r["local_ot"] = 8
    r["local_total"] += 8
    r["registro"].update({k: v for k, v in r.items() if k.startswith("local_")})
    n = motor.normalizar([r])[0]
    assert n["y"][0] == 0 and sum(n["y"][:4]) + 8 == n["local_total"]


def test_temporada_anual_y_duplicado_rechazados(filas):
    with pytest.raises(ValueError, match="anual"):
        motor.normalizar([{**filas[0], "temporada_nombre": "2019-2020"}])
    with pytest.raises(ValueError, match="duplicado"):
        motor.normalizar([filas[0], filas[0]])


def test_pasado_exclusivo_y_temporadas_efectivas(modelo):
    a = motor.alcance(modelo["datos"], [uid("2023")], "2023-03-01")
    assert a and all(r["fecha"] < "2023-03-01" and r["temporada"] == "2023" for r in a)
    with pytest.raises(ValueError, match="ajena"):
        motor.alcance(modelo["datos"], [uid("nba-season")], "2026-10-25")
    with pytest.raises(ValueError, match="POST"):
        motor.alcance(modelo["datos"], [uid("2023")], "2026-10-25", ["POST"])
    with pytest.raises(ValueError, match="duplicados"):
        motor.alcance(modelo["datos"], [uid("2023")] * 2, "2026-10-25")


def peticion(modelo, filas, **changes):
    args = dict(
        m=modelo,
        filas=filas,
        local=uid("team0"),
        visita=uid("team1"),
        temporadas=[uid("2023")],
        corte="2026-10-25",
        fases=["REG"],
        mercado="COMPLETO",
        linea=160.5,
        es_prueba=True,
    )
    return svc.analizar(**(args | changes))


def test_seleccion_modifica_media_dispersion_y_huella_sin_mutar(modelo, filas):
    original = deepcopy(modelo)
    a = peticion(modelo, filas)
    b = peticion(modelo, filas, temporadas=[uid("2026")])
    assert (
        a["predicciones"] != b["predicciones"]
        and a["dataset_sha256"] != b["dataset_sha256"]
    )
    assert (
        a["predicciones"]["COMPLETO"]["varianza_total"]
        != b["predicciones"]["COMPLETO"]["varianza_total"]
    )
    assert a["temporadas_utilizadas"] == ["2023"] and b["temporadas_utilizadas"] == [
        "2026"
    ]
    assert a["calibracion"] == "SIN_CALIBRAR" and a["confianza"] is None
    assert modelo == original
    c = peticion(modelo, filas)
    assert (
        c["predicciones"] == a["predicciones"]
        and c["dataset_sha256"] == a["dataset_sha256"]
    )


def test_historico_no_usa_propio_ni_futuro_o_season_de_futuro(modelo, filas):
    r = next(
        r
        for r in filas
        if r["temporada_nombre"] == "2026" and r["inicio_utc"][:10] == "2026-05-01"
    )
    temporadas = sorted({x["temporada_id"] for x in filas})
    p = peticion(
        modelo,
        filas,
        local=r["equipo_local_id"],
        visita=r["equipo_visitante_id"],
        temporadas=temporadas,
        corte="2026-05-01",
        partido_id=r["partido_id"],
    )
    assert p["modo"] == "HISTORICO" and p["ultimo_dato_utilizado"] < "2026-05-01"
    assert all(
        x["fecha"] < "2026-05-01"
        for t in p["contexto"]["equipos"].values()
        for x in t["recientes"]
    )
    changed = deepcopy(modelo)
    for x in changed["datos"]:
        if x["fecha"] >= "2026-05-01":
            x["y"] = [100] * 8
    q = peticion(
        changed,
        filas,
        local=r["equipo_local_id"],
        visita=r["equipo_visitante_id"],
        temporadas=temporadas,
        corte="2026-05-01",
        partido_id=r["partido_id"],
    )
    assert (
        p["predicciones"] == q["predicciones"]
        and p["probabilidades"] == q["probabilidades"]
    )
    with pytest.raises(ValueError, match="posterior"):
        peticion(
            modelo,
            filas,
            local=r["equipo_local_id"],
            visita=r["equipo_visitante_id"],
            partido_id=r["partido_id"],
        )


@pytest.mark.parametrize(
    "change",
    [
        {"local": uid("nba-team")},
        {"partido_id": uid("nba-fixture")},
        {"corte": None},
        {"local": uid("team1")},
        {"temporadas": [uid("2026")], "corte": "2026-01-20"},
    ],
)
def test_abstencion_sin_fallback(modelo, filas, change):
    with pytest.raises(ValueError):
        peticion(modelo, filas, **change)


@pytest.mark.parametrize("linea", [0, 0.5, 40, 40.5, 160, 160.5, 160.2, 600])
def test_probabilidades_discretas_coherentes(linea):
    p = motor.probabilidades(160, 400, linea)
    assert sum(p.values()) == pytest.approx(1, abs=1e-12) and all(
        0 <= v <= 1 for v in p.values()
    )
    if not float(linea).is_integer():
        assert p["push"] == 0
    if linea == 0:
        assert p["under"] == 0
    if linea == 160:
        assert p["push"] > 0
    assert motor.probabilidades(160, 400, linea + 1)["over"] <= p["over"]


@pytest.mark.parametrize(
    "mu,var,linea", [(float("nan"), 2, 3), (1, 0, 3), (-1, 4, 3), (1, 4, -1)]
)
def test_probabilidad_no_finita_o_invalida_rechazada(mu, var, linea):
    with pytest.raises(ValueError):
        motor.probabilidades(mu, var, linea)


def test_suma_varianzas_incluye_covarianzas_y_ganador_empate(modelo):
    m = deepcopy(modelo["ajuste_final"])
    m["covarianza"] = (np.eye(8) * 2 + np.ones((8, 8))).tolist()
    p = motor.predecir(m, uid("team0"), uid("team1"), "COMPLETO", 160)
    assert p["predicciones"]["COMPLETO"]["varianza_total"] == 80
    assert p["predicciones"]["COMPLETO"]["varianza_total"] != sum(
        p["predicciones"][q]["varianza_total"] for q in ["Q1", "Q2", "Q3", "Q4"]
    )
    assert (
        sum(p["ganador_regulacion"].values()) == pytest.approx(1)
        and p["ganador_regulacion"]["empate"] > 0
    )


def test_eval_no_selecciona_con_futuro_y_recarga_con_fitting_prohibido(
    modelo, filas, tmp_path, monkeypatch
):
    changed = deepcopy(modelo["datos"])
    for x in changed:
        if x["fecha"] >= "2025-01-01":
            x["y"] = [90] * 8
    other = motor.evaluar_congelado(changed)
    assert other["candidato"] == modelo["validacion"]["candidato"]
    assert other["cal_seleccion"] == modelo["validacion"]["cal_seleccion"]
    dest = tmp_path / "activo.json"
    monkeypatch.setenv("ANALYTICSPREDICT_MODELO_WNBA_ACTIVO", str(dest))
    svc.publicar(modelo)
    monkeypatch.setattr(
        motor,
        "ajustar",
        lambda *a: pytest.fail("No ajustar para reproducir candidato congelado"),
    )
    restored = svc.cargar()
    c = restored["validacion"]["candidato"]
    cohorte = restored["validacion"]["cohorte"]
    byid = {r["id"]: r for r in restored["datos"]}
    predictions = motor.medias(c, [byid[x["id"]] for x in cohorte])
    np.testing.assert_allclose(
        predictions, np.array([x["proyeccion"] for x in cohorte]), rtol=0, atol=1e-12
    )
    assert restored == modelo
    metrics = restored["validacion"]["evaluacion"]
    assert (
        len(cohorte) == metrics["analizados"]
        and metrics["analizados"] + metrics["abstenciones"] == metrics["partidos"]
    )
    assert sum(
        x["n"] for x in metrics["mercados"]["COMPLETO"]["calibracion_bins"]
    ) == len(cohorte)


def test_journal_solo_wnba_pruebas_no_prospectivas_y_corrupto(
    modelo, filas, tmp_path, monkeypatch
):
    dest = tmp_path / "wnba" / "activo.json"
    monkeypatch.setenv("ANALYTICSPREDICT_MODELO_WNBA_ACTIVO", str(dest))
    svc.publicar(modelo)
    r = svc.registrar(peticion(modelo, filas))
    assert (
        svc.historial() == [r]
        and r["es_prueba"]
        and not r["prospectiva_acreditada"]
        and not r["guardar_bitacora_habilitado"]
    )
    with pytest.raises(ValueError):
        svc.validar_guardado(
            SimpleNamespace(
                razones=[{"tipo": "trazabilidad_wnba", "analisis_id": r["analisis_id"]}]
            )
        )
    bad = json.loads(dest.read_text())
    bad["datos"][0]["y"][0] += 1
    dest.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="dañado"):
        svc.cargar()


def test_api_catalogo_aislado_ausencia_y_contrato(modelo, filas, tmp_path, monkeypatch):
    from contextlib import nullcontext
    from servicios import calendario_wnba, predictor_euroliga
    monkeypatch.setattr(predictor_euroliga, "conexion_lectura", lambda: nullcontext(None))
    monkeypatch.setattr(calendario_wnba, "listar", lambda conn: ([], {}))
    monkeypatch.setattr(svc, "leer_datos", lambda: filas)
    monkeypatch.setenv(
        "ANALYTICSPREDICT_MODELO_WNBA_ACTIVO", str(tmp_path / "activo.json")
    )
    app = FastAPI()
    app.include_router(rutas.router)
    client = TestClient(app)
    cat = client.get("/api/wnba/catalogo").json()
    assert (
        not cat["modelo"]["disponible"]
        and len(cat["equipos"]) == 4
        and cat["fuente_n"] == len(filas)
    )
    payload = dict(
        equipo_local_id=uid("team0"),
        equipo_visitante_id=uid("team1"),
        temporadas=[uid("2023")],
        corte="2026-10-25",
        linea=160.5,
        es_prueba=True,
    )
    assert client.post("/api/wnba/analizar", json=payload).status_code == 503
    svc.publicar(modelo)
    assert (
        client.post(
            "/api/wnba/analizar", json=payload | {"modo": "CIERRE_Q1"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/wnba/analizar", json=payload | {"temporadas": [uid("euro-season")]}
        ).status_code
        == 422
    )
    response = client.post("/api/wnba/analizar", json=payload)
    assert (
        response.status_code == 200
        and response.json()["resultado"]["dominio"] == "wnba"
    )
    assert len(client.get("/api/wnba/historial").json()["analisis"]) == 1
    assert client.get("/api/wnba/partidos").json()["partidos"] == []


def test_cierre_wnba_regulacion_sin_ot():
    from motor.resolucion_bitacora import valor_baloncesto

    p = {f"{s}_q{i}": 20 for s in ("local", "visitante") for i in range(1, 5)}
    p.update(
        local_ot=8,
        visitante_ot=4,
        local_total=88,
        visitante_total=84,
        equipo_local_id="a",
        equipo_visitante_id="b",
        ganador_id="a",
    )
    assert valor_baloncesto("COMPLETO", p, "wnba") == 160
    assert valor_baloncesto("COMPLETO", p, "nba") == 172


def test_guardado_expreso_exige_identidad_probabilidad_y_fecha_vigente(
    modelo, filas, tmp_path, monkeypatch
):
    from api.modelos_peticion import PeticionCrearApuesta

    monkeypatch.setenv(
        "ANALYTICSPREDICT_MODELO_WNBA_ACTIVO", str(tmp_path / "activo.json")
    )
    r = peticion(modelo, filas)
    r.update(
        es_prueba=False,
        modo="PREPARTIDO",
        fecha_partido="2099-01-01T20:00:00+00:00",
        partido_id=uid("oficial"),
        guardar_bitacora_habilitado=True,
    )
    r = svc.registrar(r)
    p = PeticionCrearApuesta(
        competicion_codigo="wnba",
        partido_id=r["partido_id"],
        equipo_local=r["equipo_local"],
        equipo_visitante=r["equipo_visitante"],
        mercado=r["mercado"],
        linea=r["linea"],
        lado="OVER",
        cuota=1.9,
        stake=10,
        probabilidad_sistema=r["probabilidades"]["over"],
        razones=[{"tipo": "trazabilidad_wnba", "analisis_id": r["analisis_id"]}],
    )
    svc.validar_guardado(p)
    for cambio in (
        {"partido_id": uid("nba")},
        {"linea": 190},
        {"probabilidad_sistema": 0.99},
        {"confianza_sistema": "ALTA"},
    ):
        with pytest.raises(ValueError):
            svc.validar_guardado(p.model_copy(update=cambio))


@pytest.mark.integracion
def test_pg_catalogo_wnba_aislado_y_transaccion_lectura(tmp_path):
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo
    from psycopg_pool import ConnectionPool
    from ingesta_wnba import MIGRACION, importar, leer_lote
    from test_ingesta_wnba import escribir_lote, registro
    from scripts.run_suite_global_testdb import validar_admin_local

    admin_url = os.getenv("TEST_PG_ADMIN_URL")
    if not admin_url:
        pytest.skip("PostgreSQL local sintético requerido")
    validar_admin_local(admin_url)
    dbname = "ap_wnba_predictor_test_" + uid(str(tmp_path)).replace("-", "")
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
        try:
            url = make_conninfo(admin_url, dbname=dbname, sslmode="disable")
            with psycopg.connect(url) as c:
                from pathlib import Path

                c.execute(
                    (
                        Path(__file__).parent / "integracion/wnba_legacy_fixture.sql"
                    ).read_text()
                )
                c.execute(MIGRACION.read_text())
                importar(
                    c,
                    leer_lote(
                        escribir_lote(
                            tmp_path / "lote",
                            [
                                registro(),
                                registro("101", False),
                                registro("102", fase="PRE"),
                            ],
                        )
                    ),
                )
            with ConnectionPool(url, min_size=1, max_size=2) as pool:
                rows = svc.leer_datos(pool)
                assert len(rows) == 3 and all(
                    r["competicion_codigo"] == "wnba" for r in rows
                )
                assert len(motor.normalizar(rows)) == 1
                assert sum(r["local_total"] is None for r in rows) == 1
                with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                    with svc.conexion_lectura(pool) as c:
                        assert (
                            c.execute("SHOW transaction_read_only").fetchone()[0]
                            == "on"
                        )
                        c.execute("UPDATE equipos SET nombre='NO ESCRIBIR'")
        finally:
            admin.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(dbname))
            )


@pytest.mark.parametrize("corte", ["incorrecto", "2099-01-01"])
def test_publicacion_rechaza_cortes_no_validos(filas, corte):
    with pytest.raises(ValueError):
        svc.construir(filas, corte)


@pytest.mark.parametrize('q',[1,2,3])
def test_api_v2_cortes_raw_sin_fallback_ni_guardado(modelo,filas,tmp_path,monkeypatch,q):
    monkeypatch.setattr(svc,'leer_datos',lambda:filas)
    monkeypatch.setenv('ANALYTICSPREDICT_MODELO_WNBA_ACTIVO',str(tmp_path/'activo.json'))
    svc.publicar(modelo)
    app=FastAPI();app.include_router(rutas.router);client=TestClient(app)
    body=dict(equipo_local_id=uid('team0'),equipo_visitante_id=uid('team1'),temporadas=[uid('2023')],
              corte='2026-10-25',mercado='COMPLETO',linea=160.5,es_prueba=True,
              contrato='NBA_EQUIVALENTE_V2',modo=f'CIERRE_Q{q}',parciales=[[20,19]]*q,lado='UNDER')
    response=client.post('/api/wnba/analizar',json=body)
    assert response.status_code==200,response.text
    r=response.json()['resultado']
    assert r['lado_solicitado']=='UNDER' and r['modo']==f'CIERRE_Q{q}'
    assert not r['incluye_ot'] and not r['guardar_bitacora_habilitado'] and not r['prospectiva_acreditada']
    assert all(r['predicciones'][f'Q{i+1}']['desviacion_total']==0 for i in range(q))
    assert client.post('/api/wnba/analizar',json=body|{'cuota_over':1.91}).status_code==422
    assert client.post('/api/wnba/analizar',json=body|{'mercado':f'Q{q}'}).status_code==422
    assert client.post('/api/wnba/analizar',json=body|{'parciales':[[True,19]]*q}).status_code==422
    assert client.post('/api/wnba/analizar',json=body|{'modo':'PREPARTIDO'}).status_code==422
    assert len(list(svc.journal().glob('*.json')))==1


def test_historial_conserva_snapshot_original_tras_cambios_bd(modelo,filas,tmp_path,monkeypatch):
    monkeypatch.setenv('ANALYTICSPREDICT_MODELO_WNBA_ACTIVO',str(tmp_path/'activo.json'))
    svc.publicar(modelo)
    r=svc.registrar(peticion(modelo,filas))
    # La lectura viva contiene otro universo; el detalle de un análisis debe ignorarlo.
    monkeypatch.setattr(rutas,'datos_bd',lambda:[])
    from servicios.presentacion_wnba import historial_equipo
    esperadas=motor.alcance(modelo['datos'],[s['id'] for s in r['temporadas_solicitadas']],r['corte_exclusivo'],r['fases_solicitadas'])
    aid=r['analisis_id'];archivo=svc.journal()/(aid+'.json');antes=archivo.read_bytes()
    app=FastAPI();app.include_router(rutas.router);client=TestClient(app)
    tid=r['equipo_local_id']
    response=client.get(f'/api/wnba/equipos/{tid}/historial',params={'analisis_id':aid})
    assert response.status_code==200,response.text
    assert response.json()==historial_equipo(esperadas,tid,regulacion=True)
    assert client.get(f'/api/wnba/equipos/{uid("ajeno")}/historial',params={'analisis_id':aid}).status_code==422
    assert archivo.read_bytes()==antes


def test_cierre_wnba_respeta_ot_solo_si_snapshot_lo_declara():
    from motor.resolucion_bitacora import valor_baloncesto
    p={f'{lado}_q{i}':20 for lado in ('local','visitante') for i in range(1,5)}
    p.update(local_ot=8,visitante_ot=4,local_total=88,visitante_total=84,
             equipo_local_id='a',equipo_visitante_id='b',ganador_id='a')
    assert valor_baloncesto('COMPLETO',p,'wnba',True)==172
    assert valor_baloncesto('Q4',p,'wnba',True)==40
    assert valor_baloncesto('COMPLETO',p,'euroleague',True)==160


@pytest.mark.parametrize('mercado,linea',[('Q1',40.5),('COMPLETO',160.5)])
def test_api_pre_2020_con_cuartos_suficientes_y_ot_insuficiente(modelo,filas,tmp_path,monkeypatch,mercado,linea):
    monkeypatch.setenv('ANALYTICSPREDICT_MODELO_WNBA_ACTIVO',str(tmp_path/'activo.json'))
    monkeypatch.setattr(svc,'leer_datos',lambda:filas)
    svc.publicar(modelo)
    app=FastAPI();app.include_router(rutas.router);client=TestClient(app)
    response=client.post('/api/wnba/analizar',json={
        'equipo_local_id':uid('team0'),'equipo_visitante_id':uid('team1'),
        'temporadas':[uid('2020')],'mercado':mercado,'linea':linea,'es_prueba':True,
        'contrato':'NBA_EQUIVALENTE_V2','cuota_over':1.91,'cuota_under':1.91})
    assert response.status_code==200,response.text
    r=response.json()['resultado']
    assert r['temporadas_utilizadas']==['2020'] and r['ot']['n']<10
    assert set(r['predicciones'])=={'Q1','Q2','Q3','Q4'}
    assert set(r['mercados_no_disponibles'])=={'COMPLETO'}
    assert all(r['predicciones'][q]['desviacion_total']>0 for q in r['predicciones'])
    if mercado=='Q1':
        assert sum(r['probabilidades'].values())==pytest.approx(1)
        assert r['valor']['over']['ev_sin_calibrar'] is not None
        assert 'base_descompuesta' in r
    else:
        assert all(x is None for x in r['probabilidades'].values())
        assert r['valor']['over']['ev_sin_calibrar'] is None
        assert r['valor']['under']['ev_sin_calibrar'] is None
        assert 'base_descompuesta' not in r
        assert not r['guardar_bitacora_habilitado'] and not r['prospectiva_acreditada']
