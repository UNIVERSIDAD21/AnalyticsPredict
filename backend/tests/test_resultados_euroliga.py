from copy import deepcopy
import pytest
from servicios.resultados_euroliga import interpretar_boxscore, insertar_finales


def caso():
    juego={'season':2025,'gamecode':'E2025_200','gamenumber':'200','played':'true',
           'fecha':'2026-01-08','round':'RS','homecode':'MAD','awaycode':'BAR',
           'homescore':'106','awayscore':'103'}
    box={'Live':False,'ByQuarter':[
        {'Team':'Local','Quarter1':20,'Quarter2':25,'Quarter3':20,'Quarter4':25,'Extra1':8,'Extra2':8},
        {'Team':'Visitante','Quarter1':25,'Quarter2':20,'Quarter3':25,'Quarter4':20,'Extra1':8,'Extra2':5}],
        'Stats':[{'Team':'Local','PlayersStats':[{'Team':'MAD'}]},
                 {'Team':'Visitante','PlayersStats':[{'Team':'BAR'}]}]}
    return juego,box


def test_doble_prorroga_explicita_y_dominio_separado():
    g,b=caso();r=interpretar_boxscore(g,b,{'MAD':'local','BAR':'visita'},{2025:'temporada'},'euro')
    assert r['local_ot']==16 and r['visitante_ot']==13
    assert r['local_q4']==25 and r['local_total']==106
    assert r['source']=='EUROLEAGUE_OFFICIAL' and r['competicion_id']=='euro'
    assert r['hubo_overtime'] is True
    assert r['url_referencia']=='https://live.euroleague.net/api/Boxscore?gamecode=200&seasoncode=E2025'


def test_no_imputa_ot_ni_acepta_otro_equipo_o_fase():
    g,b=caso()
    mal=deepcopy(b);del mal['ByQuarter'][0]['Extra2']
    with pytest.raises(ValueError,match='no concilian'):
        interpretar_boxscore(g,mal,{'MAD':'l','BAR':'v'},{2025:'t'},'e')
    mal=deepcopy(b);mal['Stats'][0]['PlayersStats'][0]['Team']='OTRO'
    with pytest.raises(ValueError,match='otros equipos'):
        interpretar_boxscore(g,mal,{'MAD':'l','BAR':'v'},{2025:'t'},'e')
    g['round']='DESCONOCIDA'
    with pytest.raises(ValueError,match='Fase'):
        interpretar_boxscore(g,b,{'MAD':'l','BAR':'v'},{2025:'t'},'e')


@pytest.mark.parametrize('campo', ['competicion_id','temporada_id','equipo_local_id','equipo_visitante_id','tipo_partido'])
def test_mismo_id_y_marcador_no_autoriza_cambiar_identidad_o_fase(campo):
    g,b=caso();r=interpretar_boxscore(g,b,{'MAD':'l','BAR':'v'},{2025:'t'},'e')
    previo={**r,campo:'OTRA_IDENTIDAD'}

    class Conexion:
        def transaction(self):
            return self

        def cursor(self, **_kwargs):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, consulta, *_args):
            assert consulta.lstrip().startswith('SELECT'), 'No sobrescribir histórico contradictorio'
            return self

        def fetchall(self):
            return [previo]

    with pytest.raises(ValueError,match='contradictorio'):
        insertar_finales(Conexion(),[r])
