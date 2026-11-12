from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

import pytest
from servicios.resolucion_multifuente_futbol import EvidenciaNoValida, extraer_evidencia_espn, construir_plan_resolucion

FIXTURES = json.loads((Path(__file__).parent/'fixtures/calidad_espn_boxscore_20261106.json').read_text(encoding='utf-8'))
CASO = next(c for c in FIXTURES if c['evento']=='401928493')


def extraer(case):
    rejected=[]
    evidence=extraer_evidencia_espn(case['payload'],case['esperado'],
        observado_en=datetime.fromisoformat(case['observado_en']),rechazos_calidad=rejected)
    return construir_plan_resolucion({},evidence),rejected


@pytest.mark.parametrize('case',FIXTURES,ids=[c['evento'] for c in FIXTURES])
def test_regresion_capturas_reales_y_cero_coherente(case):
    plan,rejected=extraer(case)
    if case['rechazado']:
        assert not plan.actualizaciones
        assert len(rejected)==6 and all('BLOQUE_CEROS_SIN_COBERTURA' in r['motivo'] for r in rejected)
    else:
        assert len(plan.actualizaciones)==6 and 0 in plan.actualizaciones.values()
        assert not rejected


def control_posesion(case):
    for t,p in zip(case['payload']['boxscore']['teams'],('52','48')):
        next(x for x in t['statistics'] if x['name']=='possessionPct')['displayValue']=p


def test_un_autogol_no_exige_disparos_y_se_preservan_ceros_coherentes():
    case=deepcopy(CASO);control_posesion(case)
    for d in case['payload']['header']['competitions'][0]['details']:d['ownGoal']=True
    plan,rejected=extraer(case)
    assert len(plan.actualizaciones)==6 and all(v==0 for v in plan.actualizaciones.values()) and not rejected


@pytest.mark.parametrize('period,shootout',[(3,False),(4,False),(5,True)])
def test_prorroga_y_tanda_no_se_comparan_con_tiros_reglamentarios(period,shootout):
    case=deepcopy(CASO);control_posesion(case)
    for d in case['payload']['keyEvents']:
        d.update(period={'number':period},shootout=shootout)
    plan,rejected=extraer(case)
    assert len(plan.actualizaciones)==6 and not rejected


def test_gol_reglamentario_invalida_tiros_pero_no_un_corner_cero_aislado():
    case=deepcopy(CASO);control_posesion(case)
    local=case['payload']['boxscore']['teams'][0]
    next(x for x in local['statistics'] if x['name']=='totalShots')['displayValue']='4'
    plan,rejected=extraer(case)
    assert plan.actualizaciones['local_disparos_total']==4
    assert plan.actualizaciones['visitante_corners_total']==0
    assert {x['campo'] for x in rejected}=={'visitante_disparos_total','visitante_disparos_arco'}


def test_boxscore_parcial_coherente_conserva_dato_observado_y_no_imputa():
    case=deepcopy(CASO)
    case['payload']['boxscore']['teams'][0]['statistics']=[{'name':'wonCorners','displayValue':'0'}]
    case['payload']['boxscore']['teams'][1]['statistics']=None
    plan,rejected=extraer(case)
    assert plan.actualizaciones=={'local_corners_total':0} and not rejected


def test_boxscore_ausente_no_es_estadistica_completa():
    case=deepcopy(CASO);case['payload'].pop('boxscore')
    with pytest.raises(EvidenciaNoValida,match='Boxscore'):extraer(case)


def test_marca_full_no_acredita_bloque_totalmente_cero_sin_contexto():
    case=deepcopy(CASO)
    for t in case['payload']['boxscore']['teams']:
        t['statistics']=[s for s in t['statistics'] if s['name'] in ('wonCorners','totalShots','shotsOnTarget')]
    case['payload']['header']['competitions'][0]['details']=[]
    plan,rejected=extraer(case)
    assert not plan.actualizaciones and len(rejected)==6
