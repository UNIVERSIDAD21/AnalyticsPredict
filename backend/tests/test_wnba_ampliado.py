"""Invariantes de condicionamiento, OT y mercados; solo datos WNBA sintéticos."""
from copy import deepcopy
import numpy as np
import pytest
from motor.wnba_ampliado import condicionar, predecir_ampliado, ajustar_ot
from motor.wnba import huella


@pytest.fixture
def modelo():
    # Intercepto de 20 por lado/cuarto; dispersión de regulación WNBA sintética.
    return {'entidades':{'h':0,'a':1},'coeficientes':[[20.]*4]+[[0.]*4]*5,
            'muestras':{'h':100,'a':100},'efectivos':{'h':90,'a':90},
            'covarianza':(np.eye(8)*9+np.ones((8,8))*.5).tolist()}


@pytest.fixture
def ot():
    return {'n':20,'incrementos':[[7,9],[10,8]]*10,'partidos_sha256':'sintetico','metodo':'bootstrap WNBA'}


@pytest.mark.parametrize('n',[0,1,2,3])
def test_observados_fijos_y_varianza_solo_pendiente(modelo,ot,n):
    parciales=[[19,21]]*n
    r=predecir_ampliado(modelo,'h','a','COMPLETO',160,parciales,ot)
    for i in range(n):
        p=r['predicciones'][f'Q{i+1}']
        assert (p['media_local'],p['media_visitante'],p['desviacion_total'])==(19,21,0)
        assert p['observado']
    assert sum(r['probabilidades'].values())==pytest.approx(1)
    assert r['regulacion']['varianza_total']<105
    assert r['incluye_ot'] is (n==0)
    assert sum(r['ganador_mercado'].values())==pytest.approx(1)
    if n==0:
        assert r['predicciones']['COMPLETO']['media_total']>r['regulacion']['media_total']
        assert r['predicciones']['COMPLETO']['ganador']['empate']==0
    else:
        assert r['predicciones']['COMPLETO']==r['regulacion']


def test_schur_analitico_y_reduccion_de_incertidumbre():
    mu=np.ones(8)*20;cov=np.eye(8)*10+np.ones((8,8))*2
    a,c,p=condicionar(mu,cov,[[25,15]])
    assert a[0]==25 and a[4]==15
    assert np.allclose(a[p],20)
    assert c.trace()<cov.trace()
    assert np.linalg.eigvalsh(c).min()>=-1e-9


@pytest.mark.parametrize('parciales',[[[True,20]],[[20.1,20]],[[-1,20]],[[20]],[[20,20]]*4])
def test_parciales_incoherentes_rechazados(modelo,ot,parciales):
    with pytest.raises(ValueError):predecir_ampliado(modelo,'h','a','COMPLETO',160,parciales,ot)


@pytest.mark.parametrize('n',[1,2,3])
def test_mercado_resuelto_no_acepta_ot_y_no_usa_ft(modelo,ot,n):
    with pytest.raises(ValueError,match='resuelto'):
        predecir_ampliado(modelo,'h','a',f'Q{n}',40,[[20,21]]*n,ot)


def test_sin_ot_suficiente_abstiene_no_fallback(modelo,ot):
    with pytest.raises(ValueError,match='Abstención OT'):
        predecir_ampliado(modelo,'h','a','COMPLETO',160,[],{**ot,'n':0})
    # Cortes no anuncian OT: no requieren su muestra.
    assert predecir_ampliado(modelo,'h','a','COMPLETO',160,[[20,20]],{**ot,'n':0})


def test_ot_bootstrap_solo_regulacion_empatada():
    r={'id':'x','fecha':'2020-01-01','y':[20]*8,'local_ot':7,'visitante_ot':9}
    assert ajustar_ot([r])['n']==1
    assert ajustar_ot([{**r,'y':[21]+[20]*7}])['n']==0
    assert ajustar_ot([{**r,'local_ot':0,'visitante_ot':0}])['n']==0


def test_determinismo_inmutabilidad_media_linea_y_ganador_del_periodo(modelo,ot):
    original=huella(modelo)
    a=predecir_ampliado(modelo,'h','a','Q4',40.5,[[20,22]],ot)
    b=predecir_ampliado(modelo,'h','a','Q4',40.5,[[20,22]],ot)
    assert a==b and huella(modelo)==original
    assert a['probabilidades']['push']==0
    assert a['ganador_mercado']==a['predicciones']['Q4']['ganador']
    c=predecir_ampliado(modelo,'h','a','Q4',40,[[20,22]],ot)
    assert c['probabilidades']['push']>0
