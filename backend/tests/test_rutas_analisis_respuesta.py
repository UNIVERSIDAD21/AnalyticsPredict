import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.modelos_peticion import PeticionAnalisis
from api import rutas_analisis


def _peticion_base(**overrides):
    data = {
        "equipo_local": "Lakers",
        "equipo_visitante": "Heat",
        "mercado": "Q1",
        "linea": 50.5,
        "cuota_over": 1.9,
        "cuota_under": 1.9,
        "lado": "OVER",
        "modo_devig": "estricto",
    }
    data.update(overrides)
    return PeticionAnalisis(**data)


def _stub_ejecucion(monkeypatch, datos_respuesta):
    monkeypatch.setattr(rutas_analisis, "obtener_modelo", lambda: object())
    monkeypatch.setattr(rutas_analisis, "validar_equipos", lambda *args, **kwargs: None)
    monkeypatch.setattr(rutas_analisis, "analizar_partido", lambda **kwargs: object())
    monkeypatch.setattr(
        rutas_analisis,
        "resultado_a_dict",
        lambda resultado: dict(datos_respuesta),
    )
    monkeypatch.setattr(
        rutas_analisis,
        "_colectar_advertencias_resultado",
        lambda resultado: [],
    )


def test_respuesta_incluye_advertencias_root_overround_alto(monkeypatch):
    _stub_ejecucion(
        monkeypatch,
        {
            "mejor_apuesta": None,
            "mensaje_apuesta": "NO_APTO: SIN_CANDIDATOS",
            "candidatos": [],
            "advertencias": ["NO_DEBE_IR_EN_DATOS"],
        },
    )
    peticion = _peticion_base(cuota_over=1.4, cuota_under=1.4)

    respuesta = rutas_analisis.ejecutar_analisis(peticion)

    assert "OVERROUND_ALTO_REVISAR" in (respuesta.advertencias or [])
    assert "advertencias" not in respuesta.datos


def test_respuesta_advertencia_devig_estimado(monkeypatch):
    _stub_ejecucion(
        monkeypatch,
        {
            "mejor_apuesta": None,
            "mensaje_apuesta": "NO_APTO: SIN_CANDIDATOS",
            "candidatos": [],
        },
    )
    peticion = _peticion_base(cuota_under=None, modo_devig="estimado")

    respuesta = rutas_analisis.ejecutar_analisis(peticion)

    assert "DEVIG_ESTIMADO_PENALIZA" in (respuesta.advertencias or [])


def test_respuesta_no_apta_incluye_mensaje(monkeypatch):
    _stub_ejecucion(
        monkeypatch,
        {
            "mejor_apuesta": None,
            "mensaje_apuesta": "NO_APTO: EV<=0 o edge_real<=0 en todos los candidatos",
            "candidatos": [],
        },
    )
    peticion = _peticion_base(cuota_over=1.9, cuota_under=1.9)

    respuesta = rutas_analisis.ejecutar_analisis(peticion)

    assert respuesta.datos["mejor_apuesta"] is None
    assert (
        respuesta.datos["mensaje_apuesta"]
        == "NO_APTO: EV<=0 o edge_real<=0 en todos los candidatos"
    )
