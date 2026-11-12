from datetime import datetime, timedelta, timezone

from servicios.cobertura_actualizador import clasificar, resumir_obligaciones

NOW = datetime(2026,11,12,17,tzinfo=timezone.utc)


def test_un_feed_vacio_o_sin_adaptador_no_archiva_una_liga_desconocida():
    r=clasificar({'codigo':'LIGA_NUEVA','estado':'SIN_ADAPTADOR'})
    assert r['afecta_cobertura_diaria'] and r['ambito']=='REVISION_DIARIA'
    for code in ['ARG_MARADONA','USA_MLS_BACK']:
        r=clasificar({'codigo':code,'estado':'SIN_ADAPTADOR'})
        assert not r['afecta_cobertura_diaria'] and r['estado']=='SIN_ADAPTADOR'


def test_seis_campos_de_un_partido_no_se_presentan_como_seis_partidos():
    rows=[{'clave':['futbol','COL_COPA','2026','ESPN','123','ESTADISTICAS','All',str(i)],
        'tipo':'EVENTO','estado':'ESPERA_FUENTE','motivo':'ESTADISTICAS_AUSENTES',
        'partido_id':'un-partido','reintentar_en':NOW+timedelta(hours=1)} for i in range(6)]
    rows.append({**rows[0],'clave':['futbol','COL_COPA','2026','ESPN','456','IDENTIDAD_RESULTADO','All','identidad'],
                 'estado':'REVISION_IDENTIDAD','motivo':'Sin equivalencia','partido_id':None,'reintentar_en':NOW})
    r=resumir_obligaciones(rows,NOW)['COL_COPA']
    assert r['resultados']==1 and r['campos_estadisticas']==6 and r['partidos_estadisticas']==1
    assert r['campos_estadisticas_elegibles']==0
    assert r['proximo_reintento_en']==(NOW+timedelta(hours=1)).isoformat()


def test_un_resultado_y_su_agenda_no_inflan_el_numero_de_resultados():
    rows=[{'clave':['futbol','COPA','2026','ESPN','123',stage,'All','identidad'],
           'tipo':'EVENTO','estado':'REVISION_IDENTIDAD','motivo':'Sin equivalencia',
           'partido_id':None,'reintentar_en':None} for stage in ['AGENDA','IDENTIDAD_RESULTADO']]
    r=resumir_obligaciones(rows,NOW)['COPA']
    assert r['resultados']==1 and r['eventos_agenda']==1
    assert r['partidos_estadisticas']==0
