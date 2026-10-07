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


def test_final_nba_exige_marcador_y_cuartos_acreditados():
    ctx = ingesta.DbContext('comp', 'temporada', '2026-27', {'LCL': 'local', 'VIS': 'visitante'}, {})
    evento = {
        'id': 'espn-1', 'date': '2026-10-06T23:00Z', 'season': {'type': 1},
        'competitions': [{'competitors': [
            {'homeAway': 'home', 'team': {'abbreviation': 'LCL'}, 'score': '0',
             'linescores': [{'value': 0}] * 4},
            {'homeAway': 'away', 'team': {'abbreviation': 'VIS'}, 'score': '99',
             'linescores': [{'value': 25}, {'value': 25}, {'value': 25}, {'value': 24}]},
        ]}],
    }
    with pytest.raises(ValueError, match='no positivo'):
        ingesta.event_to_record(evento, ctx)
    evento['competitions'][0]['competitors'][0]['score'] = '100'
    evento['competitions'][0]['competitors'][0]['linescores'] = [{'value': 25}] * 4
    assert ingesta.event_to_record(evento, ctx)['tipo_partido'] == 'PRE'
    evento['competitions'][0]['competitors'][0]['linescores'] = [{'value': 25}] * 3
    with pytest.raises(ValueError, match='faltan cuartos'):
        ingesta.event_to_record(evento, ctx)
    evento['competitions'][0]['competitors'][0]['linescores'] = [{'value': 25}] * 4
    evento['competitions'][0]['competitors'][0]['score'] = '101'
    with pytest.raises(ValueError, match='overtime sin líneas'):
        ingesta.event_to_record(evento, ctx)


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
    monkeypatch.setattr(ingesta, "existing_keys", lambda _conn, _records: (set(), set(), {clave}))
    assert ingesta.upsert_records(None, [fila], dry_run=True) == {
        "found": 1, "inserted": 0, "existing": 1, "updated": 0, "failed": 0,
    }


def test_ingesta_no_sobrescribe_partido_legacy_con_clave_natural(monkeypatch):
    fila = {"source_game_id": "espn-1", "temporada_id": "temporada-1",
            "fecha_partido": date(2026, 10, 5), "tipo_partido": "PRE",
            "equipo_local_id": "local-1", "equipo_visitante_id": "visitante-1"}
    clave = (fila["temporada_id"], fila["fecha_partido"], fila["tipo_partido"],
             fila["equipo_local_id"], fila["equipo_visitante_id"])
    monkeypatch.setattr(ingesta, "existing_keys", lambda _conn, _records: (set(), set(), {clave}))

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


def test_ingesta_no_duplica_id_espn_legacy_si_fecha_natural_difiere(monkeypatch):
    fila = {"source_game_id": "401810975", "temporada_id": "temporada-1",
            "fecha_partido": date(2026, 4, 4), "tipo_partido": "REG",
            "equipo_local_id": "local-1", "equipo_visitante_id": "visitante-1"}
    # La fila legacy es del 3 de abril, pero ESPN la fecha en UTC el día 4.
    monkeypatch.setattr(ingesta, "existing_keys", lambda _conn, _records: (set(), {"401810975"}, set()))

    class Conexion:
        def cursor(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, *_args):
            raise AssertionError("No insertar ni modificar fila legacy con ID ESPN")

        def commit(self):
            raise AssertionError("No abrir escritura")

    esperado = {"found": 1, "inserted": 0, "existing": 1, "updated": 0, "failed": 0}
    assert ingesta.upsert_records(None, [fila], dry_run=True) == esperado
    assert ingesta.upsert_records(Conexion(), [fila], dry_run=False) == esperado
