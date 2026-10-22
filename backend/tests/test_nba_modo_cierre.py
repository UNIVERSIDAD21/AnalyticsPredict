"""Cortes NBA aislados: secuencia, puntos observados, varianza y dominio de registro."""
from types import SimpleNamespace
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from api.modelos_peticion import PeticionAnalisisEnVivo
from api import rutas_analisis as rutas
from motor import nba_predictor_cuartos as motor
from motor.tipos import ModeloRidge, Ubicacion
from motor.calculadora_probabilidad import calcular_probabilidad_victoria

@pytest.fixture
def modelo(monkeypatch):
    w = np.zeros((6,4)); w[0] = [25,26,27,28]
    v = np.zeros((6,4)); v[0] = [24,25,26,27]
    monkeypatch.setattr(motor, 'obtener_calibrador_activo', lambda **k: None)
    return ModeloRidge(5, {'local':0,'visitante':1}, w,v,np.array([6.]*4),np.array([5.]*4))

def calcular(modelo, **kw):
    return motor.analizar_partido(modelo,'Local','Visitante',Ubicacion.LOCAL,mercado='COMPLETO',linea=210.5,incluir_contexto=False,**kw)

@pytest.mark.parametrize('extra', [
    {}, {'marcador_q2':'22-21'}, {'marcador_q1':'20-21','marcador_q3':'20-22'},
    {'marcador_q1':'1.5-20'}, {'marcador_q1':'101-20'}, {'marcador_q1':'-1-20'},
    {'marcador_q1':'texto'}, {'marcador_q1':'20-21','mercado':'Q1'},
    {'marcador_q1':'20-21','marcador_q4':'10-8'}, {'marcador_q1':'20-21','reloj':'03:00'}, {'marcador_q1':'20-21','temporadas':['2026']}, {'marcador_q1':'20-21','cuota_over':1.9},
])
def test_rechaza_entradas_ambiguas_o_prepartido(extra):
    body={'equipo_local':'Local','equipo_visitante':'Visitante','mercado':'COMPLETO','linea':210.5,**extra}
    with pytest.raises(ValidationError):
        PeticionAnalisisEnVivo(**body)

@pytest.mark.parametrize('n',[1,2,3])
def test_corte_fija_observados_y_solo_propaga_varianza_pendiente(modelo, monkeypatch,n):
    base = calcular(modelo)
    def prohibido(**kw): pytest.fail('Un corte no reutiliza calibración prepartido')
    monkeypatch.setattr(motor,'obtener_calibrador_activo',prohibido)
    valores=[(20,22),(23,24),(24,25)]
    r=calcular(modelo,**{f'marcador_q{i+1}':f'{a}-{b}' for i,(a,b) in enumerate(valores[:n])})
    assert r.es_en_vivo and r.metadata['modo_analisis']==f'CIERRE_Q{n}'
    for i,(a,b) in enumerate(valores[:n]):
        p=r.predicciones[f'Q{i+1}']
        assert (p.media_equipo,p.media_rival,p.desviacion_total)==(a,b,0)
    total=r.prediccion_juego_completo
    assert total.media_total==pytest.approx(sum(p.media_total for p in r.predicciones.values()))
    assert total.desviacion_total==pytest.approx(np.sqrt((4-n)*(36+25)))
    assert total.desviacion_total < base.prediccion_juego_completo.desviacion_total
    assert total.probabilidad_ganador==pytest.approx(calcular_probabilidad_victoria(total.media_equipo,total.desviacion_equipo,total.media_rival,total.desviacion_rival))
    assert not r.candidatos and r.mejor_apuesta is None and r.sizing is None
    assert r.prediccion_ajustada is None and 'metodo_live' in r.metadata
    assert np.array_equal(modelo.desviacion_equipo,[6]*4)  # no mutar el artefacto compartido


