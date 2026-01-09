import sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.modelos_peticion import PeticionCrearApuesta
from api import rutas_bitacora


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

    payload = rutas_bitacora._construir_payload_apuesta(
        peticion,
        UUID("00000000-0000-0000-0000-000000000000"),
    )

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
