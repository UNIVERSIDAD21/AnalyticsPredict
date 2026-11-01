"""Regresiones MLS sin red/BD: contrato, recuperación, archivo y CLI."""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import csv
import hashlib
import json
import signal
import subprocess
import sys
from pathlib import Path

import pytest
import requests

from scrapers.mls.archivo import Archivo, ArchivoError, bloqueo, bytes_json
from scrapers.mls.cliente import ClienteESPN, ConsultaError, FuenteError, url_consulta
from scrapers.mls.contrato import (
    ContratoError,
    REQUERIDOS,
    normalizar,
    enriquecer,
    entero,
    eventos_scoreboard,
)
from scrapers.mls.pipeline import ejecutar, ventana, plan
from scripts.scraper_mls import main, pendientes_previos

NOW = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)


def event(
    eid="123",
    *,
    start="2019-10-06T20:00Z",
    name="STATUS_FULL_TIME",
    score=(3, 1),
    phase="regular-season",
):
    final = name in {"STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FINAL_AET", "STATUS_FINAL_PEN"}
    state = "post" if final else "pre"
    typ = {"name": name, "state": state, "completed": final}
    teams = []
    for side, tid, value, pts in [
        ("home", "1", score[0], [1, score[0] - 1]),
        ("away", "2", score[1], [0, score[1]]),
    ]:
        teams.append(
            {
                "id": tid,
                "uid": f"s:600~t:{tid}",
                "homeAway": side,
                "score": str(value),
                "team": {"id": tid, "uid": f"s:600~t:{tid}", "displayName": "Equipo " + tid},
                "linescores": [{"displayValue": str(x)} for x in pts],
            }
        )
    return {
        "id": eid,
        "uid": f"s:600~l:770~e:{eid}",
        "date": start,
        "season": {"year": int(start[:4]), "type": 8620, "slug": phase},
        "status": {"type": deepcopy(typ)},
        "competitions": [
            {
                "id": eid,
                "date": start,
                "timeValid": True,
                "neutralSite": False,
                "status": {"type": typ},
                "competitors": teams,
            }
        ],
    }


def sides(e):
    return e["competitions"][0]["competitors"]


def scoreboard(*events):
    return {
        "leagues": [{"id": "770", "slug": "usa.1", "uid": "s:600~l:770"}],
        "events": list(events),
    }


def summary(e):
    h = deepcopy(e)
    h["league"] = {"id": "770", "slug": "usa.1", "uid": "s:600~l:770"}
    return {
        "header": h,
        "format": {"regulation": {"periods": 2, "slug": "half"}},
        "boxscore": {
            "teams": [
                {
                    "team": {"id": t["team"]["id"]},
                    "statistics": [
                        {"name": k, "displayValue": str(v)}
                        for k, v in [
                            ("wonCorners", 0 if t["homeAway"] == "home" else 5),
                            ("shotsOnTarget", 4),
                            ("totalShots", 10),
                        ]
                    ],
                }
                for t in sides(e)
            ]
        },
    }


class Clock:
    def __init__(self):
        self.value = 0.0
        self.waits = []

    def mono(self):
        return self.value

    def sleep(self, s):
        self.waits.append(s)
        self.value += s


class Response:
    def __init__(self, code=200, payload=None, raw=None, headers=None):
        self.status_code = code
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.raw = (
            raw if raw is not None else bytes_json(scoreboard() if payload is None else payload)
        )
        self.closed = False

    def iter_content(self, chunk_size):
        yield self.raw

    def close(self):
        self.closed = True


class Session:
    def __init__(self, responses, clock):
        self.responses = list(responses)
        self.clock = clock
        self.calls = []
        self.headers = {}
        self.trust_env = True

    def get(self, url, **kwargs):
        self.calls.append((url, self.clock.mono(), kwargs))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def close(self):
        pass


def client(path, *responses, **kwargs):
    c = Clock()
    s = Session(responses, c)
    kwargs.setdefault("intervalo", 2.5)
    return (
        ClienteESPN(
            Archivo(path),
            session=s,
            dormir=c.sleep,
            reloj=c.mono,
            ahora=lambda: NOW,
            jitter=lambda: 0,
            **kwargs,
        ),
        s,
        c,
    )