def test_contexto_descriptivo_no_aplica_ajustes_prepartido(modelo,monkeypatch):
    monkeypatch.setattr(motor,'recolectar_contexto',lambda **k: SimpleNamespace())
    monkeypatch.setattr(motor,'aplicar_ajustes_contextuales',lambda **k: pytest.fail('No reajustar un corte observado con reglas PRE'))
    r=motor.analizar_partido(modelo,'Local','Visitante',Ubicacion.LOCAL,mercado='COMPLETO',linea=210.5,marcador_q1='20-22')
    assert r.contexto is not None and r.prediccion_ajustada is None


def test_api_valida_antes_de_ejecutar_y_despacha_un_solo_corte(monkeypatch):
    llamadas=[]
    monkeypatch.setattr(rutas,'ejecutar_analisis',lambda p,**kw: (llamadas.append(kw) or {'exito':True,'datos':{},'advertencias':[]}))
    app=FastAPI();app.include_router(rutas.router)
    c=TestClient(app)
    body={'equipo_local':'Local','equipo_visitante':'Visitante','mercado':'COMPLETO','linea':210.5}
    assert c.post('/api/analizar-en-vivo',json={**body,'marcador_q2':'20-22'}).status_code==422
    assert not llamadas
    assert c.post('/api/analizar-en-vivo',json={**body,'marcador_q1':'20-22'}).status_code==200
    assert llamadas==[{'marcador_q1':'20-22','marcador_q2':None,'marcador_q3':None,'peso_en_vivo':0.5}]


def test_ejecucion_live_no_entrena_ni_registra_prediccion_pre(modelo,monkeypatch):
    r=calcular(modelo,marcador_q1='20-22')
    monkeypatch.setattr(rutas,'_validar_peticion_analisis',lambda p:[])
    monkeypatch.setattr(rutas,'obtener_modelo',lambda:SimpleNamespace(version=71))
    monkeypatch.setattr(rutas,'validar_equipos',lambda *a:None)
    monkeypatch.setattr(rutas,'_obtener_config_usuario',lambda:{})
    monkeypatch.setattr(rutas,'analizar_partido',lambda **kw:r)
    monkeypatch.setattr(rutas,'_obtener_mercados_bloqueados_nba',lambda **kw:[])
    monkeypatch.setattr(rutas,'_modo_estricto_nba_activo',lambda:False)
    monkeypatch.setattr(rutas,'_extraer_contexto_registro',lambda p:pytest.fail('No clasificar un corte como prepartido'))
    monkeypatch.setattr(rutas,'registrar_prediccion',lambda **kw:pytest.fail('No contaminar cohorte PRE'))
    calls=[];monkeypatch.setattr(rutas,'_registrar_bitacora_analisis_nba',lambda *args:calls.append(args))
    p=PeticionAnalisisEnVivo(equipo_local='Local',equipo_visitante='Visitante',mercado='COMPLETO',linea=210.5,marcador_q1='20-22')
    salida=rutas.ejecutar_analisis(p,marcador_q1=p.marcador_q1)
    assert salida.datos['metadata']['modo_analisis']=='CIERRE_Q1'
    assert salida.datos['metadata']['modelo_version']==71 and len(calls)==1


@pytest.mark.parametrize('fixture',[None,'00000000-0000-0000-0000-000000000071'])
def test_corte_no_se_guarda_como_apuesta_ni_se_enlaza_a_un_futuro(modelo,monkeypatch,fixture):
    r=calcular(modelo,marcador_q1='20-22')
    monkeypatch.setattr(rutas,'_partido_id_bitacora_nba',lambda *a:pytest.fail('No adivinar fixture'))
    monkeypatch.setattr(rutas,'registrar_apuesta_analizada',lambda **kw:pytest.fail('No contaminar registros financieros/PRE'))
    p=PeticionAnalisisEnVivo(partido_id=fixture,equipo_local='Local',equipo_visitante='Visitante',mercado='COMPLETO',linea=210.5,marcador_q1='20-22')
    rutas._registrar_bitacora_analisis_nba(p,r,None)
