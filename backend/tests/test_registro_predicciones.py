# -*- coding: utf-8 -*-

from datetime import date
from uuid import UUID, uuid4

from motor.registro_predicciones import registrar_prediccion


class FakeCursor:
    def __init__(self, store, fail=False):
        self._store = store
        self._row = None
        self._fail = fail

    def execute(self, _query, params):
        if self._fail:
            raise RuntimeError("DB down")
        key = (
            params[0],
            params[6],
            params[7],
            params[8],
            params[10],
            params[11],
            params[12],
        )
        if key in self._store:
            self._row = None
        else:
            nuevo_id = uuid4()
            self._store[key] = nuevo_id
            self._row = (nuevo_id,)

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, store, fail=False):
        self._store = store
        self._fail = fail

    def cursor(self):
        return FakeCursor(self._store, fail=self._fail)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, store, fail=False):
        self._store = store
        self._fail = fail

    def connection(self):
        return FakeConnection(self._store, fail=self._fail)


def _base_kwargs():
    return {
        "partido_id": UUID("11111111-1111-1111-1111-111111111111"),
        "temporada_id": UUID("22222222-2222-2222-2222-222222222222"),
        "equipo_local_id": UUID("33333333-3333-3333-3333-333333333333"),
        "equipo_visitante_id": UUID("44444444-4444-4444-4444-444444444444"),
        "fecha_partido": date(2024, 1, 1),
        "tipo_partido": "REG",
        "mercado": "Q1",
        "lado": "OVER",
        "linea": 210.5,
        "linea_es_sintetica": False,
        "origen": "API_USUARIO",
        "modelo_version_id": 1,
        "calibrador_id": None,
        "media_predicha": 110.2,
        "desviacion_predicha": 8.1,
        "p_raw": 0.62,
        "cuota": 1.9,
        "cuota_over": 1.9,
        "cuota_under": 1.9,
    }


def test_registro_idempotente_por_llave_natural():
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    primero = registrar_prediccion(pool=pool, **kwargs)
    segundo = registrar_prediccion(pool=pool, **kwargs)

    assert primero is not None
    assert segundo is None


def test_registro_con_modelo_version_distinta_inserta():
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    primero = registrar_prediccion(pool=pool, **kwargs)
    segundo = registrar_prediccion(pool=pool, **{**kwargs, "modelo_version_id": 2})

    assert primero is not None
    assert segundo is not None
    assert primero != segundo


def test_registro_con_calibrador_distinto_inserta():
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    primero = registrar_prediccion(pool=pool, **kwargs)
    segundo = registrar_prediccion(
        pool=pool,
        **{**kwargs, "calibrador_id": UUID("55555555-5555-5555-5555-555555555555")},
    )

    assert primero is not None
    assert segundo is not None
    assert primero != segundo


def test_registro_falla_sin_romper_flujo():
    store = {}
    pool = FakePool(store, fail=True)
    kwargs = _base_kwargs()

    resultado = registrar_prediccion(pool=pool, **kwargs)

    assert resultado is None
