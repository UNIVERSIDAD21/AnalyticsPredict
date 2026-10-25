import sys
import asyncio
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from api.modelos_peticion import PeticionCrearApuesta
from api import rutas_bitacora
from motor.resolucion_apuestas import resolver_apuestas


def test_construir_payload_apuesta_incluye_campos_profesionales():
    peticion = PeticionCrearApuesta(
        partido_id="test-123",
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        lado="OVER",
        linea=Decimal("52.5"),
        cuota=Decimal("1.95"),
        cuota_over=Decimal("1.95"),
        cuota_under=Decimal("1.87"),
        stake=Decimal("50"),
        probabilidad_sistema=0.56,
        confianza_sistema="MEDIA",
        valor_esperado=0.08,
        devig_metodo="exacto",
        modo_devig="estricto",
        devig_overround=1.06,
        devig_p_mkt_raw=0.52,
        devig_p_mkt_fair=0.51,
        devig_advertencias=["ok"],
        edge_real=0.04,
        score_total=8.5,
        score_componentes={"ev": 2.0, "edge_real": 1.5},
        score_explicacion="Score estable",
        score_penalizaciones=["RIESGO_ALTO"],
        kelly_full=0.12,
        kelly_fraccional=0.03,
        fraccion_kelly=0.25,
        stake_porcentaje=2.5,
        bankroll_momento=1000.0,
        perfil_riesgo_usado="MEDIO",
        sizing_advertencias=["cap"],
        sizing_penalizaciones={"cap_por_apuesta": 0.1},
        prediccion_media=55.0,
        prediccion_desviacion=6.2,
        razones=[{"tipo": "modelo", "detalle": "prueba"}],
    )

    payload = rutas_bitacora._construir_payload_apuesta(peticion)

    claves_esperadas = {
        "devig_overround",
        "devig_p_mkt_raw",
        "devig_p_mkt_fair",
        "devig_advertencias",
        "edge_real",
        "score_total",
        "score_componentes",
        "score_explicacion",
        "score_penalizaciones",
        "kelly_full",
        "kelly_fraccional",
        "fraccion_kelly",
        "stake_porcentaje",
        "bankroll_momento",
        "perfil_riesgo_usado",
        "sizing_advertencias",
        "sizing_penalizaciones",
        "cuota_over",
        "cuota_under",
        "modo_devig",
        "devig_metodo",
    }

    assert claves_esperadas.issubset(payload.keys())
    assert payload["score_total"] == 8.5
    assert payload["kelly_fraccional"] == 0.03
    assert payload["stake_porcentaje"] == 2.5
    if rutas_bitacora.Jsonb is not None:
        assert isinstance(payload["score_componentes"], rutas_bitacora.Jsonb)
        assert isinstance(payload["sizing_penalizaciones"], rutas_bitacora.Jsonb)
        assert isinstance(payload["razones"], rutas_bitacora.Jsonb)
    else:
        assert isinstance(payload["score_componentes"], str)
        assert isinstance(payload["sizing_penalizaciones"], str)
        assert isinstance(payload["razones"], str)

    assert payload["devig_advertencias"] == ["ok"]
    assert payload["score_penalizaciones"] == ["RIESGO_ALTO"]
    assert payload["sizing_advertencias"] == ["cap"]


class _CursorGuardarEuro:
    def __init__(self, competicion_codigo="euroleague"):
        self.competicion_codigo = competicion_codigo
        self.insert = None
        self.fila_actual = None

    def execute(self, query, params=None):
        if "FROM competiciones_baloncesto" in query and "WHERE codigo" in query:
            self.fila_actual = {"id": UUID("00000000-0000-0000-0000-000000000101"), "nombre_corto": "EuroLeague"}
        elif "FROM partidos_baloncesto p" in query:
            self.fila_actual = {
                "competicion_id": UUID("00000000-0000-0000-0000-000000000101"),
                "codigo": self.competicion_codigo,
                "fecha_partido": date(2026, 10, 22),
                "equipo_local": "Real Madrid",
                "equipo_visitante": "Maccabi",
            }
        elif "INSERT INTO apuestas" in query:
            self.insert = (query, params)
            self.fila_actual = {
                "id": UUID("00000000-0000-0000-0000-000000000201"),
                "partido_id": UUID("00000000-0000-0000-0000-000000000301"),
                "competicion_id": UUID("00000000-0000-0000-0000-000000000101"),
                "competicion_nombre": "EuroLeague",
                "equipo_local": "Real Madrid", "equipo_visitante": "Maccabi",
                "fecha_partido": date(2026, 10, 22), "mercado": "COMPLETO",
                "lado": "UNDER", "linea": Decimal("170.5"), "cuota": Decimal("1.91"),
                "stake": Decimal("25"), "probabilidad_sistema": params["probabilidad_sistema"],
                "confianza_sistema": params["confianza_sistema"], "valor_esperado": params["valor_esperado"],
                "resultado": "PENDIENTE", "ganancia": Decimal("0"),
            }
        else:
            raise AssertionError(f"Consulta inesperada en prueba sintética: {query}")

    def fetchone(self):
        return self.fila_actual

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _ConexionGuardarEuro:
    def __init__(self, cursor):
        self.cursor_sintetico = cursor

    def cursor(self, **_kwargs):
        return self.cursor_sintetico

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _PoolGuardarEuro:
    def __init__(self, cursor):
        self.cursor_sintetico = cursor

    def connection(self):
        return _ConexionGuardarEuro(self.cursor_sintetico)