def run(c, **kw):
    return ejecutar(
        c,
        desde=date(2019, 10, 6),
        hasta=date(2019, 10, 6),
        zona="America/New_York",
        rondas=kw.pop("rondas", 1),
        **kw,
    )


@pytest.mark.parametrize(
    "value", [None, True, False, "-1", "3.2", "1abc", -1, 2.5, float("nan"), float("inf"), {}, []]
)
def test_numeros_no_se_inventan(value):
    with pytest.raises(ContratoError):
        entero(value, "valor")


def test_goles_cero_y_campos_planos_correctos():
    e = event(score=(0, 0))
    r = normalizar(e)
    assert r["local_goles"] == r["visitante_goles"] == 0 and r["local_corners"] is None
    assert (
        r["ganador_partido_id"] is None and r["fase"] == "REG" and r["season_type_fuente"] == "8620"
    )


def test_estadisticas_local_visitante_cero_distinto_de_null():
    e = event()
    p = summary(e)
    p["boxscore"]["teams"].reverse()
    r = enriquecer(normalizar(e), p)
    assert r["local_corners"] == 0 and r["visitante_corners"] == 5 and r["estadisticas_completas"]
    assert r["local_goles_1t"] == 1 and r["local_goles_2t"] == 2 and r["local_goles_90"] == 3


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda e: e.update(uid="s:600~l:54~e:123"), "OTRA_LIGA"),
        (lambda e: e.update(date="2019-10-06T20:00"), "FECHA_SIN_ZONA"),
        (lambda e: e["competitions"][0].update(id="456"), "ID_DISCORDANTE"),
        (lambda e: sides(e)[1].update(homeAway="home"), "LOCALIA_AMBIGUA"),
        (lambda e: sides(e)[0]["team"].update(id="2"), "ID_DISCORDANTE"),
        (lambda e: e["status"]["type"].update(completed=False), "ESTADO_CONTRADICTORIO"),
        (lambda e: e["competitions"][0]["status"]["type"].update(name=[]), "ESTADO_DESCONOCIDO"),
        (lambda e: e["competitions"][0].update(timeValid=False), "HORA_NO_CONFIRMADA"),
        (lambda e: sides(e)[0].update(score="2.5"), "ENTERO_INVALIDO"),
        (lambda e: e["season"].update(slug=[]), "FASE_AUSENTE"),
    ],
)
def test_identidad_y_esquema_invalidos_se_rechazan(mutation, code):
    e = event()
    mutation(e)
    with pytest.raises(ContratoError, match=code):
        normalizar(e)


@pytest.mark.parametrize(
    "slug",
    [
        "eastern-conference-playoffs---semifinals",
        "mls-cup",
        "western-conference-playoffs---round-one",
    ],
)
def test_fases_mls_opacas_no_se_confunden_con_tipo_nba(slug):
    e = event(phase=slug)
    e["season"]["type"] = 9754
    assert normalizar(e)["fase"] == "POST"


def test_no_final_nunca_inventa_resultado_o_estadisticas():
    r = normalizar(event(name="STATUS_SCHEDULED"))
    assert not r["final_completo"] and r["local_goles"] is None and r["hubo_penales"] is None
    assert all(r[k] is None for k in REQUERIDOS)


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda p: p["header"].update(id="777"), "SUMMARY_OTRO_EVENTO"),
        (lambda p: p["header"]["league"].update(slug="bra.1"), "OTRA_LIGA"),
        (lambda p: p["header"]["season"].update(type=999), "SUMMARY_OTRA_TEMPORADA"),
        (lambda p: sides(p["header"])[0].update(score="8"), "SUMMARY_OTRO_MARCADOR"),
        (
            lambda p: p["header"]["competitions"][0].update(date="2019-10-07T20:00Z"),
            "SUMMARY_OTRA_FECHA",
        ),
        (
            lambda p: p["boxscore"]["teams"].append(deepcopy(p["boxscore"]["teams"][0])),
            "BOXScore_OTROS_EQUIPOS",
        ),
    ],
)
def test_summary_ajeno_no_enriquece(mutation, code):
    e = event()
    p = summary(e)
    mutation(p)
    with pytest.raises(ContratoError, match=code):
        enriquecer(normalizar(e), p)


