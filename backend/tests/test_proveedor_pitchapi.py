import pytest
from scripts.auditar_catalogo_pitchapi import _guardar_sin_sobrescribir, main

from servicios.proveedor_pitchapi import (
    AccesoDenegadoPitchAPI,
    ClientePitchAPI,
    ContratoPitchAPI,
    ErrorProveedorPitchAPI,
    interpretar_partido_liga_pitchapi,
)


class Response:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class Session:
    def __init__(self, response):
        self.headers = {}
        self.response = response
        self.calls = []
        self.closed = False

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response

    def close(self):
        self.closed = True


def test_cliente_usa_host_fijo_y_no_sigue_redirecciones():
    session = Session(Response(payload={"data": {"leagues": []}}))
    with ClientePitchAPI("secreto-de-prueba", session=session, intervalo_minimo=0) as cliente:
        assert cliente.listar_ligas() == []

    (args, kwargs), = session.calls
    assert args[0] == "https://api.pitchapi.dev/v1/leagues"
    assert kwargs["allow_redirects"] is False
    assert session.headers["X-API-KEY"] == "secreto-de-prueba"
    assert session.closed is True


def test_cliente_acepta_ids_opacos_del_catalogo_y_rechaza_path_traversal():
    assert ClientePitchAPI.validar_id("m_Ab12Z9") == "m_Ab12Z9"
    assert ClientePitchAPI.validar_id("eng-premier_A1b2C3") == "eng-premier_A1b2C3"
    with pytest.raises(ValueError, match="ID PitchAPI"):
        ClientePitchAPI.validar_id("../m_Ab12Z9")
    with pytest.raises(ValueError, match="Ruta PitchAPI"):
        ClientePitchAPI._validar_path("/v1/../matches/m_Ab12Z9")


def test_interpretar_fila_partido_conserva_orden_estado_fecha_y_score():
    partido = interpretar_partido_liga_pitchapi(
        "l_4Kd0Wq",
        {
            "id": "m_B8x2K9",
            "time_utc": "2025-11-09T16:30:00Z",
            "status": "finished",
            "home_team": {"id": "t_9aB2xQ", "name": "Manchester City"},
            "away_team": {"id": "t_2mLp7C", "name": "Manchester United"},
            "score_home": 3,
            "score_away": 1,
        },
    )
    assert partido.evento_id == "m_B8x2K9"
    assert partido.competicion_id == "l_4Kd0Wq"
    assert partido.equipo_local_id == "t_9aB2xQ"
    assert partido.equipo_visitante_id == "t_2mLp7C"
    assert partido.goles_local == 3 and partido.goles_visitante == 1
    assert partido.inicio_utc.utcoffset().total_seconds() == 0


def test_interpretar_partido_rechaza_score_parcial():
    with pytest.raises(ContratoPitchAPI, match="parcialmente ausente"):
        interpretar_partido_liga_pitchapi(
            "l_4Kd0Wq",
            {
                "id": "m_B8x2K9",
                "time_utc": "2025-11-09T16:30:00Z",
                "status": "finished",
                "home_team": {"id": "t_9aB2xQ"},
                "away_team": {"id": "t_2mLp7C"},
                "score_home": 1,
                "score_away": None,
            },
        )


def test_cliente_no_reintenta_ni_expone_clave_cuando_acceso_es_denegado():
    session = Session(Response(status_code=403))
    cliente = ClientePitchAPI("secreto-de-prueba", session=session, intervalo_minimo=0)
    with pytest.raises(AccesoDenegadoPitchAPI) as error:
        cliente.obtener_estadisticas("m_Ab12Z9")

    assert error.value.status_code == 403
    assert "secreto-de-prueba" not in str(error.value)
    assert len(session.calls) == 1


@pytest.mark.parametrize(
    "response",
    [
        Response(status_code=302, headers={"Location": "https://other.invalid/"}),
        Response(payload={"error": {"code": "bad-shape"}}),
        Response(payload=ValueError("bad json")),
    ],
)
def test_cliente_rechaza_redireccion_json_invalido_y_sobre_erroneo(response):
    session = Session(response)
    cliente = ClientePitchAPI("secreto-de-prueba", session=session, intervalo_minimo=0)
    with pytest.raises(ErrorProveedorPitchAPI):
        cliente.get_data("/v1/leagues")
    assert len(session.calls) == 1


def test_cliente_rechaza_respuesta_json_con_data_de_tipo_invalido():
    session = Session(Response(payload={"data": []}))
    cliente = ClientePitchAPI("secreto-de-prueba", session=session, intervalo_minimo=0)
    with pytest.raises(ContratoPitchAPI, match="sobre JSON"):
        cliente.get_data("/v1/leagues")


def test_auditor_no_usa_archivo_si_falta_clave_y_no_imprime_valor(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("PITCHAPI_API_KEY", raising=False)
    destino = tmp_path / "pitchapi.json"
    with pytest.raises(SystemExit):
        main(["--out", str(destino)])
    assert not destino.exists()
    assert "PITCHAPI_API_KEY" in capsys.readouterr().err


def test_evidencia_se_escribe_con_modo_privado_y_no_sobrescribe(tmp_path):
    destino = tmp_path / "subdir" / "evidencia.json"
    _guardar_sin_sobrescribir(destino, {"sample": 1})
    antes = destino.read_text(encoding="utf-8")
    assert destino.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        _guardar_sin_sobrescribir(destino, {"sample": 2})
    assert destino.read_text(encoding="utf-8") == antes
