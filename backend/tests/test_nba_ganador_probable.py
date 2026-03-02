from motor.nba_predictor_cuartos import calcular_prediccion_cuarto


def test_ganador_probable_equipo_cuando_media_local_superior():
    pred = calcular_prediccion_cuarto(
        cuarto='Q1',
        media_equipo=30.0,
        desviacion_equipo=6.0,
        media_rival=24.0,
        desviacion_rival=6.0,
        linea=52.5,
    )
    assert pred.ganador_probable == 'equipo'
    assert pred.probabilidad_ganador > 0.5


def test_ganador_probable_rival_cuando_media_rival_superior():
    pred = calcular_prediccion_cuarto(
        cuarto='Q1',
        media_equipo=23.0,
        desviacion_equipo=6.0,
        media_rival=29.0,
        desviacion_rival=6.0,
        linea=52.5,
    )
    assert pred.ganador_probable == 'rival'
    assert pred.probabilidad_ganador < 0.5
