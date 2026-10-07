"""Los resúmenes no imputan ganancia de apuestas pendientes o sin importe."""

import asyncio

from api import rutas_apuestas_futbol, rutas_metricas_futbol


class _CursorApuestas:
    def __init__(self, faltantes):
        self.faltantes = faltantes
        self.consultas = []

    def execute(self, query, _params=None):
        self.consultas.append(query)

    def fetchone(self):
        if "COUNT(*) as total FROM apuestas_futbol" in self.consultas[-1]:
            return {"total": 3}
        return {"total": 3, "pendientes": 1, "ganadas": 1, "perdidas": 1,
                "push": 0, "stake_total": 30, "stake_resuelto": 20,
                "ganancia_neta": 2, "ganancias_faltantes": self.faltantes}

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _CursorSistema(_CursorApuestas):
    def fetchone(self):
        query = self.consultas[-1]
        if "stake_resuelto" in query:
            return {"stake_resuelto": 20, "ganancia_neta": 2,
                    "ganancias_faltantes": self.faltantes, "ganadas": 1, "resueltas": 2}
        if "SELECT mensaje" in query:
            return None
        return {"count": 0}


class _Connection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self, **_kwargs):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Pool:
    def __init__(self, cursor):
        self.cursor = cursor

    def connection(self):
        return _Connection(self.cursor)


def test_listado_apuestas_roi_solo_resueltas_y_sin_ganancias_faltantes(monkeypatch):
    monkeypatch.setattr(rutas_apuestas_futbol, "_obtener_columnas_apuestas", lambda *_: {
        "estado", "ganancia_real", "fecha_creacion"})
    for faltantes, roi, ganancia in ((0, 10.0, 2.0), (1, None, None)):
        cursor = _CursorApuestas(faltantes)
        monkeypatch.setattr(rutas_apuestas_futbol, "obtener_pool", lambda: _Pool(cursor))
        respuesta = asyncio.run(rutas_apuestas_futbol.listar_apuestas(
            estado=None, mercado=None, desde=None, hasta=None,
            pagina=1, tamano=20, limite=None, offset=None))
        assert respuesta.resumen.roi == roi
        assert respuesta.resumen.ganancia_neta == ganancia
        assert respuesta.resumen.stake_total == 30
        assert "SUM(stake) FILTER" in cursor.consultas[-1]


def test_resumen_sistema_no_imputa_ganancia_faltante(monkeypatch):
    monkeypatch.setattr(rutas_metricas_futbol, "_resolver_columna_estado_apuestas", lambda *_: "estado")
    monkeypatch.setattr(rutas_metricas_futbol, "_resolver_columna_ganancia_apuestas", lambda *_: "ganancia")
    for faltantes, roi in ((0, 10.0), (1, None)):
        cursor = _CursorSistema(faltantes)
        monkeypatch.setattr(rutas_metricas_futbol, "obtener_pool", lambda: _Pool(cursor))
        respuesta = asyncio.run(rutas_metricas_futbol.obtener_resumen_sistema())
        assert respuesta.roi_global == roi
        assert respuesta.win_rate_global == 0.5
        assert any("SUM(stake) FILTER" in query for query in cursor.consultas)