def _peticion_euro(probabilidad_sistema=0.7):
    return PeticionCrearApuesta(
        partido_id="00000000-0000-0000-0000-000000000301",
        competicion_codigo="euroleague",
        equipo_local="Real Madrid", equipo_visitante="Maccabi",
        fecha_partido=date(2026, 10, 22), mercado="COMPLETO", lado="UNDER",
        linea=Decimal("170.5"), cuota=Decimal("1.91"), stake=Decimal("25"),
        probabilidad_sistema=probabilidad_sistema, confianza_sistema=None,
        valor_esperado=None, razones=[],
    )


def test_guardar_apuesta_euroliga_persiste_cuota_y_competencia_sin_confianza(monkeypatch):
    cursor = _CursorGuardarEuro()
    monkeypatch.setattr(rutas_bitacora, "obtener_pool", lambda: _PoolGuardarEuro(cursor))

    respuesta = asyncio.run(rutas_bitacora.guardar_apuesta(_peticion_euro()))

    assert cursor.insert is not None
    consulta, payload = cursor.insert
    assert "competicion_id" in consulta and "competicion_nombre" in consulta
    assert payload["cuota"] == Decimal("1.91")
    assert payload["competicion_id"] == UUID("00000000-0000-0000-0000-000000000101")
    assert payload["competicion_nombre"] == "EuroLeague"
    assert payload["probabilidad_sistema"] == 0.7
    assert payload["confianza_sistema"] is None
    assert payload["valor_esperado"] is None
    assert respuesta.apuesta.competicion_nombre == "EuroLeague"
    assert respuesta.apuesta.confianza_sistema is None


def test_guardar_apuesta_euroliga_con_probabilidad_no_disponible_conserva_null(monkeypatch):
    cursor = _CursorGuardarEuro()
    monkeypatch.setattr(rutas_bitacora, "obtener_pool", lambda: _PoolGuardarEuro(cursor))

    respuesta = asyncio.run(rutas_bitacora.guardar_apuesta(_peticion_euro(probabilidad_sistema=None)))

    assert cursor.insert is not None
    _, payload = cursor.insert
    assert payload["cuota"] == Decimal("1.91")
    assert payload["probabilidad_sistema"] is None
    assert payload["confianza_sistema"] is None
    assert payload["valor_esperado"] is None
    assert respuesta.apuesta.probabilidad_sistema is None


def test_guardar_apuesta_rechaza_fixture_de_otra_competencia(monkeypatch):
    cursor = _CursorGuardarEuro(competicion_codigo="nba")
    monkeypatch.setattr(rutas_bitacora, "obtener_pool", lambda: _PoolGuardarEuro(cursor))

    try:
        asyncio.run(rutas_bitacora.guardar_apuesta(_peticion_euro()))
    except HTTPException as exc:
        assert exc.status_code == 422
        assert "no pertenece" in exc.detail
    else:
        raise AssertionError("No se rechazó el fixture cruzado")

    assert cursor.insert is None


class _CursorResolverNBA:
    def __init__(self):
        self.consultas = []

    def execute(self, query, _params=None):
        self.consultas.append(query)

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _ConexionResolverNBA:
    def __init__(self, cursor):
        self.cursor_sintetico = cursor

    def cursor(self, **_kwargs):
        return self.cursor_sintetico

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _PoolResolverNBA:
    def __init__(self, cursor):
        self.cursor_sintetico = cursor

    def connection(self):
        return _ConexionResolverNBA(self.cursor_sintetico)


def test_resolvedor_nba_no_toca_apuestas_de_euroliga():
    cursor = _CursorResolverNBA()

    resumen = resolver_apuestas(pool=_PoolResolverNBA(cursor))

    assert resumen.resueltas == 0
    assert len(cursor.consultas) == 1
    assert all("competiciones_baloncesto" in consulta for consulta in cursor.consultas)
    assert all("COALESCE(cp.codigo, ca.codigo, 'nba')=%s" in consulta for consulta in cursor.consultas)