def test_metrica_invalida_aislada_y_tiros_contradictorios():
    e = event()
    p = summary(e)
    stats = p["boxscore"]["teams"][0]["statistics"]
    stats[0]["displayValue"] = "-5"
    stats[1]["displayValue"] = "11"
    r = enriquecer(normalizar(e), p)
    assert (
        r["local_corners"] is None
        and r["local_tiros_al_arco"] is None
        and r["local_tiros_totales"] is None
    )
    assert (
        r["visitante_corners"] == 5
        and len(r["incidencias"]) == 2
        and not r["estadisticas_completas"]
    )


@pytest.mark.parametrize("extra", [False, True])
def test_tanda_separada_de_goles_con_y_sin_prorroga(extra):
    e = event(name="STATUS_FINAL_PEN", score=(1, 1), phase="mls-cup")
    p = summary(e)
    p["keyEvents"] = [
        {"type": {"type": "start-shootout"}, "clock": {"value": 7200 if extra else 5400}}
    ]
    for side, goals in zip(sides(p["header"]), [6, 5]):
        periods = [1, 0] + ([0, 0] if extra else []) + [goals]
        side["shootoutScore"] = float(goals)
        side["linescores"] = [{"displayValue": str(x)} for x in periods]
        side["winner"] = side["homeAway"] == "home"
    r = enriquecer(normalizar(e), p)
    assert (
        r["local_goles"] == r["visitante_goles"] == 1
        and r["local_penales"] == 6
        and r["visitante_penales"] == 5
    )
    assert (
        r["ganador_partido_id"] is None
        and r["ganador_tanda_id"] == "1"
        and r["hubo_prorroga"] is extra
    )


def test_prorroga_goles_90_distintos_de_final():
    e = event(name="STATUS_FINAL_AET", score=(4, 3), phase="mls-cup")
    p = summary(e)
    for t, pts in zip(sides(p["header"]), [[2, 1, 0, 1], [1, 2, 0, 0]]):
        t["linescores"] = [{"displayValue": str(x)} for x in pts]
    r = enriquecer(normalizar(e), p)
    assert (
        r["local_goles"] == 4
        and r["local_goles_90"] == 3
        and r["local_goles_et"] == 1
        and r["estadisticas_completas"]
    )


def test_periodos_malos_no_eliminan_metricas_validas_ni_se_completan_por_resta():
    e = event()
    p = summary(e)
    sides(p["header"])[0].pop("linescores")
    r = enriquecer(normalizar(e), p)
    assert (
        r["estadisticas_completas"] and r["local_goles_1t"] is None and r["local_goles_2t"] is None
    )
    assert r["incidencias"][0]["codigo"] == "PERIODOS_AUSENTES"


def test_identidad_boxscore_rechaza_duplicados_y_campos_repetidos():
    e = event()
    p = summary(e)
    p["boxscore"]["teams"][0]["statistics"] *= 2
    with pytest.raises(ContratoError, match="ESTADISTICAS_DUPLICADAS"):
        enriquecer(normalizar(e), p)


@pytest.mark.parametrize(
    "response", [Response(404), Response(503), requests.Timeout(), Response(raw=b"bad")]
)
def test_summary_fallido_no_impide_resto_de_partidos(tmp_path, response):
    a, b = event(), event("124")
    c, s, _ = client(
        tmp_path,
        Response(payload=scoreboard(a, b)),
        response,
        Response(payload=summary(b)),
        intentos=1,
    )
    folder, r, code = run(c)
    assert code == 2 and r["estado"] == "COMPLETO_CON_INCIDENCIAS" and r["recorrido_completo"]
    assert (
        r["partidos_exportados"] == 2
        and r["finales_con_estadisticas_completas"] == 1
        and r["detalles_pendientes"] == 1
    )
    assert (
        len(list(csv.DictReader((folder / "partidos_completos.csv").open()))) == 1
        and len(s.calls) == 3
    )


