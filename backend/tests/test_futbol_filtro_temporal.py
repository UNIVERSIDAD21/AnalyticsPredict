import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.schemas_futbol import AnalisisRequest
from api import rutas_analisis_futbol as raf


class CursorFake:
    def __init__(self, fetchall_responses=None):
        self._responses = list(fetchall_responses or [])
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params or []))

    def fetchall(self):
        if self._responses:
            return self._responses.pop(0)
        return []


def test_request_acepta_temporadas_y_bloquea_conflicto_con_fecha_minima():
    req = AnalisisRequest(partido_id="11111111-1111-1111-1111-111111111111", temporadas=["2025/2026"])
    assert req.temporadas == ["2025/2026"]

    with pytest.raises(ValueError):
        AnalisisRequest(
            partido_id="11111111-1111-1111-1111-111111111111",
            temporadas=["2025/2026"],
            fecha_minima="2025-01-01T00:00:00Z",
        )


def test_resolver_filtro_temporal_con_temporadas_explicitas():
    cursor = CursorFake(fetchall_responses=[[{"id": "t1", "nombre": "2025/2026"}]])
    req = AnalisisRequest(partido_id="11111111-1111-1111-1111-111111111111", temporadas=["2025/2026"])

    res = raf._resolver_filtro_temporal_futbol(
        cursor,
        request=req,
        competicion_id="comp-1",
        fecha_corte=datetime(2026, 4, 3, tzinfo=timezone.utc),
    )

    assert res["estrategia"] == "temporadas_explicitas"
    assert res["temporada_ids"] == ["t1"]
    assert res["fecha_minima"] is None


def test_resolver_filtro_temporal_default_activa_mas_anterior():
    cursor = CursorFake(fetchall_responses=[[{"id": "t2", "nombre": "2025/2026"}, {"id": "t1", "nombre": "2024/2025"}]])
    req = AnalisisRequest(partido_id="11111111-1111-1111-1111-111111111111")

    res = raf._resolver_filtro_temporal_futbol(
        cursor,
        request=req,
        competicion_id="comp-1",
        fecha_corte=datetime(2026, 4, 3, tzinfo=timezone.utc),
    )

    assert res["estrategia"] == "temporada_activa_mas_anterior"
    assert res["temporada_ids"] == ["t2", "t1"]


def test_queries_aplican_filtro_temporal_por_temporada_o_fecha():
    cursor = CursorFake(fetchall_responses=[[]])
    raf._obtener_partidos_equipo(
        cursor,
        equipo_id="eq1",
        fecha_corte=datetime(2026, 4, 3, tzinfo=timezone.utc),
        limite=50,
        temporada_ids=["t1", "t2"],
    )
    q1, p1 = cursor.calls[-1]
    assert "pf.temporada_id::text = ANY(%s)" in q1
    assert p1[-2] == ["t1", "t2"]

    cursor = CursorFake(fetchall_responses=[[]])
    raf._obtener_partidos_h2h(
        cursor,
        equipo_local_id="eq1",
        equipo_visitante_id="eq2",
        fecha_corte=datetime(2026, 4, 3, tzinfo=timezone.utc),
        limite=20,
        fecha_minima=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    q2, _ = cursor.calls[-1]
    assert "pf.fecha_partido >= %s" in q2


def test_resumen_ponderado_por_recencia_prioriza_datos_recientes():
    valores = [1.0, 5.0]
    pesos = [0.1, 1.0]
    resumen = raf._resumen_valores(valores, incluir_std=True, pesos=pesos)
    assert resumen["promedio"] > 4.0
    assert resumen["metodo_promedio"] == "ponderado_recencia"
