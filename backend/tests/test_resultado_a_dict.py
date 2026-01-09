import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.nba_predictor_cuartos import resultado_a_dict
from motor.tipos import (
    CandidatoApuesta,
    DatosDeVig,
    FactoresConfianza,
    NivelConfianza,
    LadoApuesta,
    PerfilRiesgo,
    PrediccionCuarto,
    ResultadoAnalisis,
    ResultadoSizing,
    ScoreApuesta,
    TipoMercado,
    Ubicacion,
)


def _crear_prediccion_base() -> PrediccionCuarto:
    return PrediccionCuarto(
        cuarto="Q1",
        media_equipo=26.0,
        desviacion_equipo=5.0,
        rango_equipo=(20.0, 32.0),
        media_rival=25.0,
        desviacion_rival=5.0,
        rango_rival=(19.0, 31.0),
        media_total=51.0,
        desviacion_total=7.0,
        rango_total=(44.0, 58.0),
        linea_analizada=50.5,
        probabilidad_over=0.55,
        probabilidad_under=0.45,
        ganador_probable="equipo",
        probabilidad_ganador=0.6,
    )


def _crear_resultado_base(candidatos, mejor_apuesta, metadata=None) -> ResultadoAnalisis:
    return ResultadoAnalisis(
        equipo="Lakers",
        equipo_nombre_completo="Los Angeles Lakers",
        rival="Heat",
        rival_nombre_completo="Miami Heat",
        ubicacion=Ubicacion.LOCAL,
        fecha_analisis="2024-01-01T00:00:00",
        predicciones={"Q1": _crear_prediccion_base()},
        prediccion_juego_completo=None,
        razones=[],
        nivel_confianza=NivelConfianza.MEDIA,
        factores_confianza=FactoresConfianza(
            tamano_muestra="media",
            volatilidad="media",
            frescura_datos="alta",
            puntaje_total=2,
        ),
        analisis_mercado=None,
        sizing=None,
        mejor_apuesta=mejor_apuesta,
        candidatos=candidatos,
        es_en_vivo=False,
        cuartos_reales={},
        metadata=metadata or {"mercado": "Q1"},
    )


def test_resultado_a_dict_con_devig_exacto_y_cuotas_completas():
    datos_devig = DatosDeVig(
        metodo="exacto",
        overround=1.06,
        p_mkt_raw=0.55,
        p_mkt_fair=0.52,
        advertencias=["Devig exacto"],
    )
    score = ScoreApuesta(
        score_total=10.0,
        componentes={"ev": 2.5},
        gates_pasados=True,
        explicacion="Score OK",
        penalizaciones_aplicadas=[],
    )
    sizing = ResultadoSizing(
        kelly_full=0.1,
        kelly_fraccional=0.05,
        fraccion_kelly=0.5,
        stake=50.0,
        stake_porcentaje=5.0,
        bankroll_momento=1000.0,
        perfil_riesgo_usado=PerfilRiesgo.MEDIO,
        advertencias=["cap"],
        penalizaciones={"cap_por_apuesta": 0.1},
        aplicaron_caps=True,
    )
    candidato = CandidatoApuesta(
        cuarto="Q1",
        mercado=TipoMercado.TOTAL,
        lado=LadoApuesta.OVER,
        linea=50.5,
        probabilidad=0.55,
        media=52.0,
        desviacion=6.0,
        distancia_z=0.2,
        datos_devig=datos_devig,
        edge_real=0.03,
        ev=0.06,
        p_raw=0.52,
        p_calibrada=0.55,
        calibrador_usado="platt",
        score=score,
        sizing=sizing,
        cuota=1.9,
        cuota_over=1.9,
        cuota_under=1.95,
    )
    resultado = _crear_resultado_base([candidato], candidato)

    salida = resultado_a_dict(resultado)
    mejor = salida["mejor_apuesta"]

    assert mejor["devig_metodo"] == "exacto"
    assert mejor["cuota_over"] == 1.9
    assert mejor["cuota_under"] == 1.95
    assert isinstance(mejor["devig_advertencias"], list)
    assert isinstance(mejor["score_penalizaciones"], list)
    assert isinstance(mejor["sizing_advertencias"], list)
    assert isinstance(mejor["score_componentes"], dict)
    assert isinstance(mejor["sizing_penalizaciones"], dict)
    assert mejor["p_raw"] == 0.52
    assert mejor["p_calibrada"] == 0.55
    assert mejor["calibrador_usado"] == "platt"