def test_retry_solo_detalle_transitorio_y_reanudacion_antigua(tmp_path):
    e = event()
    c, s, clock = client(
        tmp_path,
        Response(payload=scoreboard(e)),
        Response(503),
        Response(payload=summary(e)),
        intentos=1,
    )
    folder, r, code = run(c, rondas=3, espera_rondas=4)
    assert code == 0 and r["consultas_pendientes"] == 0 and len(s.calls) == 3 and 4 in clock.waits
    replay, s, _ = client(tmp_path, offline=True)
    replay.ahora = lambda: NOW + timedelta(days=180)
    again, r2, code = run(replay)
    assert (
        code == 0
        and not s.calls
        and (folder / "partidos.jsonl").read_bytes() == (again / "partidos.jsonl").read_bytes()
    )
    for line in (again / "SHA256SUMS").read_text().splitlines():
        h, name = line.split("  ")
        assert hashlib.sha256((again / name).read_bytes()).hexdigest() == h


def test_cobertura_por_temporada_y_metricas_parciales(tmp_path):
    e = event()
    p = summary(e)
    p["boxscore"]["teams"][0]["statistics"].pop(0)
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=p))
    folder, r, code = run(c)
    assert code == 2 and r["cobertura"]["campos"]["local_corners"]["presentes"] == 0
    assert r["cobertura_por_temporada"]["2019"]["campos"]["visitante_corners"]["presentes"] == 1
    assert json.loads((folder / "pendientes.jsonl").read_text())["campos_faltantes"] == [
        "local_corners"
    ]


def test_ventana_mensual_truncada_se_expande_a_dia_sin_declarar_exito_prematuro(tmp_path):
    e = event()
    c, s, _ = client(
        tmp_path,
        Response(payload=scoreboard(*([e] * 500))),
        Response(payload=scoreboard(e)),
        Response(payload=summary(e)),
    )
    _, r, code = run(c)
    assert code == 0 and r["meses_expandidos"] == {"201910": ["20191006"]}
    assert "dates=20191006" in s.calls[1][0] and r["ventanas_verificadas"] == ["201910"]


def test_feed_diario_tambien_truncado_queda_pendiente(tmp_path):
    p = scoreboard(*([event()] * 500))
    c, _, _ = client(tmp_path, Response(payload=p), Response(payload=p))
    _, r, code = run(c)
    assert code == 3 and not r["recorrido_completo"] and r["ventanas_pendientes"] == ["201910"]


def test_mes_fallido_continua_con_siguiente(tmp_path):
    c, s, _ = client(tmp_path, Response(404), Response(payload=scoreboard()))
    _, r, code = ejecutar(c, desde=date(2019, 10, 1), hasta=date(2019, 11, 2), rondas=1)
    assert (
        code == 3
        and r["ventanas_verificadas"] == ["201911"]
        and r["ventanas_pendientes"] == ["201910"]
    )


def test_duplicados_contradictorios_excluyen_versiones(tmp_path):
    a = event()
    b = deepcopy(a)
    b["date"] = "2019-10-06T21:00Z"
    b["competitions"][0]["date"] = b["date"]
    c, _, _ = client(tmp_path, Response(payload=scoreboard(a, a, b)), Response(payload=summary(a)))
    _, r, code = run(c)
    assert (
        code == 2
        and r["partidos_exportados"] == 0
        and r["ids_cuarentena"] == ["123"]
        and r["duplicados_identicos"] == 1
    )


def test_futuro_fuera_del_rango_no_descarga_summary(tmp_path):
    a = event()
    b = event("124", start="2019-10-07T04:30Z")
    c, s, _ = client(tmp_path, Response(payload=scoreboard(a, b)), Response(payload=summary(a)))
    _, r, code = run(c)
    assert (
        code == 0
        and r["partidos_exportados"] == 1
        and r["eventos_fuera_ventana"] == 1
        and len(s.calls) == 2
    )


