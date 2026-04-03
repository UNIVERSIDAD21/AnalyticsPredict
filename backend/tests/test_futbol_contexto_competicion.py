from datetime import datetime, timezone

from api.rutas_analisis_futbol import _obtener_partidos_equipo, _obtener_partidos_h2h


class CursorDummy:
    def __init__(self):
        self.query = ""
        self.params = []

    def execute(self, query, params):
        self.query = str(query)
        self.params = list(params)

    def fetchall(self):
        return []


def test_obtener_partidos_h2h_filtra_por_competicion_y_temporada():
    c = CursorDummy()
    _obtener_partidos_h2h(
        c,
        equipo_local_id="l",
        equipo_visitante_id="v",
        fecha_corte=datetime.now(timezone.utc),
        limite=10,
        temporada_ids=["temp-1"],
        competicion_id="comp-1",
    )
    assert "pf.competicion_id::text = %s" in c.query
    assert "pf.temporada_id::text = ANY(%s)" in c.query
    assert "comp-1" in c.params


def test_obtener_partidos_equipo_filtra_por_competicion_y_fallback_fecha():
    c = CursorDummy()
    _obtener_partidos_equipo(
        c,
        equipo_id="eq-1",
        fecha_corte=datetime.now(timezone.utc),
        limite=12,
        solo_local=True,
        temporada_ids=None,
        fecha_minima=datetime(2025, 1, 1, tzinfo=timezone.utc),
        competicion_id="comp-2",
    )
    assert "pf.competicion_id::text = %s" in c.query
    assert "pf.fecha_partido >= %s" in c.query
    assert "comp-2" in c.params
