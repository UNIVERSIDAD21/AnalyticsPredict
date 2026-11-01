"""La matriz detecta fallos, abstenciones y ausencia de casos sin tocar publicaciones."""
from copy import deepcopy

import numpy as np
import pytest

from calidad import auditoria_wnba as auditoria


@pytest.fixture
def datos(monkeypatch):
    modelo = {'entidades': {'h': 0, 'a': 1}, 'coeficientes': [[20.]*4]+[[0.]*4]*5,
              'muestras': {'h': 100, 'a': 100}, 'efectivos': {'h': 90, 'a': 90},
              'covarianza': (np.eye(8)*9+np.ones((8,8))*.5).tolist()}
    monkeypatch.setattr(auditoria, 'ajustar_alcance', lambda rows: deepcopy(modelo))
    return [{'id': '1', 'fecha': '2020-07-01', 'inicio_utc': '2020-07-01T20:00:00Z',
             'temporada': '2020', 'fase': 'REG', 'local_id': 'h', 'visitante_id': 'a',
             'local': 'H', 'visitante': 'A', 'y': [20]*8, 'local_ot': 0, 'visitante_ot': 0}]


def test_todos_los_sentidos_y_cortes_sin_bloquear_cuartos_por_ot(datos):
    antes = deepcopy(datos)
    r = auditoria.auditar(datos, corte='2020-08-01', potencia=6)
    assert r['estado'] == 'VERIFICADO' and not r['fallos']
    assert r['casos_con_soporte'] == 8  # Dos localías, cuatro modos cada una.
    assert r['alcances'][0]['total_pre_con_ot_disponible'] is False
    assert r['serving_exacto'] is False and datos == antes


def test_equipo_de_otra_temporada_debe_abstenerse(datos):
    otros = {**datos[0], 'id': '2', 'local_id': 'z', 'local': 'Z', 'temporada': '2021'}
    r = auditoria.auditar([*datos, otros], corte='2022-01-01', potencia=5)
    assert r['estado'] == 'VERIFICADO'
    assert all(a['parejas_abstencion'] == 4 for a in r['alcances'])


def test_reporta_probabilidad_rota_sin_ocultarla(datos, monkeypatch):
    original = auditoria.predecir_ampliado
    def rota(*args, **kwargs):
        r = original(*args, **kwargs)
        r['probabilidades']['over'] = float('nan')
        return r
    monkeypatch.setattr(auditoria, 'predecir_ampliado', rota)
    r = auditoria.auditar(datos, corte='2020-08-01', potencia=5)
    assert r['estado'] == 'CON_FALLOS' and len(r['fallos']) == 8
    assert r['casos_con_soporte'] == 0


def test_sin_soporte_no_se_anuncia_verificado(datos, monkeypatch):
    def insuficiente(rows):
        raise ValueError('Muestra insuficiente')
    monkeypatch.setattr(auditoria, 'ajustar_alcance', insuficiente)
    r = auditoria.auditar(datos, corte='2020-08-01', potencia=5)
    assert r['estado'] == 'SIN_CASOS_VERIFICABLES'


def test_ids_duplicados_y_corte_vacio_rechazados(datos):
    with pytest.raises(ValueError, match='duplicados'):
        auditoria.auditar(datos*2, corte='2021-01-01')
    with pytest.raises(ValueError, match='Sin datos'):
        auditoria.auditar(datos, corte='2020-01-01')