def test_colombia_cubre_mes_eastern_vecino():
    assert ventana(date(2025, 7, 31), date(2025, 7, 31), "America/Bogota")[-1] == [
        "202507",
        "202508",
    ]
    assert plan(date(2019, 1, 1), date(2026, 10, 25))["ventanas_previstas"] == 94


@pytest.mark.parametrize("code", [401, 403, 302, 429])
def test_bloqueo_no_se_oculta_como_cobertura_completa(tmp_path, code):
    c, s, _ = client(tmp_path, Response(payload=scoreboard(event())), Response(code))
    _, r, result = run(c)
    assert (
        result == 3
        and r["estado"] == "INCOMPLETO"
        and not r["recorrido_completo"]
        and len(s.calls) == 2
    )


def test_pacing_presupuesto_y_5xx(tmp_path):
    c, s, _ = client(
        tmp_path,
        Response(503),
        requests.ConnectionError(),
        Response(payload=scoreboard()),
        max_requests=3,
    )
    c.obtener("scoreboard", "201910")
    assert c.contadores["reintentos"] == 2 and all(
        b[1] - a[1] >= 2.5 for a, b in zip(s.calls, s.calls[1:])
    )
    with pytest.raises(FuenteError, match="Presupuesto"):
        c.obtener("scoreboard", "201911")


def test_caching_refresh_integridad_y_offline(tmp_path):
    c, s, _ = client(
        tmp_path,
        Response(payload=scoreboard()),
        Response(payload=scoreboard(event())),
        refresh=True,
    )
    c.obtener("scoreboard", "201910")
    c.obtener("scoreboard", "201910")
    assert len(s.calls) == 1
    fresh, s, _ = client(tmp_path, Response(payload=scoreboard(event())), refresh=True)
    _, meta = fresh.obtener("scoreboard", "201910")
    assert len(s.calls) == 1
    (tmp_path / "raw" / f"{meta['sha256']}.json").write_bytes(b"corrupt")
    offline, s, _ = client(tmp_path, offline=True)
    with pytest.raises(ArchivoError):
        offline.obtener("scoreboard", "201910")
    assert not s.calls


@pytest.mark.parametrize(
    "endpoint,param",
    [
        ("summary", "../x"),
        ("scoreboard", "201913"),
        ("scoreboard", "20190230"),
        ("scoreboard", "20190101-20190201"),
        ("teams", "1"),
    ],
)
def test_urls_fijadas_y_fechas_validas(endpoint, param):
    with pytest.raises(ValueError):
        url_consulta(endpoint, param)


def test_checkpoint_y_ctrl_c_exportan_avance(tmp_path):
    e = event()
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=summary(e)))

    def stop(x):
        folder = Path(x["ejecucion"])
        assert json.loads((folder / "reporte.json").read_text())["partidos_exportados"] == 1
        raise KeyboardInterrupt

    folder, r, code = run(c, progreso=stop, checkpoint_cada=1)
    assert (
        code == 130
        and r["partidos_exportados"] == 1
        and json.loads((folder / "reporte.json").read_text())["estado"] == "INTERRUMPIDO"
    )


def test_offline_parcial_no_solicita_red(tmp_path):
    c, s, _ = client(tmp_path, offline=True)
    _, r, code = run(c)
    assert code == 3 and r["consultas_pendientes"] == 1 and not s.calls


def test_error_interno_exportado_no_declarado_completo(tmp_path):
    c, _, _ = client(tmp_path)
    c.obtener = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("falla sintetica"))
    _, r, code = run(c)
    assert code == 4 and r["estado"] == "ERROR_INTERNO"


def test_cli_plan_no_red_y_salida_fuera_repo(tmp_path, capsys):
    output = tmp_path / "sin_crear"
    assert main(["--desde", "2019-01-01", "--hasta", "2026-10-25", "--salida", str(output)]) == 0
    assert not output.exists() and json.loads(capsys.readouterr().out)["ventanas_previstas"] == 94
    repo = Path(__file__).resolve().parents[3]
    with pytest.raises(SystemExit):
        main(
            [
                "--desde",
                "2019-10-06",
                "--hasta",
                "2019-10-06",
                "--fetch",
                "--salida",
                str(repo / "no_crear_mls"),
            ]
        )
    assert not (repo / "no_crear_mls").exists()


