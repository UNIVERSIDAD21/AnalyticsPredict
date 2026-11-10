"""Regresión de agenda: contratos verificables, sin HTTP ni BD habituales."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
from urllib.parse import urlencode

import pytest

from servicios.agenda_multiliga import pedidos, recolectar_agenda, cobertura_agenda
from servicios.fuentes_agenda import FUTBOL

HOY = date(2026, 11, 7)
NBA = {'codigo': 'nba', 'nombre': 'NBA', 'deporte': 'baloncesto'}
FA = {'codigo': 'ENG_FACUP', 'nombre': 'FA Cup', 'deporte': 'futbol'}


def evento(name='STATUS_SCHEDULED', start='2026-11-07T02:00:00Z', ident='900001', year=2027):
    final = name in {'STATUS_FINAL', 'STATUS_FULL_TIME', 'STATUS_FINAL_AET', 'STATUS_FINAL_PEN'}
    return {'id': ident, 'date': start, 'season': {'year': year, 'type': 2},
            'status': {'type': {'name': name, 'completed': final}},
            'competitions': [{'id': ident, 'date': start, 'timeValid': True, 'competitors': [
                {'homeAway': 'home', 'team': {'id': '1', 'displayName': 'A'}},
                {'homeAway': 'away', 'team': {'id': '2', 'displayName': 'B'}}]}]}


def solicitud(liga=NBA):
    return pedidos([liga], HOY, horizonte=1)[0]


class CapturasSinteticas:
    def __init__(self, folder, respuestas):
        self.folder, self.respuestas, self.calls = folder, respuestas, []
    def json(self, url, params, **kw):
        key = url + '?' + urlencode(params)
        self.calls.append(key)
        value = self.respuestas[len(self.calls)-1]
        if isinstance(value, Exception):
            raise value
        raw = json.dumps(value).encode()
        path = self.folder / (sha256(raw).hexdigest()+'.json')
        path.write_bytes(raw)
        return value, {'url': key, 'archivo': str(path), 'sha256': sha256(raw).hexdigest(),
                       'http': 200, 'observado_en': '2026-11-07T15:00:00Z'}


def payload(events, slug='nba'):
    return {'leagues': [{'slug': slug}], 'events': events}


@pytest.mark.parametrize('name,state', [('STATUS_SCHEDULED','PROGRAMADO'),
    ('STATUS_POSTPONED','POSPUESTO'),('STATUS_CANCELED','CANCELADO'),
    ('STATUS_SUSPENDED','SUSPENDIDO'),('STATUS_DELAYED','DEMORADO'),
    ('STATUS_IN_PROGRESS','EN_VIVO'),('STATUS_HALFTIME','EN_VIVO')])
def test_estados_explicitos_sin_outcomes(tmp_path, name, state):
    result = recolectar_agenda(CapturasSinteticas(tmp_path,[payload([evento(name)])]), [solicitud()])
    assert result['registros'][0]['estado'] == state
    assert result['registros'][0]['resultados'] == {}


@pytest.mark.parametrize('start,expected', [('2026-11-07T02:00:00Z',1),
    ('2026-11-06T02:00:00Z',0),('2026-11-09T04:59:00Z',1),('2026-11-09T05:00:00Z',0)])
def test_limites_se_aplican_en_cot(tmp_path,start,expected):
    result = recolectar_agenda(CapturasSinteticas(tmp_path,[payload([evento(start=start)])]),[solicitud()])
    assert len(result['registros']) == expected


@pytest.mark.parametrize('only_day', [True,False])
def test_hora_no_confirmada_no_cambia_al_dia_cot_anterior(tmp_path,only_day):
    e=evento(start='2026-11-06' if only_day else '2026-11-06T00:00:00Z')
    e['competitions'][0]['timeValid']=False
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([e])]),[solicitud()])
    assert r['registros'][0]['inicio_utc'] is None
    assert r['registros'][0]['fecha_fuente']=='2026-11-06'


def test_duplicados_iguales_no_inflan_denominador(tmp_path):
    e=evento();r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([e,e])]),[solicitud()])
    assert len(r['registros'])==r['eventos_fuente_unicos']==1


def test_tres_revisiones_no_rehabilitan_una_contradiccion(tmp_path):
    a=evento();b=evento(start='2026-11-07T03:00:00Z')
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([a,b,b])]),[solicitud()])
    assert not r['registros'] and len(r['consultas'][0]['incidencias'])==2


@pytest.mark.parametrize('fault', ['otra_liga','truncado','total','sin_id','estado_nuevo'])
def test_fallo_no_acredita_completitud(tmp_path,fault):
    p=payload([evento()])
    if fault=='otra_liga':p['leagues'][0]['slug']='wnba'
    if fault=='truncado':p['events']*=500
    if fault=='total':p['total']=2
    if fault=='sin_id':p['events'][0].pop('id')
    if fault=='estado_nuevo':p['events'][0]['status']['type']['name']='STATUS_UNKNOWN'
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[p]),[solicitud()])
    assert not r['registros']
    assert cobertura_agenda(r,[NBA])[0]['estado']=='PARCIAL'
    assert cobertura_agenda(r,[NBA])[0]['cobertura_oficial']=='DESCONOCIDA'


def test_origen_bloqueado_no_detiene_otro(tmp_path):
    from servicios.transporte_agenda import FuenteNoDisponible
    tasks=[solicitud(),solicitud(FA)]
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[FuenteNoDisponible('HTTP 403'),payload([],slug='eng.fa')]),tasks)
    assert [q['estado'] for q in r['consultas']]==['ERROR','OBSERVADA']


def test_sin_eventos_no_es_calendario_completo(tmp_path):
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([])]),[solicitud()])
    c=cobertura_agenda(r,[NBA])[0]
    assert c['estado']=='SIN_EVENTOS_PUBLICADOS' and c['ultimo_inicio_observado'] is None
    assert c['cobertura_oficial']=='DESCONOCIDA'


def test_horizonte_solicitado_no_es_publicado(tmp_path):
    task=pedidos([FA],HOY)[0]
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([evento(year=2026)],'eng.fa')]),[task])
    c=cobertura_agenda(r,[FA])[0]
    assert c['hasta_solicitado']=='2027-01-06'
    assert c['ultima_fecha_publicada']=='2026-11-06'


def test_competiciones_con_fuente_y_presupuesto():
    ligas=[{'codigo':v,'deporte':'futbol'} for v in set(FUTBOL.values())]
    ligas += [NBA,{'codigo':'wnba','deporte':'baloncesto'},{'codigo':'euroleague','deporte':'baloncesto'}]
    jobs=pedidos(ligas,HOY)
    assert len(jobs)<=200 and len({q['clave'] for q in jobs})==len(jobs)
    assert all(q['hasta']=='2027-01-06' and q['desde']=='2026-11-06' for q in jobs)
    assert len({q['liga']['codigo'] for q in jobs[:len(ligas)]})==len(ligas)
    archived={'codigo':'SIN_FUENTE_ARCHIVADA','deporte':'futbol'}
    assert not pedidos([archived],HOY)


def test_copa_colombia_se_consulta_separada_de_la_liga():
    ligas = [{'codigo': code, 'deporte': 'futbol'} for code in ('COL_PRIMERAA', 'COL_COPA')]
    jobs = pedidos(ligas, date(2026, 11, 10), horizonte=1)
    assert {(j['liga']['codigo'], j['feed']) for j in jobs} == {
        ('COL_PRIMERAA', 'col.1'), ('COL_COPA', 'col.copa')}
    assert all('/' + j['feed'] + '/scoreboard' in j['url'] for j in jobs)


def test_copa_colombia_conserva_el_partido_nocturno_del_dia_cot(tmp_path):
    liga = {'codigo': 'COL_COPA', 'deporte': 'futbol'}
    task = {**pedidos([liga], date(2026, 11, 10), horizonte=1)[0],
            'desde': '2026-11-10', 'hasta': '2026-11-10'}
    events = [evento(start=start, ident=str(i), year=2026) for i, start in enumerate([
        '2026-11-10T23:30:00Z', '2026-11-11T01:30:00Z', '2026-11-11T05:00:00Z'])]
    r = recolectar_agenda(CapturasSinteticas(tmp_path, [payload(events, 'col.copa')]), [task])
    assert not r['consultas'][0]['incidencias']
    assert len(r['registros']) == 2
    assert all(x['codigo'] == 'COL_COPA' and x['resultados'] == {} for x in r['registros'])
    assert [x['id_fuente'] for x in r['registros']] == ['0', '1']


def test_respuesta_de_liga_no_se_importa_como_copa_colombia(tmp_path):
    task = pedidos([{'codigo': 'COL_COPA', 'deporte': 'futbol'}], HOY, horizonte=1)[0]
    r = recolectar_agenda(CapturasSinteticas(tmp_path, [payload([evento(year=2026)], 'col.1')]), [task])
    assert not r['registros']
    assert r['consultas'][0]['estado'] == 'ERROR'


def test_wnba_condicional_conservado_sin_final(tmp_path):
    liga={'codigo':'wnba','deporte':'baloncesto'}
    e=evento(year=2026);e['competitions'][0]['ifNecessary']=True
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([e],'wnba')]),[solicitud(liga)])
    assert r['registros'][0]['fixture_wnba']['condicional'] is True
    assert not r['registros'][0]['resultados']


def test_cuartos_y_ot_explicitos(tmp_path):
    e=evento('STATUS_FINAL')
    for c,values in zip(e['competitions'][0]['competitors'],([20,20,25,25,10],[25,20,25,20,8])):
        c['score']=str(sum(values));c['linescores']=[{'value':x,'period':i+1} for i,x in enumerate(values)]
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([e])]),[solicitud()])
    result=r['registros'][0]['resultados']
    assert result['local_total']==100 and result['local_ot']==10 and result['hubo_overtime']
    e['competitions'][0]['competitors'][0]['linescores'][0]['value']=None
    assert not recolectar_agenda(CapturasSinteticas(tmp_path,[payload([e])]),[solicitud()])['registros']


@pytest.mark.parametrize('name', ['STATUS_FINAL_AET','STATUS_FINAL_PEN'])
def test_et_y_tanda_separadas_y_summary_obligatorio(tmp_path,name):
    e=evento(name,year=2026,ident='100')
    c=e['competitions'][0]
    pen=name.endswith('PEN')
    for participant,values,score,tanda in zip(c['competitors'],
        ([1,0,0,0,3],[0,1,0,0,4]) if pen else ([1,0,1,0],[0,1,0,0]),
        (1,1) if pen else (2,1),(3,4)):
        participant.update(score=str(score),linescores=[{'displayValue':str(v)} for v in values],
                           winner=participant['homeAway']==('away' if pen else 'home'))
        if pen:participant['shootoutScore']=tanda
    summary={'header':{'id':'100','competitions':[{**deepcopy(c),'status':e['status']}]},
             'format':{'regulation':{'periods':2,'slug':'half'}}}
    r=recolectar_agenda(CapturasSinteticas(tmp_path,[payload([e],'eng.fa'),summary]),[solicitud(FA)])
    values=r['registros'][0]['resultados']
    assert values['local_goles_total']==(1 if pen else 2)
    assert values['local_penales']==(3 if pen else None)
    assert values['local_goles_et']==(0 if pen else 1)
    class SinSummary(CapturasSinteticas):
        def json(self,*args,**kwargs):
            if 'summary' in args[0]:raise RuntimeError('Summary no disponible')
            return super().json(*args,**kwargs)
    missing=recolectar_agenda(SinSummary(tmp_path,[payload([e],'eng.fa')]),[solicitud(FA)])
    assert not missing['registros'] and missing['consultas'][0]['incidencias'][0]['id']=='100'


def test_bytes_alterados_no_acreditan_ventana(tmp_path):
    class ClienteAlterado(CapturasSinteticas):
        def json(self,*args,**kwargs):
            p,m=super().json(*args,**kwargs);m['sha256']='0'*64;return p,m
    r=recolectar_agenda(ClienteAlterado(tmp_path,[payload([evento()])]),[solicitud()])
    assert r['consultas'][0]['estado']=='ERROR' and not r['registros']
