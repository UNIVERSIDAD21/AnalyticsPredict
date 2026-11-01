"""Contratos adversariales WNBA y extracción end-to-end SIN red/BD productivas."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import requests

from scrapers.wnba.archivo import Archivo, ArchivoError, bloqueo, bytes_json
from scrapers.wnba.cliente import ClienteESPN, FuenteError, url_consulta
from scrapers.wnba.contrato import ContratoError, entero, eventos_scoreboard, normalizar
from scrapers.wnba.pipeline import ejecutar, ventana, celda_csv
from scripts.scraper_wnba import main

NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def evento(eid="123", home=None, away=None, state="FINALIZADO", start="2025-07-03T23:00Z"):
    home = [21, 25, 22, 13] if home is None else home
    away = [14, 10, 23, 7] if away is None else away
    names = {"FINALIZADO": ("STATUS_FINAL", "post", True),
             "PROGRAMADO": ("STATUS_SCHEDULED", "pre", False),
             "EN_VIVO": ("STATUS_IN_PROGRESS", "in", False)}
    name, status, done = names[state]
    typ = {"name": name, "state": status, "completed": done}
    sides = []
    for side, tid, points in (("home", "1", home), ("away", "2", away)):
        sides.append({"homeAway": side, "id": tid, "uid": f"s:40~l:59~t:{tid}",
                      "team": {"id": tid, "displayName": "Equipo sintético " + tid},
                      "score": str(sum(points)), "winner": sum(points) > sum(away if side == "home" else home),
                      "linescores": [{"value": n, "displayValue": str(n), "period": i + 1} for i, n in enumerate(points)]})
    return {"id": eid, "uid": f"s:40~l:59~e:{eid}", "date": start,
            "season": {"year": 2025, "type": 2}, "status": {"type": typ, "period": len(home)},
            "competitions": [{"id": eid, "date": start, "type": {"id": "1", "abbreviation": "STD"},
                              "timeValid": True, "neutralSite": False,
                              "status": {"type": deepcopy(typ), "period": len(home)}, "competitors": sides}]}


def scoreboard(*events):
    return {"leagues": [{"id": "59", "slug": "wnba"}], "events": list(events)}


def summary(event):
    h = deepcopy(event)
    h["league"] = {"id": "59", "slug": "wnba"}
    h["competitions"][0]["status"].pop("period")
    h["competitions"][0].pop("type")
    for side in h["competitions"][0]["competitors"]:
        side["linescores"] = [{"displayValue": p["displayValue"]} for p in side["linescores"]]
    return {"header": h, "boxscore": {"teams": []}}


def sides(e):
    return e["competitions"][0]["competitors"]


@pytest.mark.parametrize("value", [None, True, False, "", "12pts", "1.1", -1, 3.5, float("nan"), float("inf"), [], {}])
def test_entero_no_inventa_ni_trunca(value):
    with pytest.raises(ContratoError):
        entero(value, "valor")


def test_final_sintetico_completo_conserva_cero_y_timezone():
    e = evento(home=[0, 30, 30, 30])
    r = normalizar(e)
    assert r["local_q1"] == 0
    assert r["local_total"] == r["local_regulacion"] == 90
    assert r["local_ot"] == 0 and r["local_prorrogas"] == []
    assert r["inicio_colombia"] == "2025-07-03T18:00:00-05:00"
    assert r["estadisticas"]["home"]["rebotes"] is None


@pytest.mark.parametrize("state", ["PROGRAMADO", "EN_VIVO"])
def test_no_final_nunca_pasa_a_outcome(state):
    r = normalizar(evento(state=state))
    assert not r["final_completo"] and r["estado"] == state
    assert all(r[f"{side}_{field}"] is None for side in ("local", "visitante")
               for field in ("q1", "q4", "total", "ot", "regulacion"))
    assert r["ganador_id_fuente"] is None and r["estadisticas"] is None


def test_orden_periodos_explicitos_no_es_orden_de_json():
    e = evento()
    sides(e)[0]["linescores"].reverse()
    assert normalizar(e)["local_q1"] == 21


@pytest.mark.parametrize("home,away", [([20,20,20,20,5], [20,20,20,20,3]),
                                      ([20,20,20,20,5,0], [20,20,20,20,5,4])])
def test_prorrogas_multiple_y_cero_observado(home, away):
    r = normalizar(evento(home=home, away=away))
    assert r["numero_prorrogas"] == len(home) - 4
    assert r["local_prorrogas"] == home[4:]
    assert r["local_total"] == sum(home)
    assert r["local_regulacion"] == 80


def test_copa_no_contamina_regular_aunque_season_type_sea_dos():
    e = evento()
    e["competitions"][0]["type"] = {"id": "39", "abbreviation": "CC"}
    assert normalizar(e)["fase"] == "COPA"


@pytest.mark.parametrize("mutation,code", [
    (lambda e: e.update(uid="s:40~l:46~e:123"), "OTRA_LIGA"),
    (lambda e: e.update(date="2025-07-03T23:00"), "FECHA_SIN_ZONA"),
    (lambda e: e["season"].update(year=2005), "FORMATO_TEMPORADA_NO_SOPORTADO"),
    (lambda e: e["season"].update(year=2024), "TEMPORADA_FECHA_DISCORDANTE"),
    (lambda e: e["season"].update(type=99), "FASE_NO_SOPORTADA"),
    (lambda e: e["competitions"][0].update(timeValid=False), "HORA_NO_CONFIRMADA"),
    (lambda e: e["competitions"][0].update(id="124"), "ID_DISCORDANTE"),
    (lambda e: sides(e)[1].update(homeAway="home"), "LOCALIA_AMBIGUA"),
    (lambda e: sides(e)[0].update(score="82"), "PERIODOS_NO_CONCILIAN_TOTAL"),
    (lambda e: sides(e)[0].update(winner=False), "GANADOR_DISCORDANTE"),
    (lambda e: sides(e)[0]["linescores"][0].update(value=-1), "ENTERO_NEGATIVO"),
    (lambda e: sides(e)[0]["linescores"][0].update(value=21.2), "ENTERO_AUSENTE_O_INVALIDO"),
    (lambda e: sides(e)[0]["linescores"][0].update(period=2), "PERIODOS_NO_CONSECUTIVOS"),
    (lambda e: sides(e)[0]["linescores"][0].pop("period"), "PERIODOS_AMBIGUOS"),
    (lambda e: sides(e)[0]["linescores"][0].update(displayValue="22"), "PUNTOS_DISCORDANTES"),
    (lambda e: e["competitions"][0]["status"].update(period=5), "PERIODO_FINAL_DISCORDANTE"),
    (lambda e: e["competitions"][0]["status"]["type"].update(completed=False), "ESTADO_CONTRADICTORIO"),
])
def test_datos_contradictorios_rechazados(mutation, code):
    e = evento()
    mutation(e)
    with pytest.raises(ContratoError, match=code):
        normalizar(e)


def test_ot_exige_empate_antes_de_cada_prorroga():
    with pytest.raises(ContratoError, match="PRORROGA_SIN_EMPATE_PREVIO"):
        normalizar(evento(home=[20,20,20,20,5], away=[19,20,20,20,3]))
    with pytest.raises(ContratoError, match="FINAL_EMPATE"):
        normalizar(evento(home=[20]*4, away=[20]*4))


def test_summary_completa_faltante_pero_no_sobrescribe_periodos_publicados():
    e = evento()
    s = summary(e)
    sides(e)[0]["linescores"] = sides(e)[0]["linescores"][:2]
    assert normalizar(e, s)["local_q4"] == 13
    sides(e)[0]["linescores"][0].update(value=20, displayValue="20")
    with pytest.raises(ContratoError, match="SUMMARY_OTROS_PERIODOS"):
        normalizar(e, s)


@pytest.mark.parametrize("mutation,code", [
    (lambda h: h.update(id="999"), "SUMMARY_OTRO_EVENTO"),
    (lambda h: h["league"].update(slug="nba"), "OTRA_LIGA"),
    (lambda h: h["season"].update(year=2024), "SUMMARY_OTRA_TEMPORADA"),
    (lambda h: h["competitions"][0].update(date="2025-07-04T23:00Z"), "SUMMARY_OTRA_FECHA"),
    (lambda h: sides(h)[0].update(score="80"), "SUMMARY_OTRO_MARCADOR"),
    (lambda h: h.update(season=None), "OBJETO_INVALIDO"),
])
def test_summary_de_otro_contexto_se_rechaza(mutation, code):
    e = evento()
    s = summary(e)
    mutation(s["header"])
    with pytest.raises(ContratoError, match=code):
        normalizar(e, s)


def test_estadisticas_cero_distinto_de_ausente_y_coherencia_tiros():
    e = evento()
    s = summary(e)
    s["boxscore"]["teams"] = [{"team": {"id": "1"}, "statistics": [
        {"name": "steals", "displayValue": "0"},
        {"name": "fieldGoalsMade-fieldGoalsAttempted", "displayValue": "30-70"},
        {"name": "threePointFieldGoalsMade-threePointFieldGoalsAttempted", "displayValue": "10-30"},
        {"name": "freeThrowsMade-freeThrowsAttempted", "displayValue": "11-12"}]}]
    r = normalizar(e, s)
    assert r["estadisticas"]["home"]["robos"] == 0
    assert r["estadisticas"]["away"]["robos"] is None
    s["boxscore"]["teams"][0]["statistics"][-1]["displayValue"] = "10-12"
    with pytest.raises(ContratoError, match="TIROS_NO_CONCILIAN"):
        normalizar(e, s)


@pytest.mark.parametrize("bad", [{}, {"leagues": [{"id": "46", "slug": "nba"}], "events": []},
                                {"leagues": [{"id": "59", "slug": "wnba"}], "events": None},
                                {**scoreboard(), "count": 1}, scoreboard(*([evento()] * 500))])
def test_feed_invalido_no_es_dia_sin_partidos(bad):
    with pytest.raises(ContratoError):
        eventos_scoreboard(bad)


class Reloj:
    def __init__(self):
        self.now, self.waits = 0.0, []
    def sleep(self, value):
        self.waits.append(value)
        self.now += value
    def mono(self):
        return self.now


class Response:
    def __init__(self, code=200, payload=None, headers=None, raw=None):
        self.status_code = code
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.raw = bytes_json(scoreboard() if payload is None else payload) if raw is None else raw
        self.closed = False
    def iter_content(self, chunk_size):
        yield self.raw
    def close(self):
        self.closed = True


class Session:
    def __init__(self, *responses):
        self.responses, self.calls, self.headers = list(responses), [], {}
        self.trust_env, self.closed = True, False
        self.clock = None
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs, self.clock.mono() if self.clock else None))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response
    def close(self):
        self.closed = True


def client(tmp_path, *responses, **kwargs):
    clock = Reloj()
    session = Session(*responses)
    session.clock = clock
    c = ClienteESPN(Archivo(tmp_path), session=session, dormir=clock.sleep, reloj=clock.mono,
                    ahora=lambda: NOW, jitter=lambda: 0, **kwargs)
    return c, session, clock


@pytest.mark.parametrize("code", [401, 403, 301, 302, 307, 404])
def test_http_error_no_evasion_ni_retry(tmp_path, code):
    response = Response(code)
    c, s, _ = client(tmp_path, response)
    with pytest.raises(FuenteError):
        c.obtener("scoreboard", "20250703")
    assert len(s.calls) == 1 and response.closed
    assert s.calls[0][1]["allow_redirects"] is False and s.trust_env is False


@pytest.mark.parametrize("raw", [None, "-1", "abc", "61", "inf"])
def test_429_sin_espera_valida_detiene(tmp_path, raw):
    c, s, _ = client(tmp_path, Response(429, headers={} if raw is None else {"Retry-After": raw}))
    with pytest.raises(FuenteError):
        c.obtener("scoreboard", "20250703")
    assert len(s.calls) == 1


def test_429_espera_y_si_se_repite_en_otra_peticion_detiene(tmp_path):
    c, s, clock = client(tmp_path, Response(429, headers={"Retry-After": "4"}), Response(),
                         Response(429, headers={"Retry-After": "4"}))
    c.obtener("scoreboard", "20250703")
    assert 4 in clock.waits
    with pytest.raises(FuenteError, match="repetido"):
        c.obtener("scoreboard", "20250704")
    assert len(s.calls) == 3


def test_retry_after_http_date(tmp_path):
    c, _, clock = client(tmp_path, Response(429, headers={"Retry-After": "Sat, 24 Oct 2026 12:00:05 GMT"}), Response())
    c.obtener("scoreboard", "20250703")
    assert 5 in clock.waits


def test_transitorios_pacing_y_presupuesto_incluyen_reintentos(tmp_path):
    c, s, _ = client(tmp_path, Response(503), requests.Timeout(), Response(), max_requests=3)
    c.obtener("scoreboard", "20250703")
    assert c.contadores["requests"] == 3 and c.contadores["reintentos"] == 2
    assert all(b[2] - a[2] >= 1.25 for a, b in zip(s.calls, s.calls[1:]))
    with pytest.raises(FuenteError, match="Presupuesto"):
        c.obtener("scoreboard", "20250704")
    assert len(s.calls) == 3


def test_5xx_no_supera_intentos(tmp_path):
    c, s, _ = client(tmp_path, Response(503), Response(503), Response(503))
    with pytest.raises(FuenteError, match="agotados"):
        c.obtener("scoreboard", "20250703")
    assert len(s.calls) == 3


@pytest.mark.parametrize("response", [Response(raw=b"broken json"), Response(raw=b"[]"),
                                     Response(headers={"Content-Type": "text/html"}),
                                     Response(raw=b"x" * (8 * 1024 * 1024 + 1))])
def test_respuesta_no_json_o_desmesurada_no_se_reintenta(tmp_path, response):
    c, s, _ = client(tmp_path, response)
    with pytest.raises(FuenteError):
        c.obtener("scoreboard", "20250703")
    assert len(s.calls) == 1


def test_cache_verificada_offline_y_refresh_conservan_observaciones(tmp_path):
    c, s, _ = client(tmp_path, Response(payload=scoreboard(evento())))
    first = c.obtener("scoreboard", "20250703")
    assert c.obtener("scoreboard", "20250703") == first and len(s.calls) == 1
    offline, session, _ = client(tmp_path, offline=True)
    offline.ahora = lambda: NOW + timedelta(days=30)
    assert offline.obtener("scoreboard", "20250703") == first and not session.calls
    with pytest.raises(FuenteError, match="OFFLINE"):
        offline.obtener("scoreboard", "20250704")
    updated, _, _ = client(tmp_path, Response(payload=scoreboard()), refresh=True)
    second = updated.obtener("scoreboard", "20250703")
    assert second != first and len(list((tmp_path / "raw").glob("*.json"))) == 2
    assert len(list((tmp_path / "observaciones").glob("*.json"))) == 2


def test_cache_vencida_refresca_y_tampering_nunca_se_sobrescribe(tmp_path):
    c, _, _ = client(tmp_path, Response())
    _, meta = c.obtener("scoreboard", "20250703")
    newer, s, _ = client(tmp_path, Response())
    newer.ahora = lambda: NOW + timedelta(days=2)
    newer.obtener("scoreboard", "20250703")
    assert len(s.calls) == 1
    raw = tmp_path / "raw" / (meta["sha256"] + ".json")
    raw.write_bytes(b"alterado")
    refresh, session, _ = client(tmp_path, refresh=True)
    with pytest.raises(ArchivoError):
        refresh.obtener("scoreboard", "20250703")
    assert not session.calls and raw.read_bytes() == b"alterado"


@pytest.mark.parametrize("endpoint,param", [("https://example.com", "123"), ("summary", "../x"),
                                         ("scoreboard", "2025-07-03"), ("scoreboard", "20250230")])
def test_urls_no_admiten_hosts_arbitrarios_o_rutas(endpoint, param):
    with pytest.raises(ValueError):
        url_consulta(endpoint, param)


def test_limites_colombia_consultan_dia_eastern_siguiente():
    start, end, days = ventana(date(2025,7,3), date(2025,7,3), "America/Bogota")
    assert days == [date(2025,7,3), date(2025,7,4)]
    assert start.hour == end.hour == 5
    _, _, winter = ventana(date(2025,1,3), date(2025,1,3), "America/Bogota")
    assert winter == [date(2025,1,3)]


def run(c, **kwargs):
    return ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3), zona="America/New_York", **kwargs)


def test_pipeline_reanudable_dedup_cuarentena_y_csv_null(tmp_path):
    good, scheduled, bad = evento(), evento("124",state="PROGRAMADO"), evento("125")
    sides(bad)[0]["score"] = "999"
    c, _, _ = client(tmp_path, Response(payload=scoreboard(good, good, scheduled, bad)))
    folder, report, code = run(c)
    assert code == 2 and report["duplicados_identicos"] == 1
    assert report["partidos_exportados"] == 2 and report["incidencias_cuarentena"] == 1
    assert report["finales_completos"] == 1 and report["no_finales"] == 1
    assert report["ids_cuarentena"] == ["125"]
    replay, s, _ = client(tmp_path, offline=True)
    again, report2, code2 = run(replay)
    assert code2 == code and not s.calls
    assert folder != again and (folder / "partidos.jsonl").read_bytes() == (again / "partidos.jsonl").read_bytes()
    assert report2["contadores_http"]["cache_hits"] == 1
    for line in (folder / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ")
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest


def test_conflicto_duplicado_excluye_ambas_versiones(tmp_path):
    c, _, _ = client(tmp_path, Response(payload=scoreboard(evento(), evento(home=[21,25,22,14]))))
    _, report, code = run(c)
    assert code == 2 and report["partidos_exportados"] == 0
    assert report["ids_cuarentena"] == ["123"]


def test_pipeline_summary_solo_si_faltan_periodos(tmp_path):
    complete = evento()
    incomplete = deepcopy(complete)
    sides(incomplete)[0].pop("linescores")
    c, s, _ = client(tmp_path, Response(payload=scoreboard(incomplete)), Response(payload=summary(complete)))
    _, report, code = run(c)
    assert code == 0 and report["finales_completos"] == 1
    assert len(s.calls) == 2 and "summary?event=123" in s.calls[1][0]


def test_estadisticas_opt_in_no_confunde_cobertura_con_resultados(tmp_path):
    e = evento()
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=summary(e)))
    _, report, code = run(c, con_estadisticas=True)
    assert code == 0 and report["finales_completos"] == 1
    assert report["cobertura_estadisticas"]["home.robos"] == {"presentes": 0, "finales": 1}


def test_no_omite_partido_de_medianoche_eastern_que_es_ayer_colombia(tmp_path):
    e = evento(start="2025-07-04T04:30Z")
    outside = evento("124", start="2025-07-04T06:00Z")
    c, _, _ = client(tmp_path, Response(payload=scoreboard()), Response(payload=scoreboard(e, outside)))
    _, report, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3))
    assert code == 0 and report["partidos_exportados"] == 1
    assert report["eventos_fuera_ventana"] == 1 and len(report["ventanas_verificadas"]) == 2


@pytest.mark.parametrize("response", [Response(403), Response(payload={}), Response(payload=scoreboard(*([evento()] * 500)))])
def test_pipeline_fuente_fallida_no_declara_vacio_ni_exito(tmp_path, response):
    c, _, _ = client(tmp_path, response)
    folder, report, code = run(c)
    assert code == 3 and report["estado"] == "INCOMPLETO"
    assert report["ventanas_pendientes"] == ["2025-07-03"]
    assert report["ventanas_sin_eventos"] == []
    assert (folder / "reporte.json").exists()


def test_interrupcion_y_error_interno_tienen_reporte_y_codigo_no_cero(tmp_path):
    c, _, _ = client(tmp_path)
    c.obtener = lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt())
    _, report, code = run(c)
    assert code == 130 and report["estado"] == "INTERRUMPIDO"
    c.obtener = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("sintetico"))
    _, report, code = run(c)
    assert code == 4 and report["estado"] == "ERROR_INTERNO"


def test_cli_plan_no_red_ni_directorio(tmp_path, capsys):
    output = tmp_path / "no_debe_crearse"
    assert main(["--desde", "2025-07-03", "--hasta", "2025-07-03", "--salida", str(output)]) == 0
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["modo"] == "PLAN_SIN_RED"


def test_cli_real_offline_desde_cualquier_cwd(tmp_path):
    archive = Archivo(tmp_path)
    archive.guardar(url_consulta("scoreboard", "20250703"), bytes_json(scoreboard(evento())), datetime.now(timezone.utc).isoformat())
    script = Path(__file__).resolve().parents[2] / "scripts" / "scraper_wnba.py"
    result = subprocess.run([sys.executable, str(script), "--desde", "2025-07-03", "--hasta", "2025-07-03",
                             "--zona", "America/New_York", "--offline", "--salida", str(tmp_path)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["partidos"] == 1


def test_cli_no_escribe_en_repositorio_y_no_compite_por_carpeta(tmp_path):
    repo = Path(__file__).resolve().parents[3]
    with pytest.raises(SystemExit) as exc:
        main(["--desde", "2025-07-03", "--hasta", "2025-07-03", "--fetch", "--salida", str(repo / "no_crear")])
    assert exc.value.code == 2 and not (repo / "no_crear").exists()
    with bloqueo(tmp_path):
        assert main(["--desde", "2025-07-03", "--hasta", "2025-07-03", "--offline", "--salida", str(tmp_path)]) == 3


@pytest.mark.parametrize("value", ["=HYPERLINK(x)", "+command", "-formula", "@SUM(x)", " =formula"])
def test_csv_no_ejecuta_formulas_de_texto_fuente(value):
    assert celda_csv(value).startswith("'")


def test_final_con_fecha_posterior_a_observacion_no_es_evidencia(tmp_path):
    c, _, _ = client(tmp_path, Response(payload=scoreboard(evento())))
    c.ahora = lambda: datetime(2025, 7, 2, tzinfo=timezone.utc)
    _, report, code = run(c)
    assert code == 2 and report["partidos_exportados"] == 0


def test_reanudacion_tras_presupuesto_no_repite_respuestas_validas(tmp_path):
    c, _, _ = client(tmp_path, Response(payload=scoreboard(evento())), max_requests=1)
    folder, report, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3))
    assert code == 3 and report["partidos_exportados"] == 1
    assert report["ventanas_pendientes"] == ["2025-07-04"]
    resumed, session, _ = client(tmp_path, Response(payload=scoreboard()))
    again, report2, code2 = ejecutar(resumed, desde=date(2025,7,3), hasta=date(2025,7,3))
    assert code2 == 0 and len(session.calls) == 1 and "20250704" in session.calls[0][0]
    assert (folder / "partidos.jsonl").read_bytes() == (again / "partidos.jsonl").read_bytes()


def test_datos_ajenos_fuera_de_ventana_tambien_se_apartan(tmp_path):
    other = evento("999", start="2025-08-03T23:00Z")
    other["uid"] = "s:40~l:46~e:999"
    c, _, _ = client(tmp_path, Response(payload=scoreboard(evento(), other)))
    _, report, code = run(c)
    assert code == 2 and report["partidos_exportados"] == 1 and report["ids_cuarentena"] == ["999"]


def test_reprogramacion_conflictiva_fuera_ventana_no_conserva_final_viejo(tmp_path):
    c, _, _ = client(tmp_path, Response(payload=scoreboard(evento())),
                     Response(payload=scoreboard(evento(start="2025-07-04T23:00Z"))))
    _, report, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3))
    assert code == 2 and report["partidos_exportados"] == 0


@pytest.mark.parametrize("mutation", [
    lambda e: sides(e)[0].update(homeAway=[]),
    lambda e: e["competitions"][0]["status"]["type"].update(name=[]),
    lambda e: e["competitions"][0]["status"]["type"].update(state=[]),
    lambda e: e["status"].update(period=5),
])
def test_cambios_de_esquema_se_apartan_sin_error_interno(tmp_path, mutation):
    e = evento()
    mutation(e)
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)))
    _, report, code = run(c)
    assert code == 2 and report["incidencias_cuarentena"] == 1

# Regresiones de la descarga histórica real y tolerancia a fallos de WNBA v2.
@pytest.mark.parametrize('tid,abbr', [('14','RD16'), ('15','QTR'), ('16','SEMI'), ('17','FINAL')])
def test_rondas_postseason_conservan_fase_y_etiqueta(tid, abbr):
    e = evento()
    e['season']['type'] = 3
    e['competitions'][0]['type'] = {'id': tid, 'abbreviation': abbr}
    record = normalizar(e)
    assert record['fase'] == 'POST'
    assert record['tipo_competicion_fuente'] == abbr
    e['season']['type'] = 2
    with pytest.raises(ContratoError, match='RONDA_FUERA_POSTEMPORADA'):
        normalizar(e)


def test_allstar_permanece_apartado_de_partidos_wnba_estandar():
    e = evento()
    e['competitions'][0]['type'] = {'id': '4', 'abbreviation': 'ALLSTAR'}
    with pytest.raises(ContratoError, match='TIPO_COMPETICION_NO_SOPORTADO'):
        normalizar(e)


def test_404_summary_conserva_resultado_y_continua_otros_partidos_y_dias(tmp_path):
    a, b = evento(), evento('124')
    c, session, _ = client(tmp_path, Response(payload=scoreboard(a, b)), Response(404),
                            Response(payload=summary(b)), Response(payload=scoreboard()))
    folder, report, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3), con_estadisticas=True)
    assert code == 2 and report['estado'] == 'COMPLETO_CON_INCIDENCIAS'
    assert report['recorrido_completo'] and report['resultados_pendientes'] == 0
    assert report['partidos_exportados'] == 2 and report['finales_completos'] == 2
    assert report['ventanas_pendientes'] == [] and report['detalles_pendientes'] == 1
    pending = [json.loads(x) for x in (folder / 'pendientes.jsonl').read_text().splitlines()]
    assert pending[0]['source_game_id'] == '123' and pending[0]['http_status'] == 404
    assert not pending[0]['reintentar']
    assert len(session.calls) == 4
    for line in (folder / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ')
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest


def test_sin_periodos_y_summary_404_no_fabrica_final_y_continua(tmp_path):
    a, b = evento(), evento('124')
    sides(a)[0].pop('linescores')
    c, _, _ = client(tmp_path, Response(payload=scoreboard(a, b)), Response(404))
    folder, report, code = run(c)
    rows = [json.loads(x) for x in (folder / 'partidos.jsonl').read_text().splitlines()]
    assert code == 3 and [x['source_game_id'] for x in rows] == ['124']
    assert report['ids_cuarentena'] == [] and report['detalles_pendientes'] == 1


@pytest.mark.parametrize('response', [Response(404), Response(503), requests.ConnectionError(),
                                     Response(raw=b'broken'), Response(payload={})])
def test_dia_fallido_no_impide_descargar_dia_siguiente(tmp_path, response):
    c, _, _ = client(tmp_path, response, Response(payload=scoreboard()), intentos=1)
    _, report, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3))
    assert code == 3
    assert report['ventanas_verificadas'] == ['2025-07-04']
    assert report['ventanas_pendientes'] == ['2025-07-03']
    assert report['ventanas_sin_eventos'] == ['2025-07-04']


def test_ronda_recupera_dia_transitorio_sin_repetir_dias_correctos(tmp_path):
    c, session, clock = client(tmp_path, Response(503), Response(payload=scoreboard()),
                              Response(payload=scoreboard(evento())), intentos=1)
    _, report, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3), rondas=3, espera_rondas=7)
    assert code == 0 and report['partidos_exportados'] == 1
    assert report['rondas_ejecutadas'] == 2 and report['consultas_pendientes'] == 0
    assert [x[0].split('dates=')[1][:8] for x in session.calls] == ['20250703', '20250704', '20250703']
    assert 7 in clock.waits


def test_ronda_recupera_estadisticas_sin_confundir_mejora_con_duplicado(tmp_path):
    e = evento()
    s = summary(e)
    s['boxscore']['teams'] = [{'team': {'id': '1'}, 'statistics': [{'name': 'assists', 'displayValue': '12'}]}]
    c, session, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(503), Response(payload=s), intentos=1)
    folder, report, code = run(c, con_estadisticas=True, rondas=2, espera_rondas=0)
    record = json.loads((folder / 'partidos.jsonl').read_text())
    assert code == 0 and report['consultas_pendientes'] == 0
    assert record['estadisticas']['home']['asistencias'] == 12
    assert len(record['evidencia']) == 2 and report['duplicados_identicos'] == 0
    assert len(session.calls) == 3
    assert len((folder / 'incidencias.jsonl').read_text().splitlines()) == 1


def test_estadistica_negativa_no_elimina_resultado_ni_se_convierte_a_cero(tmp_path):
    e = evento()
    s = summary(e)
    s['boxscore']['teams'] = [{'team': {'id': '1'}, 'statistics': [{'name': 'teamTurnovers', 'displayValue': '-13'}]}]
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=s))
    folder, report, code = run(c, con_estadisticas=True)
    record = json.loads((folder / 'partidos.jsonl').read_text())
    assert code == 2 and report['partidos_exportados'] == 1 and report['detalles_pendientes'] == 0
    assert report['partidos_con_advertencias_estadisticas'] == 1
    assert record['incidencias_estadisticas'][0]['valor_fuente'] == '-13'
    assert record['local_total'] == 81 and record['estadisticas']['home']['perdidas_equipo'] is None
    assert report['incidencias_cuarentena'] == 0


def test_summary_con_otro_marcador_no_sobrescribe_resultado_valido(tmp_path):
    e = evento()
    s = summary(e)
    sides(s['header'])[0]['score'] = '999'
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=s))
    folder, report, code = run(c, con_estadisticas=True)
    record = json.loads((folder / 'partidos.jsonl').read_text())
    assert code == 2 and record['local_total'] == 81 and len(record['evidencia']) == 2
    assert report['detalles_pendientes'] == 1


def test_offline_incompleto_recorre_todo_y_no_intenta_red(tmp_path):
    Archivo(tmp_path).guardar(url_consulta('scoreboard','20250704'), bytes_json(scoreboard()), NOW.isoformat())
    c, session, _ = client(tmp_path, offline=True)
    _, report, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3), rondas=3)
    assert code == 3 and report['ventanas_verificadas'] == ['2025-07-04']
    assert report['rondas_ejecutadas'] == 1 and not session.calls


def test_reanudacion_historica_dias_despues_no_redescarga_respuestas(tmp_path):
    first, _, _ = client(tmp_path, Response(payload=scoreboard(evento())))
    folder, _, code = run(first)
    assert code == 0
    resumed, session, _ = client(tmp_path)
    resumed.ahora = lambda: NOW + timedelta(days=180)
    again, report, code = run(resumed)
    assert code == 0 and not session.calls and report['contadores_http']['cache_hits'] == 1
    assert (folder / 'partidos.jsonl').read_bytes() == (again / 'partidos.jsonl').read_bytes()


@pytest.mark.parametrize('code', [401, 403, 302, 429])
def test_bloqueos_globales_no_se_ocultan_como_partidos_pendientes(tmp_path, code):
    c, session, _ = client(tmp_path, Response(payload=scoreboard(evento())), Response(code))
    _, report, result = run(c, con_estadisticas=True, rondas=3)
    assert result == 3 and report['estado'] == 'INCOMPLETO' and len(session.calls) == 2
    assert report['ventanas_pendientes'] == ['2025-07-03']


def test_checkpoint_exporta_resultados_antes_de_interrupcion_abrupta(tmp_path):
    c, _, _ = client(tmp_path, Response(payload=scoreboard(evento())))
    inspected = []
    def inspect(progress):
        folder = Path(progress['ejecucion'])
        state = json.loads((folder / 'reporte.json').read_text())
        assert state['estado'] == 'EN_CURSO' and state['partidos_exportados'] == 1
        assert (folder / 'partidos.jsonl').read_text()
        inspected.append(True)
        raise KeyboardInterrupt
    folder, report, code = run(c, checkpoint_cada=1, progreso=inspect)
    assert inspected and code == 130 and report['partidos_exportados'] == 1
    assert json.loads((folder / 'reporte.json').read_text())['estado'] == 'INTERRUMPIDO'


def test_presupuesto_global_entre_dos_partidos_conserva_primero(tmp_path):
    a, b = evento(), evento('124')
    c, session, _ = client(tmp_path, Response(payload=scoreboard(a,b)), Response(payload=summary(a)), max_requests=2)
    _, report, code = run(c, con_estadisticas=True, rondas=3)
    assert code == 3 and report['partidos_exportados'] == 1 and len(session.calls) == 2
    assert 'Presupuesto' in report['error']


@pytest.mark.parametrize('kwargs', [{'rondas': 0}, {'rondas': 11}, {'espera_rondas': float('nan')},
                                     {'espera_rondas': 61}, {'checkpoint_cada': 0}])
def test_configuracion_reintentos_invalida_no_crea_ejecucion(tmp_path, kwargs):
    c, _, _ = client(tmp_path)
    with pytest.raises(ValueError):
        run(c, **kwargs)
    assert not (tmp_path / 'ejecuciones').exists()

@pytest.mark.parametrize('mode,expected', [('term',130), ('kill',9)])
def test_proceso_interrumpido_recupera_desde_archivo_durable(tmp_path, mode, expected):
    # Proceso separado: comprueba señales reales y terminación sin ejecutar finally.
    program = r'''
import os, signal, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, str(Path(sys.argv[1]).parents[1]))
from test_wnba import client, Response, scoreboard, evento
from scrapers.wnba.pipeline import ejecutar
from scripts.scraper_wnba import guardar_al_terminar
folder = Path(sys.argv[2])
c, _, _ = client(folder, Response(payload=scoreboard(evento())))
def stop(progress):
    if sys.argv[3] == 'kill':
        os._exit(9)
    os.kill(os.getpid(), signal.SIGTERM)
with guardar_al_terminar():
    _, _, code = ejecutar(c, desde=date(2025,7,3), hasta=date(2025,7,3), zona='America/New_York',
                         progreso=stop, checkpoint_cada=1000)
sys.exit(code)
'''
    result = subprocess.run([sys.executable, '-c', program, str(Path(__file__).parent), str(tmp_path), mode],
                            capture_output=True, text=True, timeout=20)
    # Windows SIGTERM termina el proceso con 15, sin ejecutar el handler POSIX.
    # El replay durable se verifica igual tras esa terminaci?n forzada.
    esperado_nativo = 15 if sys.platform == "win32" and mode == "term" else expected
    assert result.returncode == esperado_nativo, result.stderr
    replay, session, _ = client(tmp_path, offline=True)
    folder, report, code = run(replay)
    assert code == 0 and report['partidos_exportados'] == 1 and not session.calls
    assert json.loads((folder / 'partidos.jsonl').read_text())['local_total'] == 81


def test_tipo_competicion_con_cambio_de_esquema_se_aparta(tmp_path):
    e = evento()
    e['competitions'][0]['type']['abbreviation'] = []
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e,evento('124'))))
    _, report, code = run(c)
    assert code == 2 and report['ids_cuarentena'] == ['123'] and report['partidos_exportados'] == 1

@pytest.mark.parametrize('name,label', [('STATUS_POSTPONED','POSPUESTO'), ('STATUS_CANCELED','CANCELADO')])
@pytest.mark.parametrize('source_state', ['pre','post'])
def test_pospuestos_y_cancelados_archivados_no_se_confunden_con_finales(name, label, source_state):
    e = evento(state='PROGRAMADO')
    for status in (e['status'],e['competitions'][0]['status']):
        status['type'] = {'name': name, 'state': source_state, 'completed': False}
    record = normalizar(e)
    assert record['estado'] == label and not record['final_completo']
    assert record['local_total'] is None and record['ganador_id_fuente'] is None
    for status in (e['status'],e['competitions'][0]['status']):
        status['type']['completed'] = True
    with pytest.raises(ContratoError, match='ESTADO_CONTRADICTORIO'):
        normalizar(e)


def test_campo_estadistico_invalido_conserva_las_otras_metricas_y_ambos_equipos(tmp_path):
    e = evento()
    s = summary(e)
    s['boxscore']['teams'] = [
        {'team': {'id': '1'}, 'statistics': [
            {'name': 'teamTurnovers', 'displayValue': '-13'},
            {'name': 'turnovers', 'displayValue': '16'},
            {'name': 'totalTurnovers', 'displayValue': '3'},
            {'name': 'assists', 'displayValue': '25'},
            {'name': 'totalRebounds', 'displayValue': '39'}]},
        {'team': {'id': '2'}, 'statistics': [{'name': 'steals', 'displayValue': '0'}]}]
    c, _, _ = client(tmp_path, Response(payload=scoreboard(e)), Response(payload=s))
    folder, report, code = run(c, con_estadisticas=True)
    r = json.loads((folder/'partidos.jsonl').read_text())
    stats = r['estadisticas']['home']
    assert stats['asistencias'] == 25 and stats['rebotes'] == 39 and stats['perdidas_jugadoras'] == 16
    assert stats['perdidas_equipo'] is None and stats['perdidas_totales'] is None
    assert r['estadisticas']['away']['robos'] == 0
    assert code == 2 and report['estado'] == 'COMPLETO_CON_INCIDENCIAS' and report['error'] is None
    assert report['consultas_pendientes'] == report['resultados_pendientes'] == 0
    assert report['campos_estadisticos_apartados'] == 2
    warnings = [json.loads(x) for x in (folder/'advertencias_estadisticas.jsonl').read_text().splitlines()]
    assert len(warnings) == 2 and warnings[0]['source_game_id'] == '123'
    with pytest.raises(ContratoError):
        normalizar(e,s)  # El modo estricto sigue disponible.


@pytest.mark.parametrize('value',[True, '-1', '3.2', 'bad'])
def test_aislamiento_estadistico_no_inventa_enteros(value):
    e = evento()
    s = summary(e)
    s['boxscore']['teams'] = [{'team': {'id':'1'},'statistics':[
        {'name':'assists','displayValue':value},{'name':'steals','displayValue':'2'}]}]
    r = normalizar(e,s,aislar_estadisticas_invalidas=True)
    assert r['estadisticas']['home']['asistencias'] is None
    assert r['estadisticas']['home']['robos'] == 2
    assert r['incidencias_estadisticas'][0]['valor_fuente'] == value


def test_nombres_de_estado_distinguen_recorrido_completo_de_resultado_faltante(tmp_path):
    e = evento()
    sides(e)[0].pop('linescores')
    c, _, _ = client(tmp_path,Response(payload=scoreboard(e)),Response(404))
    _, report, code = run(c)
    assert report['recorrido_completo'] and report['resultados_pendientes'] == 1
    assert code == 3 and report['estado'] == 'INCOMPLETO'
