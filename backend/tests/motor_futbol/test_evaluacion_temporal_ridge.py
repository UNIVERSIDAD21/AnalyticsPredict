"""Regresiones de partición, selección en CAL, conteos y límites explícitos."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import numpy as np
import pytest

from motor_futbol.entrenamiento.validacion import TimeSeriesSplitFutbol, ValidacionCruzadaTemporal
from motor_futbol.evaluacion.temporal_ridge import PoliticaTemporal, Ventana, evaluar, matrices, metricas
from motor_futbol.tipos import TipoModelo


@pytest.fixture
def datos():
    partidos = []
    for base, cantidad in [(datetime(2025,1,1,tzinfo=timezone.utc), 24),
                           (datetime(2025,2,1,tzinfo=timezone.utc), 8),
                           (datetime(2025,3,1,tzinfo=timezone.utc), 8)]:
        for i in range(cantidad):
            a, b = (2,6) if i % 2 else (6,2)
            partidos.append(dict(id=uuid4(), fecha_partido=base+timedelta(days=i),
                equipo_local='Club A' if i % 2 else 'Club B', equipo_visitante='Club B' if i % 2 else 'Club A',
                competicion_id='liga', competicion_codigo='ENG_PREMIER', temporada_id='temporada',
                local_corners_1t=a, local_corners_2t=a+1, visitante_corners_1t=b, visitante_corners_2t=b+1,
                local_corners_total=2*a+1, visitante_corners_total=2*b+1,
                local_goles_1t=a//2, local_goles_2t=0, visitante_goles_1t=b//2, visitante_goles_2t=0,
                local_goles_total=a//2, visitante_goles_total=b//2,
                local_disparos_total=a*3, local_disparos_arco=a, visitante_disparos_total=b*3, visitante_disparos_arco=b))
    return partidos


@pytest.fixture
def politica():
    return PoliticaTemporal(desde=date(2025,1,1),
        ventanas=(Ventana('test',date(2025,2,1),date(2025,3,1),date(2025,4,1)),),
        min_train=10,min_cal=4,min_eval=4,min_partidos_equipo=2,bootstrap_repeticiones=100,
        min_eval_activacion=4,min_ventanas_activacion=1)


def test_split_ordena_y_no_divide_perspectivas_ni_repite_eval():
    fechas = np.repeat([datetime(2025,1,1)+timedelta(days=i) for i in range(20)],2)
    fechas = fechas[np.random.default_rng(42).permutation(len(fechas))]
    splits = list(TimeSeriesSplitFutbol(4).split(fechas))
    assert len(splits) == 4
    vistos = set()
    for train,test in splits:
        assert max(fechas[train]) < min(fechas[test])
        assert not set(fechas[train]) & set(fechas[test])
        assert not vistos & set(test)
        vistos.update(test)
    assert ValidacionCruzadaTemporal(min_train_size=100).split(np.ones((40,2)),fechas) == []


def test_eventos_una_fila_eval_y_dos_perspectivas_solo_train(datos, politica):
    informe=evaluar(datos,politica)
    f=informe['familias']['corners']; v=f['ventanas'][0]
    assert v['train']['n_partidos']==24 and v['train']['n_filas_diseno']==48
    assert v['cal']['n_partidos']==8 and v['eval']['n_partidos']==8
    assert f['resumen']['n_partidos']==8 and len(v['filas_eval'])==8
    assert v['train']['fecha_max'] < v['cal']['fecha_min'] < v['eval']['fecha_min']
    mapa={'club a':0,'club b':1}
    X,y=matrices(datos[:2],TipoModelo.CORNERS,mapa,doble=True)
    assert X.shape==(4,6) and np.array_equal(y[2:],y[:2][:,[2,3,0,1]])
    assert informe['certificacion']=='NO_CERTIFICADO'
    assert informe['disponibilidad_historica_acreditada'] is False
    assert informe['calibrador_probabilidades'] is None


def test_modificar_outcome_eval_no_cambia_alpha_coeficientes_ni_train(datos, politica):
    primero=evaluar(datos,politica)['familias']['disparos']['ventanas'][0]
    otros=deepcopy(datos)
    for p in otros[-8:]: p['local_disparos_total']+=100
    segundo=evaluar(otros,politica)['familias']['disparos']['ventanas'][0]
    for clave in ('alpha','coeficientes_sha256','seleccion_alpha','train','cal'):
        assert primero[clave]==segundo[clave]
    assert primero['metricas']['mae'] != segundo['metricas']['mae']


def test_equipo_eval_desconocido_se_cuenta_y_no_entra_al_mapa(datos, politica):
    datos[-1]['equipo_local']='Ascendido nuevo'
    f=evaluar(datos,politica)['familias']['corners']; v=f['ventanas'][0]
    assert v['eval_equipo_desconocido']==1 and v['n_eval_candidatos']==8
    assert v['eval']['n_partidos']==7 and v['cobertura_eval']==7/8
    assert 'ascendido nuevo' not in v['train']['equipos']
    assert 'COBERTURA_INSUFICIENTE' in f['gate_activacion_exploratoria']['motivos']
    with pytest.raises(ValueError,match='fuera del train'):
        matrices(datos[-1:],TipoModelo.CORNERS,{'club a':0,'club b':1})


def test_cal_escaso_no_se_sustituye_por_train_y_metrica_queda_nd(datos, politica):
    p=replace(politica,min_cal=9)
    f=evaluar(datos,p)['familias']['goles']; v=f['ventanas'][0]
    assert v['motivo']=='MUESTRA_CAL_INSUFICIENTE' and v['alpha'] is None
    assert f['resumen']['mae'] is None and f['resumen']['n_partidos']==0
    assert f['gate_activacion_exploratoria']['apto'] is False


@pytest.mark.parametrize('caso',['sin_zona','solapamiento','orden','alpha','minimo'])
def test_rechaza_politicas_o_fechas_invalidas(datos,politica,caso):
    if caso=='sin_zona': datos[0]['fecha_partido']=datetime(2025,1,1)
    if caso=='solapamiento': politica=replace(politica,ventanas=politica.ventanas*2)
    if caso=='orden': politica=replace(politica,desde=date(2025,3,1))
    if caso=='alpha': politica=replace(politica,alphas=(float('nan'),))
    if caso=='minimo': politica=replace(politica,min_train=0)
    with pytest.raises(ValueError): evaluar(datos,politica)


def test_bootstrap_pareado_no_infla_n_y_signo_negativo_es_mejora():
    filas=[{'real':[1,2,3,4],'prediccion':[1,2,3,4],'baseline':[2,3,4,5]}]*8
    m=metricas(filas,100,42)
    assert m['n_partidos']==8 and m['mae']==0 and m['mae_baseline']==1
    assert m['delta_mae']==-1 and m['ic95_delta_mae']==[-1,-1]
    assert metricas([])['mae'] is None


def test_ids_duplicados_no_aparecen_dos_veces_en_holdout(datos,politica):
    datos.append(deepcopy(datos[-1]))
    f=evaluar(datos,politica)['familias']['corners']
    assert f['dataset']['excluidos']['id_duplicado']==2
    assert f['resumen']['n_partidos']==7