def test_cli_offline_desde_cualquier_carpeta_y_lock(tmp_path):
    archive = Archivo(tmp_path)
    e = event()
    observed = datetime.now(timezone.utc).isoformat()
    for endpoint, param, payload in [
        ("scoreboard", "201910", scoreboard(e)),
        ("summary", "123", summary(e)),
    ]:
        archive.guardar(url_consulta(endpoint, param), bytes_json(payload), observed)
    script = Path(__file__).resolve().parents[2] / "scripts/scraper_mls.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--desde",
            "2019-10-06",
            "--hasta",
            "2019-10-06",
            "--offline",
            "--salida",
            str(tmp_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["finales_con_estadisticas_completas"] == 1
    with bloqueo(tmp_path):
        assert (
            main(
                [
                    "--desde",
                    "2019-10-06",
                    "--hasta",
                    "2019-10-06",
                    "--offline",
                    "--salida",
                    str(tmp_path),
                ]
            )
            == 3
        )


def test_reintentar_solo_urls_fijas_del_ultimo_informe(tmp_path):
    e = event()
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(404))
    run(c)
    assert pendientes_previos(tmp_path) == {url_consulta("summary", "123")}
    pointer = json.loads((tmp_path / "ultima_ejecucion.json").read_text())
    f = tmp_path / "ejecuciones" / pointer["ejecucion"] / "pendientes.jsonl"
    row = json.loads(f.read_text())
    row["url"] = "https://example.com"
    f.write_text(json.dumps(row) + "\n")
    with pytest.raises(ArchivoError):
        pendientes_previos(tmp_path)


def test_csv_no_ejecuta_formulas(tmp_path):
    e = event()
    sides(e)[0]["team"]["displayName"] = "=HYPERLINK(x)"
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=summary(e)))
    folder, _, _ = run(c)
    row = next(csv.DictReader((folder / "partidos.csv").open()))
    assert row["local_nombre"].startswith("'=")


def test_summary_no_sobrescribe_mitades_publicadas():
    e = event()
    p = summary(e)
    sides(p["header"])[0]["linescores"] = [{"displayValue": "2"}, {"displayValue": "1"}]
    r = enriquecer(normalizar(e), p, e)
    assert r["local_goles_1t"] is None and r["local_goles_2t"] is None and r["local_goles_90"] == 3
    assert r["estadisticas_completas"] and r["incidencias"][0]["codigo"] == "SUMMARY_OTROS_PERIODOS"


def test_tanda_con_ganador_contradictorio_no_deja_campos_parciales():
    e = event(name="STATUS_FINAL_PEN", score=(1, 1))
    p = summary(e)
    for t, pen in zip(sides(p["header"]), [6, 5]):
        t["linescores"] = [{"displayValue": str(n)} for n in [1, 0, pen]]
        t["shootoutScore"] = pen
        t["winner"] = False
    r = enriquecer(normalizar(e), p)
    assert (
        r["local_penales"] is None and r["ganador_tanda_id"] is None and r["hubo_prorroga"] is None
    )
    assert r["incidencias"][0]["codigo"] == "GANADOR_TANDA_DISCORDANTE"


@pytest.mark.parametrize("response", [Response(413), Response(raw=b"x" * (8 * 1024 * 1024 + 1))])
def test_mensual_demasiado_grande_se_expande_a_dia(tmp_path, response):
    e = event()
    c, s, _ = client(
        tmp_path, response, Response(payload=scoreboard(e)), Response(payload=summary(e))
    )
    _, r, code = run(c)
    assert code == 0 and r["meses_expandidos"] == {"201910": ["20191006"]} and len(s.calls) == 3


