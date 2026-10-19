from copy import deepcopy
import pytest

from servicios.finales_espn_futbol import interpretar_periodos_final, validar_periodos_final, interpretar_desempate_final
from scripts.auditar_fuente_espn_soccer import FuenteNoDisponible, interpretar_evento


def caso(estado='STATUS_FINAL_PEN'):
    pen=estado=='STATUS_FINAL_PEN'
    aet=estado=='STATUS_FINAL_AET'
    esperado={'id_fuente':'100','inicio_utc':'2026-01-10T12:00Z','estado_fuente':estado,
              'local_id_fuente':'1','visitante_id_fuente':'2',
              'local_goles':1 if pen else 2,'visitante_goles':1}
    participantes=[]
    for lado,ident,lineas,tanda,ganador in [
        ('home','1',[1,0,0,0,3] if pen else [1,0,1,0] if aet else [1,1],3,not pen),
        ('away','2',[0,1,0,0,4] if pen else [0,1,0,0] if aet else [0,1],4,pen)]:
        item={'team':{'id':ident,'displayName':'Equipo '+ident},'homeAway':lado,
              'score':str(esperado['local_goles' if lado=='home' else 'visitante_goles']),
              'winner':ganador,'linescores':[{'displayValue':str(x)} for x in lineas]}
        if pen:item['shootoutScore']=float(tanda)
        participantes.append(item)
    p={'id':'100','date':esperado['inicio_utc'],'status':{'type':{'name':estado,'completed':True}},
       'competitors':participantes}
    payload={'format':{'regulation':{'periods':2,'slug':'half'}},'header':{'id':'100','competitions':[p]}}
    return payload,esperado


def test_penales_no_se_suman_a_ft_ni_se_inventan_corners():
    p,e=caso()
    r=interpretar_periodos_final(p,e)
    assert r['campos']['local_goles_1t']==1
    assert r['campos']['local_goles_2t']==0
    assert r['campos']['local_goles_et']==0
    assert r['campos']['local_penales']==3
    assert r['campos']['visitante_penales']==4
    assert r['campos']['hubo_penales'] is True and r['ganador'] is None
    assert r['ganador_tanda']=='visitante'
    assert not any('corner' in campo for campo in r['campos'])
    competencia=p['header']['competitions'][0]
    evento={'id':e['id_fuente'],'date':e['inicio_utc'],'status':competencia['status'],
            'competitions':[competencia]}
    assert interpretar_evento(evento,'eng.fa')['final_acreditado'] is True


def test_prorroga_no_se_absorbe_en_segundo_tiempo():
    p,e=caso('STATUS_FINAL_AET')
    r=interpretar_periodos_final(p,e)
    assert [r['campos']['local_goles_'+x] for x in ('1t','2t','et')]==[1,0,1]
    assert r['campos']['hubo_tiempo_extra'] is True
    assert r['campos']['local_penales'] is None


def test_tanda_contradictoria_y_summary_de_otro_evento_se_rechazan():
    p,e=caso()
    mal=deepcopy(p);mal['header']['competitions'][0]['competitors'][0]['shootoutScore']=4
    with pytest.raises(FuenteNoDisponible,match='Tanda'):
        interpretar_periodos_final(mal,e)
    mal=deepcopy(p);mal['header']['id']='otro'
    with pytest.raises(FuenteNoDisponible,match='Identidad'):
        interpretar_periodos_final(mal,e)
    r=interpretar_periodos_final(p,e);r['campos']['local_goles_2t']=3
    with pytest.raises(ValueError,match='FT'):
        validar_periodos_final(r,e)


def test_no_deduce_mitades_ausentes_desde_ft():
    p,e=caso('STATUS_FULL_TIME')
    p['header']['competitions'][0]['competitors'][0]['linescores']=[]
    with pytest.raises(FuenteNoDisponible,match='Periodos ausentes'):
        interpretar_periodos_final(p,e)


def test_penales_en_vuelta_con_marcador_desigual_y_agregado_empatado():
    p,e=caso();e['local_goles']=2
    g=p['header']['competitions'][0]
    g['competitors'][0].update(score='2',winner=True)
    g['competitors'][0]['linescores'][0]['displayValue']='2'
    g['competitors'][1]['winner']=False
    g['series']=[{'completed':True,'leg':2,'totalCompetitions':2,'competitors':[
        {'id':'1','aggregateScore':2,'winner':False},
        {'id':'2','aggregateScore':2,'winner':True}]}]
    r=interpretar_periodos_final(p,e)
    assert r['ganador']=='local' and r['ganador_tanda']=='visitante'
    assert r['agregado']=={'local':2,'visitante':2}
    del g['series']
    with pytest.raises((ValueError,FuenteNoDisponible)):
        interpretar_periodos_final(p,e)


def test_periodos_negativos_se_rechazan_sin_perder_tanda_valida():
    p,e=caso();p['header']['competitions'][0]['competitors'][0]['linescores'][2]['displayValue']='-1'
    with pytest.raises(FuenteNoDisponible,match='valor de periodos'):
        interpretar_periodos_final(p,e)
    tanda=interpretar_desempate_final(p,e)
    assert tanda['campos']['local_penales']==3 and tanda['campos']['visitante_penales']==4
