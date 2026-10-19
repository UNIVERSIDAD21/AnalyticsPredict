from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import numpy as np
import pytest

from motor_futbol.evaluacion import forma_temporal as ml
from motor_futbol.entrenamiento.dataset import seleccionar
from motor_futbol.tipos import TipoModelo
from scripts.desarrollar_futbol_ml import main, ruta_externa


UTC = timezone.utc


def datos():
    filas = []
    for i in range(950):
        local = str(i % 10)
        visitante = str((i + 3) % 10)
        a, b, c, d = i % 3, (i // 3) % 3, (i // 5) % 2, (i // 7) % 3
        filas.append({'id': str(i), 'fecha_partido': datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=i // 5),
            'equipo_local': local, 'equipo_visitante': visitante, 'competicion_codigo': 'ENG_PREMIER',
            'estado': 'FINALIZADO', 'valido': True, 'local_goles_1t': a, 'local_goles_2t': b,
            'visitante_goles_1t': c, 'visitante_goles_2t': d,
            'local_goles_total': a + b, 'visitante_goles_total': c + d})
    return filas


@pytest.fixture(scope='module')
def candidato():
    filas = datos()
    corte = max(p['fecha_partido'] for p in filas) + timedelta(days=1)
    return ml.construir_candidato(filas, 'goles', corte)


def futuro(candidato, ident='futuro'):
    return {**datos()[-1], 'id': ident, 'estado': 'PROGRAMADO',
            'fecha_partido': datetime.fromisoformat(candidato['corte']) + timedelta(days=2)}


def test_empates_temporales_no_consumen_outcomes_y_orden_es_determinista():
    filas = datos()[:150]
    validos, _ = seleccionar(filas, 'goles')
    a, _ = ml.historial_causal(validos, TipoModelo.GOLES)
    alterados = deepcopy(validos)
    instante = validos[100]['fecha_partido']
    for p in alterados:
        if p['fecha_partido'] == instante:
            p['local_goles_1t'] += 50
            p['local_goles_total'] += 50
    b, _ = ml.historial_causal(alterados, TipoModelo.GOLES)
    assert [f['forma'] for f in a if f['partido']['fecha_partido'] <= instante] == [
        f['forma'] for f in b if f['partido']['fecha_partido'] <= instante]
    assert a[-1]['forma'] != b[-1]['forma']
    mezclados, _ = seleccionar(list(reversed(filas)), 'goles')
    assert ml.historial_causal(mezclados, TipoModelo.GOLES)[0] == a


def test_refit_explicito_no_hereda_mae_cal_y_no_consume_futuro(candidato):
    assert candidato['estado'] == 'CANDIDATO_SOMBRA'
    assert candidato['train_seleccion']['n_partidos'] >= 500
    assert candidato['cal_seleccion']['n_partidos'] >= 100
    assert candidato['dataset_refit']['n_partidos'] > candidato['train_seleccion']['n_partidos']
    assert candidato['dataset_refit']['n_filas_diseno'] == candidato['dataset_refit']['n_partidos']
    assert candidato['train_seleccion']['fecha_max'] < candidato['cal_seleccion']['fecha_min']
    assert len(candidato['busqueda']) == 9
    assert candidato['metricas_artefacto_final'] is None and not candidato['activable']
    envenenado = futuro(candidato)
    envenenado['local_goles_1t'] = 10000
    otro = ml.construir_candidato(datos() + [envenenado], 'goles', datetime.fromisoformat(candidato['corte']))
    assert otro == candidato


def test_recarga_exacta_sin_ajuste_y_fixture_no_lee_outcomes(candidato, monkeypatch):
    original = ml.predecir(candidato, futuro(candidato))
    def prohibido(*args, **kwargs):
        raise AssertionError('Serving no debe ajustar')
    monkeypatch.setattr(ml, 'ajustar', prohibido)
    recargado = json.loads(json.dumps(candidato))
    fixture = futuro(candidato)
    fixture['local_goles_1t'] = None
    assert ml.predecir(recargado, fixture) == original
    assert len(original['features']) == len(candidato['feature_names'])
    assert np.isfinite(original['prediccion']).all()
    assert min(original['prediccion']) >= 0
    recargado['ajuste']['pesos'][0][0] += 1
    with pytest.raises(ValueError, match='hash'):
        ml.predecir(recargado, fixture)


def test_no_oculta_equipo_nuevo_ni_acepta_fechas_ambiguas(candidato):
    fixture = futuro(candidato)
    fixture['equipo_local'] = 'nuevo'
    assert ml.predecir(candidato, fixture)['motivo'] == 'EQUIPO_SIN_CINCO_ANTECEDENTES_TRAIN'
    malas = datos()
    malas[0]['fecha_partido'] = malas[0]['fecha_partido'].replace(tzinfo=None)
    with pytest.raises(ValueError, match='zona'):
        ml.construir_candidato(malas, 'goles', datetime.fromisoformat(candidato['corte']))
    with pytest.raises(ValueError, match='duplicadas'):
        ml.construir_candidato(datos() + [datos()[0]], 'goles', datetime.fromisoformat(candidato['corte']))


def test_no_baja_gates_y_ausencias_no_se_convierten_en_ceros():
    with pytest.raises(ValueError, match='rebajar'):
        replace(ml.PoliticaForma(), min_cal=99).validar()
    filas = datos()
    for p in filas[-180:]:
        p['local_goles_1t'] = None
    corte = filas[-1]['fecha_partido'] + timedelta(days=1)
    candidato = ml.construir_candidato(filas, 'goles', corte)
    assert candidato['exclusiones_datos']['target_ausente'] == 180


def cohorte_de(candidato):
    corte = datetime.fromisoformat(candidato['corte'])
    desarrollo = ml.sellar({'corte': candidato['corte'], 'fit_completed_at': (corte + timedelta(seconds=1)).isoformat(),
                            'familias': {'goles': {'candidato_final': candidato}}})
    fixture = futuro(candidato)
    nuevo = {**fixture, 'id': 'nuevo', 'equipo_local': 'nuevo'}
    ausente = {**fixture, 'id': 'sin-target'}
    inicio = corte + timedelta(days=1)
    fin = corte + timedelta(days=45)
    return ml.congelar(desarrollo, [fixture, nuevo, ausente], corte + timedelta(seconds=2), inicio, fin,
                       corte - timedelta(seconds=1))


def test_cohorte_futura_cuenta_abstenciones_y_rechaza_congelamiento_tardio(candidato):
    cohorte = cohorte_de(candidato)
    familia = cohorte['familias']['goles']
    assert len(familia['predicciones']) == 2 and len(familia['abstenciones']) == 1
    assert familia['cobertura_maxima'] == 2 / 3 and not familia['cobertura_maxima_suficiente']
    assert familia['predicciones'][0]['p_calibrada'] is None
    corte = datetime.fromisoformat(candidato['corte'])
    desarrollo = ml.sellar({'corte': candidato['corte'], 'fit_completed_at': (corte + timedelta(seconds=5)).isoformat(),
                            'familias': {'goles': {'candidato_final': candidato}}})
    with pytest.raises(ValueError, match='ajuste'):
        ml.congelar(desarrollo, [], corte + timedelta(seconds=2), corte + timedelta(days=1),
                     corte + timedelta(days=2), corte - timedelta(seconds=1))


def test_evaluacion_conserva_denominador_hash_identidad_y_n_partidos(candidato):
    cohorte = cohorte_de(candidato)
    real = {**futuro(candidato), 'estado': 'FINALIZADO'}
    ausente = {**real, 'id': 'sin-target', 'local_goles_1t': None}
    observado = datetime.fromisoformat(cohorte['fin_eval']) + timedelta(days=1)
    r = ml.evaluar_congelada(cohorte, [real, ausente], observado)['familias']['goles']
    assert r['candidatos'] == 3 and r['metricas']['n_partidos'] == 1
    assert r['cobertura_resuelta_total'] == 1 / 3
    assert r['exclusiones'] == {'target_ausente': 1} and r['abstenciones'] == 1
    assert not r['activable'] and not r['gate_estadistico_superado']
    cambio = {**real, 'competicion_codigo': 'ESP_LALIGA'}
    r = ml.evaluar_congelada(cohorte, [cambio], observado)['familias']['goles']
    assert r['exclusiones'] == {'IDENTIDAD_O_HORA_CAMBIADA': 1}
    assert 'OUTCOMES_PENDIENTES' in r['motivos_estadisticos']
    corrupta = deepcopy(cohorte)
    corrupta['familias']['goles']['predicciones'][0]['prediccion'][0] += 1
    with pytest.raises(ValueError, match='hash'):
        ml.evaluar_congelada(corrupta, [], observado)


def test_proyeccion_disparos_respeta_arco_y_total():
    ajuste = {'media': [0.], 'escala': [1.], 'pesos': [[-3., 5., 2., 7.], [0., 0., 0., 0.]]}
    assert ml.aplicar(ajuste, np.asarray([[0.]]), TipoModelo.DISPAROS).tolist() == [[0., 0., 2., 2.]]


def test_cli_declaracion_no_conecta_db_y_no_sobrescribe(tmp_path, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, 'db', None)
    path = tmp_path / 'politica.json'
    inicio = datetime.now(UTC) + timedelta(days=1)
    args = ['declarar', '--salida', str(path), '--inicio', inicio.isoformat(),
            '--fin', (inicio + timedelta(days=40)).isoformat()]
    assert main(args) == 0
    ml.verificar(json.loads(path.read_text()))
    with pytest.raises(FileExistsError):
        main(args)
    with pytest.raises(Exception, match='fuera del repositorio'):
        ruta_externa(__file__)