def test_expansion_diaria_no_acepta_mes_hasta_resolver_todos_los_dias(tmp_path):
    e = event()
    c, s, _ = client(
        tmp_path,
        Response(413),
        Response(payload=scoreboard(e)),
        Response(payload=summary(e)),
        Response(404),
    )
    _, r, code = ejecutar(
        c, desde=date(2019, 10, 6), hasta=date(2019, 10, 7), zona="America/New_York", rondas=1
    )
    assert code == 3 and r["ventanas_verificadas"] == [] and r["ventanas_pendientes"] == ["201910"]
    assert r["partidos_exportados"] == 1 and r["meses_expandidos"]["201910"] == [
        "20191006",
        "20191007",
    ]


def test_esquema_feed_invalido_no_se_trata_como_mes_vacio(tmp_path):
    c, _, _ = client(tmp_path, Response(payload={}))
    _, r, code = run(c)
    assert code == 3 and r["consultas_sin_eventos"] == [] and r["ventanas_pendientes"] == ["201910"]


def test_final_con_observacion_anterior_al_partido_no_se_acepta(tmp_path):
    c, _, _ = client(tmp_path, Response(payload=scoreboard(event())))
    c.ahora = lambda: datetime(2019, 10, 5, tzinfo=timezone.utc)
    _, r, code = run(c)
    assert code == 2 and r["partidos_exportados"] == 0 and r["ids_cuarentena"] == ["123"]


def test_presupuesto_global_conserva_exportaciones_parciales(tmp_path):
    a, b = event(), event("124")
    c, s, _ = client(
        tmp_path, Response(payload=scoreboard(a, b)), Response(payload=summary(a)), max_requests=2
    )
    _, r, code = run(c)
    assert (
        code == 3
        and r["partidos_exportados"] == 1
        and not r["recorrido_completo"]
        and len(s.calls) == 2
    )


def test_campo_invalido_y_pendiente_se_refresca_sin_redescargar_lo_sano(tmp_path):
    e = event()
    p = summary(e)
    p["boxscore"]["teams"][0]["statistics"][0]["displayValue"] = "-3"
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=p))
    run(c)
    c, s, _ = client(tmp_path, Response(payload=summary(e)))
    c.refrescar_urls = pendientes_previos(tmp_path)
    _, r, code = run(c)
    assert code == 0 and len(s.calls) == 1 and "/summary?" in s.calls[0][0]
    assert r["finales_con_estadisticas_completas"] == 1


def test_reintentos_429_respetan_espera_y_se_detienen_si_repite(tmp_path):
    c, s, clock = client(
        tmp_path,
        Response(429, headers={"Retry-After": "4"}),
        Response(payload=scoreboard()),
        Response(429, headers={"Retry-After": "4"}),
    )
    c.obtener("scoreboard", "201910")
    assert 4 in clock.waits
    with pytest.raises(FuenteError, match="repetido"):
        c.obtener("scoreboard", "201911")
    assert len(s.calls) == 3


@pytest.mark.parametrize(
    "kwargs",
    [{"rondas": 0}, {"rondas": 11}, {"espera_rondas": float("nan")}, {"checkpoint_cada": 0}],
)
def test_configuracion_operativa_invalida_no_crea_ejecucion(tmp_path, kwargs):
    c, _, _ = client(tmp_path)
    with pytest.raises(ValueError):
        run(c, **kwargs)
    assert not (tmp_path / "ejecuciones").exists()


