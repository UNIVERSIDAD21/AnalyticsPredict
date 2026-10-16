from scripts.generar_reporte_forma_reciente_nba import resumen_fases


def test_regular_no_contamina_resumen_pre_y_fase_ausente_no_se_pierde():
    def fila(fase, puntos):
        return {'tipo_partido': fase, 'fecha_partido': '2026-10-15', 'hubo_overtime': False,
                **{k: puntos for k in ['puntos_q1', 'puntos_q2', 'puntos_q3', 'puntos_q4', 'puntos_total',
                                      'recibidos_q1', 'recibidos_q2', 'recibidos_q3', 'recibidos_q4', 'recibidos_total']}}
    r = resumen_fases([fila('PRE', 10), fila('REG', 90), fila('PRE', 20), fila(None, 0)])
    assert r['PRE']['n'] == 2
    assert r['PRE']['general']['5']['metricas']['puntos_q1']['promedio'] == 15
    assert r['REG']['general']['5']['metricas']['puntos_q1']['promedio'] == 90
    assert r['SIN_CLASIFICAR']['n'] == 1
