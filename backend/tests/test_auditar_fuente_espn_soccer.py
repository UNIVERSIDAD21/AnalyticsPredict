"""Contrato de fuente alternativa: final comprobable y fallos sin datos parciales."""

import pytest

from scripts.auditar_fuente_espn_soccer import (
    FuenteNoDisponible, auditar_mes, interpretar_estadisticas, interpretar_evento,
)


def _evento(*, final=True, goles_local="0", goles_visitante="2"):
    return {"id": "evento-1", "date": "2026-03-01T13:00Z",
            "status": {"type": {"name": "STATUS_FULL_TIME" if final else "STATUS_SCHEDULED",
                                "completed": final}},
            "competitions": [{"competitors": [
                {"homeAway": "home", "team": {"id": "1", "displayName": "Local"}, "score": goles_local},
                {"homeAway": "away", "team": {"id": "2", "displayName": "Visitante"}, "score": goles_visitante},
            ]}]}


def test_cero_real_solo_en_final_y_zona_utc():
    final = interpretar_evento(_evento(), "esp.1")
    assert final["final_acreditado"] is True
    assert final["local_goles"] == 0
    assert final["inicio_utc"] == "2026-03-01T13:00:00+00:00"
    programado = interpretar_evento(_evento(final=False), "esp.1")
    assert programado["local_goles"] is None
    with pytest.raises(FuenteNoDisponible):
        interpretar_evento(_evento(goles_local=None), "esp.1")


def test_estadisticas_solo_completas_en_ambos_equipos():
    evento = interpretar_evento(_evento(), "esp.1")
    boxscore = {"boxscore": {"teams": [
        {"team": {"id": "1"}, "statistics": [
            {"name": "wonCorners", "displayValue": "0"},
            {"name": "totalShots", "displayValue": "17"}]},
        {"team": {"id": "2"}, "statistics": [
            {"name": "wonCorners", "displayValue": "3"},
            {"name": "totalShots", "displayValue": "9"}]},
    ]}}
    stats = interpretar_estadisticas(boxscore, evento)
    assert (stats["local_corners"], stats["visitante_corners"]) == (0, 3)
    assert stats["disparos_completos"] is True
    assert stats["disparos_arco_completos"] is False
    assert stats["local_disparos_arco"] is None


class _Response:
    def __init__(self, status, payload=None):
        self.status_code = status
        self.payload = payload

    def json(self):
        return self.payload


class _Session:
    def __init__(self, respuesta):
        self.headers = {}
        self.respuesta = respuesta
        self.calls = 0

    def get(self, *_args, **_kwargs):
        self.calls += 1
        return self.respuesta


def test_403_termina_sin_reintentar_ni_etiquetar_no_data():
    sesion = _Session(_Response(403))
    with pytest.raises(FuenteNoDisponible, match="HTTP 403"):
        auditar_mes("laliga", "202603", session=sesion)
    assert sesion.calls == 1


def test_200_vacio_vs_contrato_roto():
    assert auditar_mes("laliga", "202603", session=_Session(_Response(200, {"events": []})))["estado"] == "NO_DATA"
    with pytest.raises(FuenteNoDisponible):
        auditar_mes("laliga", "202603", session=_Session(_Response(200, {})))