@pytest.mark.parametrize("mode,expected", [("term", 130), ("kill", 9)])
def test_signales_y_terminacion_abrupta_reanudan_sin_red(tmp_path, mode, expected):
    program = r"""
import os,signal,sys
from pathlib import Path
from datetime import date
sys.path.insert(0,sys.argv[1]);sys.path.insert(0,str(Path(sys.argv[1]).parents[1]))
from test_mls import client,Response,scoreboard,summary,event
from scripts.scraper_mls import guardar_al_terminar
from scrapers.mls.pipeline import ejecutar
p=Path(sys.argv[2]);e=event();c,_,_=client(p,Response(payload=scoreboard(e)),Response(payload=summary(e)))
def stop(x):
    if sys.argv[3]=='kill':os._exit(9)
    os.kill(os.getpid(),signal.SIGTERM)
with guardar_al_terminar():
    _,_,code=ejecutar(c,desde=date(2019,10,6),hasta=date(2019,10,6),zona='America/New_York',progreso=stop,checkpoint_cada=1000)
sys.exit(code)
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(Path(__file__).parent), str(tmp_path), mode],
        capture_output=True,
        text=True,
        timeout=20,
    )
    # En Windows SIGTERM termina sin handler; el caché durable debe permitir reanudar igual.
    if sys.platform == 'win32' and mode == 'term': expected = 15
    assert result.returncode == expected, result.stderr
    c, s, _ = client(tmp_path, offline=True)
    _, r, code = run(c)
    assert code == 0 and r["finales_con_estadisticas_completas"] == 1 and not s.calls


def test_evento_fuera_del_rango_no_causa_cuarentena_por_hora_provisional(tmp_path):
    a = event()
    b = event("124", start="2019-10-20T20:00Z", name="STATUS_SCHEDULED")
    b["competitions"][0]["timeValid"] = False
    c, s, _ = client(tmp_path, Response(payload=scoreboard(a, b)), Response(payload=summary(a)))
    _, r, code = run(c)
    assert code == 0 and r["eventos_fuera_ventana"] == 1 and r["incidencias_cuarentena"] == 0


def test_mismo_id_reprogramado_fuera_del_rango_no_conserva_final_antiguo(tmp_path):
    a = event()
    b = event(start="2019-10-20T20:00Z")
    c, _, _ = client(tmp_path, Response(payload=scoreboard(a, b)), Response(payload=summary(a)))
    _, r, code = run(c)
    assert code == 2 and r["partidos_exportados"] == 0 and r["ids_cuarentena"] == ["123"]


def test_formato_de_periodos_ajeno_no_inventa_mitades():
    e = event()
    p = summary(e)
    p["format"]["regulation"]["periods"] = 4
    r = enriquecer(normalizar(e), p)
    assert r["local_goles_1t"] is None and r["estadisticas_completas"]
    assert r["incidencias"][0]["codigo"] == "FORMATO_PERIODOS_NO_ACREDITADO"


@pytest.mark.parametrize("clock,expected", [(5400, False), (7200, True), (None, None)])
def test_ceros_de_relleno_no_demuestran_prorroga(clock, expected):
    e = event(name="STATUS_FINAL_PEN", score=(1, 1))
    p = summary(e)
    for t, pen in zip(sides(p["header"]), [7, 8]):
        t["linescores"] = [{"displayValue": str(n)} for n in [1, 0, 0, 0, pen]]
        t["shootoutScore"] = pen
        t["winner"] = t["homeAway"] == "away"
    if clock is not None:
        p["keyEvents"] = [{"type": {"type": "start-shootout"}, "clock": {"value": clock}}]
    r = enriquecer(normalizar(e), p)
    assert (
        r["hubo_prorroga"] is expected and r["local_penales"] == 7 and r["ganador_tanda_id"] == "2"
    )
    assert r["local_goles_90"] == 1 and r["local_goles_et"] == 0 and r["estadisticas_completas"]
    assert bool(r["incidencias"]) is (clock is None)


def test_eventos_de_prorroga_y_tanda_a_90_contradictorios_no_se_eligen():
    e = event(name="STATUS_FINAL_PEN", score=(1, 1))
    p = summary(e)
    for t, pen in zip(sides(p["header"]), [7, 8]):
        t["linescores"] = [{"displayValue": str(n)} for n in [1, 0, 0, 0, pen]]
        t["shootoutScore"] = pen
    p["keyEvents"] = [
        {"type": {"type": "start-shootout"}, "clock": {"value": 5400}},
        {"type": {"type": "end-extra-time"}},
    ]
    r = enriquecer(normalizar(e), p)
    assert r["hubo_prorroga"] is None and r["local_penales"] is None
    assert (
        r["incidencias"][0]["codigo"] == "PRORROGA_CONTRADICTORIA" and r["estadisticas_completas"]
    )
