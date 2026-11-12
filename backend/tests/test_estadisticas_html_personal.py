from datetime import datetime,timezone
from hashlib import sha256
import json

import pytest

from servicios.estadisticas_html_personal import extraer_captura


def caso():
    row={'id':'p','competicion_id':'c','estado':'FINALIZADO','hubo_tiempo_extra':False,
         'fecha_partido':datetime(2026,11,6,19,30,tzinfo=timezone.utc),
         'equipo_local_id':'a','equipo_visitante_id':'b','local_goles_total':2,'visitante_goles_total':0,
         'local_disparos_total':8,'visitante_disparos_total':9}
    link={'partido_id':'p','competicion_id':'c','evento_web':'123','competicion_nombre':'FA Cup','competicion_web_id':'1840',
          'local_web_id':'10','visitante_web_id':'20','local_nombre_web':'Equipo A','visitante_nombre_web':'Equipo B',
          'local_canonico_id':'a','visitante_canonico_id':'b'}
    event={'@type':'SportsEvent','@id':'event','url':'https://scoremondo.com/es/partido/a-b-123',
           'description':'El resultado del partido 2-0','startDate':'2026-11-06T20:30:00+01:00',
           'superEvent':{'name':'FA Cup'},'homeTeam':{'name':'Equipo A','url':'https://scoremondo.com/es/equipo/a-10'},
           'awayTeam':{'name':'Equipo B','url':'https://scoremondo.com/es/equipo/b-20'}}
    blog={'@type':'LiveBlogPosting','about':{'@id':'event'},'liveBlogUpdate':[{'headline':'Final del partido · 2 - 0'}]}
    return row,link,event,blog


def extraer(row,link,event,blog,stats=None):
    section=stats if stats is not None else '<div class="st-v"><b class="num">3</b><span>Tiros a puerta</span><b class="num">5</b></div>'
    raw=(''.join('<script type="application/ld+json">'+json.dumps(x)+'</script>' for x in [event,blog])+section).encode()
    meta={'url':event['url'],'sha256':sha256(raw).hexdigest(),'http':200,'observado_en':'2026-11-12T18:00:00+00:00'}
    return extraer_captura(raw,meta,row,link)


def test_preserva_metricas_ausentes_y_no_inventa_tiros_totales():
    e,_,_,_=extraer(*caso())
    assert {x.campo:x.valor for x in e}=={'local_disparos_arco':3,'visitante_disparos_arco':5}


def test_totales_aproximados_visibles_no_se_importan_como_observados():
    section='<div class="st-v"><b class="num">~10</b><span>Tiros totales</span><b class="num">~9</b></div><div class="st-v"><b class="num">3</b><span>Tiros a puerta</span><b class="num">5</b></div>'
    e,_,_,_=extraer(*caso(),stats=section)
    assert {x.campo:x.valor for x in e}=={'local_disparos_arco':3,'visitante_disparos_arco':5}


@pytest.mark.parametrize('modificacion',['sin_cierre','otro_evento','otra_competicion','ft_distinto','sin_zona','hora_distinta','localia','prorroga'])
def test_identidad_incompatible_no_genera_evidencia(modificacion):
    row,link,event,blog=caso()
    if modificacion=='sin_cierre':blog['liveBlogUpdate']=[]
    elif modificacion=='otro_evento':blog['about']['@id']='otro'
    elif modificacion=='otra_competicion':event['superEvent']['name']='Otra Copa'
    elif modificacion=='ft_distinto':event['description']='Resultado 3-0'
    elif modificacion=='sin_zona':event['startDate']='2026-11-06T19:30:00'
    elif modificacion=='hora_distinta':event['startDate']='2026-11-07T19:30:00+00:00'
    elif modificacion=='localia':link['local_web_id']='20'
    elif modificacion=='prorroga':row['hubo_tiempo_extra']=True
    with pytest.raises(ValueError):extraer(row,link,event,blog)


def test_una_seccion_duplicada_no_se_confunde_con_ft():
    section='<div class="st-v"><b class="num">3</b><span>Tiros a puerta</span><b class="num">5</b></div>'
    with pytest.raises(ValueError):extraer(*caso(),stats=section*2)


def test_sot_incoherente_se_rechaza_y_cero_observado_de_corners_se_conserva():
    row,link,event,blog=caso()
    section='<div class="st-v"><b class="num">0</b><span>Tiros a puerta</span><b class="num">12</b></div><div class="st-v"><b class="num">0</b><span>Córneres</span><b class="num">3</b></div>'
    e,_,rejected,_=extraer(row,link,event,blog,section)
    assert set(rejected)=={'local_disparos_arco','visitante_disparos_arco'}
    assert {x.campo:x.valor for x in e}=={'local_corners_total':0,'visitante_corners_total':3}