def test_resultado_a_dict_con_cuota_unica_y_devig_no_aplicado():
    datos_devig = DatosDeVig(
        metodo="no_aplicado",
        overround=None,
        p_mkt_raw=0.5,
        p_mkt_fair=0.5,
        advertencias=["Sin devig exacto"],
    )
    score = ScoreApuesta(
        score_total=-5.0,
        componentes={"ev": -1.0},
        gates_pasados=True,
        explicacion="Devig no aplicado",
        penalizaciones_aplicadas=["SIN_DEVIG"],
    )
    sizing = ResultadoSizing(
        kelly_full=0.02,
        kelly_fraccional=0.01,
        fraccion_kelly=0.5,
        stake=10.0,
        stake_porcentaje=1.0,
        bankroll_momento=1000.0,
        perfil_riesgo_usado=PerfilRiesgo.CONSERVADOR,
        advertencias=["sin cuota opuesta"],
        penalizaciones={"sin_devig": 0.2},
        aplicaron_caps=False,
    )
    candidato = CandidatoApuesta(
        cuarto="Q1",
        mercado=TipoMercado.TOTAL,
        lado=LadoApuesta.UNDER,
        linea=50.5,
        probabilidad=0.45,
        media=49.0,
        desviacion=6.0,
        distancia_z=0.3,
        datos_devig=datos_devig,
        edge_real=0.0,
        ev=0.0,
        p_raw=0.45,
        p_calibrada=None,
        calibrador_usado=None,
        score=score,
        sizing=sizing,
        cuota=1.85,
        cuota_under=1.85,
    )
    resultado = _crear_resultado_base([candidato], candidato)

    salida = resultado_a_dict(resultado)
    mejor = salida["mejor_apuesta"]

    assert mejor["devig_metodo"] == "no_aplicado"
    assert mejor["devig_advertencias"] == ["Sin devig exacto"]
    assert isinstance(mejor["sizing_penalizaciones"], dict)
    assert mejor.get("cuota_over") is None
    assert mejor["p_raw"] == 0.45
    assert mejor["p_calibrada"] is None


def test_resultado_a_dict_sin_apuestas_aptas_incluye_mensaje_y_candidatos():
    datos_devig = DatosDeVig(
        metodo="estimado",
        overround=None,
        p_mkt_raw=0.55,
        p_mkt_fair=0.53,
        advertencias=["Devig estimado"],
    )
    score = ScoreApuesta(
        score_total=-1000.0,
        componentes={"ev": -3.0},
        gates_pasados=False,
        explicacion="No apto",
        penalizaciones_aplicadas=["RIESGO_ALTO"],
    )
    candidato = CandidatoApuesta(
        cuarto="Q1",
        mercado=TipoMercado.TOTAL,
        lado=LadoApuesta.OVER,
        linea=50.5,
        probabilidad=0.52,
        media=51.0,
        desviacion=8.0,
        distancia_z=0.1,
        datos_devig=datos_devig,
        edge_real=-0.01,
        ev=-0.02,
        score=score,
        sizing=None,
        cuota=1.9,
        cuota_over=1.9,
        cuota_under=1.9,
    )
    resultado = _crear_resultado_base(
        [candidato],
        None,
        metadata={"mercado": "Q1", "mensaje_apuesta": "No hay apuestas aptas."},
    )

    salida = resultado_a_dict(resultado)

    assert salida["mejor_apuesta"] is None
    assert salida["mensaje_apuesta"] == "No hay apuestas aptas."
    assert salida["candidatos"][0]["score_penalizaciones"] == ["RIESGO_ALTO"]
