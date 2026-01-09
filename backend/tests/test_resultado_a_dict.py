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


def test_resultado_a_dict_serializa_mejor_apuesta_con_shape_profesional():
    datos_devig = DatosDeVig(
        metodo="no_aplicado",
        overround=None,
        p_mkt_raw=0.5,
        p_mkt_fair=0.5,
        advertencias=["Sin devig"],
    )
    score = ScoreApuesta(
        score_total=10.0,
        componentes={"ev": 2.5},
        gates_pasados=True,
        explicacion="Score OK",
        penalizaciones_aplicadas=["SIN_DEVIG"],
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
        score=score,
        sizing=sizing,
        cuota=1.9,
    )
    prediccion = PrediccionCuarto(
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
    resultado = ResultadoAnalisis(
        equipo="Lakers",
        equipo_nombre_completo="Los Angeles Lakers",
        rival="Heat",
        rival_nombre_completo="Miami Heat",
        ubicacion=Ubicacion.LOCAL,
        fecha_analisis="2024-01-01T00:00:00",
        predicciones={"Q1": prediccion},
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
        mejor_apuesta=candidato,
        candidatos=[candidato],
        es_en_vivo=False,
        cuartos_reales={},
        metadata={"mercado": "Q1"},
    )

    salida = resultado_a_dict(resultado)
    mejor = salida["mejor_apuesta"]

    assert mejor["devig_advertencias"] == ["Sin devig"]
    assert mejor["score_penalizaciones"] == ["SIN_DEVIG"]
    assert mejor["sizing_advertencias"] == ["cap"]
    assert isinstance(mejor["score_componentes"], dict)
    assert isinstance(mejor["sizing_penalizaciones"], dict)
