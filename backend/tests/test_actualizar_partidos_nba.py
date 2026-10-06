from datetime import date

import pytest

from scripts import actualizar_partidos_nba as ingesta


def test_espn_403_se_detiene_sin_reintentos(monkeypatch):
    llamadas = []

    class Respuesta:
        status_code = 403

    monkeypatch.setattr(ingesta.requests, 'get', lambda *args, **kwargs: llamadas.append(args) or Respuesta())
    with pytest.raises(RuntimeError, match='SOURCE_UNAVAILABLE'):
        ingesta.request_json(ingesta.ESPN_SCOREBOARD, {'dates': '20261006'})
    assert len(llamadas) == 1


def test_scoreboard_consulta_dias_individuales_y_descarta_no_finalizados(monkeypatch):
    consultas = []

    def consultar(_url, params):
        consultas.append(params["dates"])
        evento = {"id": params["dates"], "date": params["dates"],
                  "status": {"type": {"completed": True}}}
        return {"events": [evento, {"id": "pendiente", "status": {"type": {"completed": False}}}]}

    monkeypatch.setattr(ingesta, "request_json", consultar)
    eventos = ingesta.fetch_events(date(2026, 10, 5), date(2026, 10, 6))
    assert consultas == ["20261005", "20261006"]
    assert [evento["id"] for evento in eventos] == consultas


def test_dry_run_reconoce_clave_natural_sin_id_espn(monkeypatch):
    fila = {"source_game_id": "espn-1", "temporada_id": "temporada-1",
            "fecha_partido": date(2026, 10, 5), "tipo_partido": "PRE",
            "equipo_local_id": "local-1", "equipo_visitante_id": "visitante-1"}
    clave = (fila["temporada_id"], fila["fecha_partido"], fila["tipo_partido"],
             fila["equipo_local_id"], fila["equipo_visitante_id"])
    monkeypatch.setattr(ingesta, "existing_keys", lambda _conn, _records: (set(), {clave}))
    assert ingesta.upsert_records(None, [fila], dry_run=True) == {
        "found": 1, "inserted": 0, "existing": 1, "updated": 0, "failed": 0,
    }


def test_ingesta_no_sobrescribe_partido_legacy_con_clave_natural(monkeypatch):
    fila = {"source_game_id": "espn-1", "temporada_id": "temporada-1",
            "fecha_partido": date(2026, 10, 5), "tipo_partido": "PRE",
            "equipo_local_id": "local-1", "equipo_visitante_id": "visitante-1"}
    clave = (fila["temporada_id"], fila["fecha_partido"], fila["tipo_partido"],
             fila["equipo_local_id"], fila["equipo_visitante_id"])
    monkeypatch.setattr(ingesta, "existing_keys", lambda _conn, _records: (set(), {clave}))

    class Conexion:
        def cursor(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, *_args):
            raise AssertionError("La ingesta no debe escribir sobre una fila legacy")

        def commit(self):
            raise AssertionError("No debe abrir una transacción de escritura")

    assert ingesta.upsert_records(Conexion(), [fila], dry_run=False) == {
        "found": 1, "inserted": 0, "existing": 1, "updated": 0, "failed": 0,
    }
