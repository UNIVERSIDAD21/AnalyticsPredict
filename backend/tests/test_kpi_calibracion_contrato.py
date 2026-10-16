"""Contrato de series homogéneas, muestra real, N/D y frescura sin precálculos."""
from datetime import date
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api import rutas_metricas as rutas
from backtesting.metricas import calculador


@pytest.fixture
def cliente(monkeypatch):
    filas = [(0.1, 0.9, True, None, None, None, None, None),
             (0.3, None, False, None, None, None, None, None),
             (0.8, None, True, None, None, None, None, None)]
    monkeypatch.setattr(calculador, '_obtener_predicciones', lambda *a, **kw: filas)
    def calcular(**kw):
        assert kw['persistir'] is False
        return calculador.calcular_metricas_calibracion(pool=object(), **kw)
    monkeypatch.setattr(rutas, 'calcular_metricas_calibracion', calcular)
    monkeypatch.setattr(calculador, '_persistir_metricas', lambda *a, **kw: pytest.fail('GET escribió'))
    monkeypatch.setattr(rutas, '_resolver_periodo', lambda *a, **kw: SimpleNamespace(
        inicio=date(2026, 1, 1), fin=date(2026, 1, 31),
        texto_inicio='2026-01-01', texto_fin='2026-01-31'))
    monkeypatch.setattr(rutas, '_contar_excluidos_push', lambda *a, **kw: 0)
    monkeypatch.setattr(rutas, '_contar_outcomes_nba_cero_cero', lambda *a, **kw: 0)
    monkeypatch.setattr(rutas, 'obtener_calibrador_activo', lambda **kw: None)
    monkeypatch.setattr(rutas, 'listar_alertas_calibracion', lambda **kw: [])
    monkeypatch.setattr(rutas, '_obtener_predicciones_para_curva', lambda **kw: [
        {'p_efectiva': f[0] if kw['serie'] == 'raw' else f[1], 'outcome_binario': f[2]}
        for f in filas])
    app = FastAPI()
    app.include_router(rutas.router)
    with TestClient(app) as client:
        yield client, filas


def test_series_comparten_filtros_no_denominador_ni_probabilidades(cliente):
    client, _ = cliente
    for serie, n, brier, base_rate in [('raw', 3, (.81+.09+.04)/3, 2/3),
                                      ('calibrada', 1, .01, 1)]:
        params = {'origen': 'API_USUARIO', 'mercado': 'Q1', 'serie': serie, 'modelo_version_id': 7}
        respuesta = client.get('/api/metricas/calibracion', params=params)
        assert respuesta.status_code == 200
        data = respuesta.json()
        m = data['metricas_por_mercado'][0]
        assert m['serie'] == serie and m['n_predicciones'] == n
        assert (m['n_raw'], m['n_calibradas']) == (3, 1)
        assert m['brier_score'] == pytest.approx(brier)
        assert m['base_rate'] == pytest.approx(base_rate)
        assert m['mejora_vs_raw'] is None  # Distinta cohorte: no atribuir mejora.
        assert m['suficiente_data'] is False
        assert m['n_excluidas_probabilidad'] == 3-n
        assert m['periodo'] == {'inicio': '2026-01-01', 'fin': '2026-01-31'}
        assert data['certificacion'] == 'NO_CERTIFICADO' and data['cache'] == 'SIN_CACHE'
        assert data['timestamp_calculo'].endswith('+00:00')
        curva = client.get('/api/metricas/calibracion/Q1/curva', params=params).json()
        assert curva['n_predicciones_total'] == n and curva['serie'] == serie
        assert curva['modelo_version_id'] == 7
        assert curva['n_excluidas_probabilidad'] == 3-n
        assert sum(b['n'] for b in curva['bins']) == n


def test_vacio_no_devuelve_calibracion_perfecta(cliente):
    client, filas = cliente
    filas.clear()
    data = client.get('/api/metricas/calibracion?origen=API_USUARIO&mercado=Q1').json()
    m = data['metricas_por_mercado'][0]
    assert m['n_predicciones'] == 0 and m['brier_score'] is None and m['ece'] is None
    assert m['estado_calidad'] == 'NO_EVALUABLE'
    curva = client.get('/api/metricas/calibracion/Q1/curva?origen=API_USUARIO').json()
    assert curva['n_predicciones_total'] == 0
    assert curva['ece'] is None and curva['mce'] is None
    assert curva['estado_calidad'] == 'NO_EVALUABLE'


def test_actualizar_lee_cambios_sin_cache_de_cinco_minutos(cliente):
    client, filas = cliente
    ruta = '/api/metricas/calibracion?origen=API_USUARIO&mercado=Q1'
    curva = '/api/metricas/calibracion/Q1/curva?origen=API_USUARIO'
    antes = client.get(ruta).json()['metricas_por_mercado'][0]
    ece_antes = client.get(curva).json()['ece']
    filas[0] = (.9, .9, True, None, None, None, None, None)
    despues = client.get(ruta).json()['metricas_por_mercado'][0]
    assert despues['brier_score'] < antes['brier_score']
    assert client.get(curva).json()['ece'] != ece_antes


@pytest.mark.parametrize('ruta', ['/api/metricas/calibracion', '/api/metricas/calibracion/Q1/curva'])
def test_fallo_bd_es_503_sin_cero_exitoso_ni_texto_del_driver(cliente, monkeypatch, ruta, caplog):
    client, _ = cliente
    def fallo(*a, **kw):
        raise RuntimeError('DSN_PRIVADA_NO_PUBLICAR')
    monkeypatch.setattr(rutas, '_resolver_periodo', fallo)
    r = client.get(ruta, params={'origen': 'API_USUARIO'})
    assert r.status_code == 503
    assert 'DSN_PRIVADA_NO_PUBLICAR' not in r.text
    assert 'DSN_PRIVADA_NO_PUBLICAR' not in caplog.text
    assert 'n_predicciones' not in r.json()


def test_calibrada_sin_raw_es_medible_y_sharpness_es_varianza(cliente):
    client, filas = cliente
    filas[:] = [(None, .2, False, None, None, None, None, None),
                (None, .8, True, None, None, None, None, None)]
    m = client.get('/api/metricas/calibracion?origen=API_USUARIO&mercado=Q1&serie=calibrada').json()['metricas_por_mercado'][0]
    assert m['n_raw'] == 0 and m['n_calibradas'] == 2 and m['n_predicciones'] == 2
    assert m['brier_score'] == pytest.approx(.04)
    assert m['sharpness'] == pytest.approx(.09)  # Varianza, no desviación estándar .3.
    assert m['base_rate'] == .5


def test_igual_n_con_cohortes_distintas_no_atribuye_mejora(cliente):
    client, filas = cliente
    filas[:] = [(.1, None, True, None, None, None, None, None),
                (None, .9, True, None, None, None, None, None)]
    m = client.get('/api/metricas/calibracion?origen=API_USUARIO&mercado=Q1').json()['metricas_por_mercado'][0]
    assert m['n_raw'] == m['n_calibradas'] == 1
    assert m['mejora_vs_raw'] is None


@pytest.mark.parametrize('parametro', ['serie=mixta', 'modelo_version_id=0'])
def test_rechaza_serie_o_version_invalida(cliente, parametro):
    client, _ = cliente
    for ruta in ['/api/metricas/calibracion', '/api/metricas/calibracion/Q1/curva']:
        assert client.get(ruta+'?origen=API_USUARIO&'+parametro).status_code == 422
