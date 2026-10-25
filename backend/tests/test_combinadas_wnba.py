"""Conjuntas WNBA: snapshot exacto, push y aislamiento del motor genérico NBA."""
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest
from motor.wnba_ampliado import predecir_ampliado
from servicios import predictor_wnba as svc, combinadas_wnba as combinadas
from test_wnba_ampliado import modelo, ot


@pytest.fixture
def selecciones(tmp_path,monkeypatch,modelo,ot):
    monkeypatch.setenv('ANALYTICSPREDICT_MODELO_WNBA_ACTIVO',str(tmp_path/'activo.json'))
    rows=[{'id':'r','fecha':'2020-01-01','temporada_id':'s','fase':'REG'}]
    monkeypatch.setattr(svc,'cargar',lambda:{'version':'publicado','dataset_sha256':'datos','datos':rows})
    monkeypatch.setattr(svc,'ajuste_cache',lambda *a:modelo)
    monkeypatch.setattr(combinadas,'ajustar_ot',lambda rows:ot)
    fid=str(uuid4());ss=[]
    for mercado,linea in [('COMPLETO',160.5),('Q4',40)]:
        pred=predecir_ampliado(modelo,'h','a',mercado,linea,[],ot)
        r={**pred,'dominio':'wnba','contrato_prediccion':'wnba-condicional-ot-v2','modelo_version':'modelo',
           'publicacion_version':'publicado','equipo_local':'H WNBA','equipo_visitante':'A WNBA',
           'equipo_local_id':'h','equipo_visitante_id':'a','partido_id':fid,
           'fecha_partido':(datetime.now(timezone.utc)+timedelta(days=2)).isoformat(),
           'modo':'PREPARTIDO','es_prueba':True,'guardar_bitacora_habilitado':False,
           'mercado':mercado,'linea':linea,'temporadas_solicitadas':[{'id':'s','nombre':'2020'}],
           'corte_exclusivo':'2021-01-01','fases_solicitadas':['REG']}
        r=svc.registrar(r)
        ss.append({'equipo_local':'H WNBA','equipo_visitante':'A WNBA','partido_id':fid,
          'mercado':mercado,'linea':linea,'lado':'OVER','cuota':1.91,'confianza_sistema':None,
          'probabilidad_sistema':r['probabilidades']['over'],
          'razones':[{'tipo':'trazabilidad_wnba','analisis_id':r['analisis_id'],'partido_id':fid,'incluye_ot':True}]})
    return ss


def test_conjunta_propia_no_factores_nba_y_push_exactos(selecciones,modelo,ot):
    r=combinadas.evaluar(selecciones)
    p=predecir_ampliado(modelo,'h','a','COMPLETO',160.5,[],ot,devolver_muestras=True)
    a=p['_muestras']['COMPLETO']>160.5;b=p['_muestras']['Q4']>40
    expected=np.mean(np.where(a,1.91,0)*np.where(b,1.91,np.where(p['_muestras']['Q4']==40,1,0)))-1
    assert r['probabilidad_ajustada']==float(np.mean(a&b))
    assert r['valor_esperado_unidad']==pytest.approx(expected)
    assert r['tiene_mismo_partido'] and r['n_partidos_unicos']==1
    assert r['factor_correlacion'] not in (.8,.84,.93,.96)


def test_no_guarda_comprobaciones_ni_probabilidades_alteradas(selecciones):
    with pytest.raises(ValueError,match='oficial WNBA'):
        combinadas.evaluar(selecciones,guardar=True)
    selecciones[0]['probabilidad_sistema']=.99
    with pytest.raises(ValueError,match='alterada'):
        combinadas.evaluar(selecciones)


def test_rechaza_ligas_mezcladas_y_seleccion_duplicada(selecciones):
    with pytest.raises(ValueError,match='duplicada'):
        combinadas.evaluar([selecciones[0],selecciones[0]])
    selecciones[1]['razones']=[]
    with pytest.raises(ValueError,match='mezclar'):
        combinadas.evaluar(selecciones)
