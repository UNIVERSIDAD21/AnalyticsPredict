from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from calidad.elegibilidad_futbol import clasificar, seleccionar, muestra, evaluar_mercado, configurar_mercado
from api import rutas_analisis_futbol as rutas


def fila(**cambios):
    p = {'id':str(uuid4()), 'estado':'FINALIZADO', 'valido':True, 'hubo_tiempo_extra':False,
         'equipo_local_id':'l', 'equipo_visitante_id':'v', 'fecha_partido':datetime(2026,10,1,tzinfo=timezone.utc)}
    for lado in ('local','visitante'):
        p.update({f'{lado}_goles_total':1, f'{lado}_goles_1t':0, f'{lado}_goles_2t':1,
                  f'{lado}_goles_et':0, f'{lado}_corners_total':6, f'{lado}_corners_1t':2,
                  f'{lado}_corners_2t':4, f'{lado}_disparos_total':12, f'{lado}_disparos_arco':4})
    return {**p, **cambios}


@pytest.mark.parametrize('valor,estado', [(None,'AUSENTE'),(0,'OBSERVADO'),(-1,'INVALIDO'),(True,'INVALIDO'),(float('nan'),'INVALIDO'),(float('inf'),'INVALIDO'),(1.2,'INVALIDO')])
def test_null_cero_signo_y_finitud(valor, estado):
    assert clasificar(fila(local_corners_total=valor), 'corners_ft','local').estado == estado


def test_individual_no_exige_campo_del_otro_lado_ni_mitades_ft():
    p = fila(visitante_corners_total=None,local_corners_1t=None,local_corners_2t=None)
    assert seleccionar(p,'corners_ft','local').valor == 6
    assert seleccionar(p,'corners_ft').estado == 'AUSENTE'
    assert seleccionar(p,'corners_1t').estado == 'AUSENTE'


def test_negativo_real_no_se_oculta_por_suma_ni_invalida_otras_familias():
    p = fila(visitante_goles_total=0,visitante_goles_1t=1,visitante_goles_2t=-1)
    assert seleccionar(p,'goles_2t').estado == 'INVALIDO'
    assert clasificar(p,'goles_1t','visitante').motivo == 'PERIODOS_NO_CONCILIAN'
    assert seleccionar(p,'goles_ft').valor == 1
    assert seleccionar(p,'corners_ft').valor == 12


def test_regulacion_no_confunde_prorroga_ni_reparte_estadisticas():
    p = fila(hubo_tiempo_extra=True,local_goles_total=3,local_goles_et=2)
    assert clasificar(p,'goles_ft','local').valor == 1
    assert seleccionar(p,'corners_ft').motivo == 'FT_CON_ET_SIN_DESGLOSE_ESTADISTICO'
    assert seleccionar(p,'disparos_arco_ft').estado == 'AUSENTE'
    assert seleccionar(p,'corners_1t').estado == 'OBSERVADO'
    assert seleccionar({**p,'local_goles_et':None},'goles_ft').estado == 'AUSENTE'


def test_datos_completos_no_sustituye_campos_y_conflicto_identidad_es_explicito():
    assert seleccionar(fila(datos_completos=True,local_disparos_arco=None),'disparos_arco_ft').estado == 'AUSENTE'
    assert seleccionar(fila(identidad_conflictiva=True),'goles_ft').motivo == 'IDENTIDAD_CONFLICTIVA'
    assert seleccionar(fila(valido=False),'goles_ft').estado == 'INVALIDO'
    assert seleccionar(fila(local_disparos_arco=20),'disparos_arco_ft').motivo == 'ARCO_MAYOR_DISPAROS'


def test_muestras_reales_y_estimadas_son_distintas_y_no_mutan_entradas():
    rows=[fila(),fila(local_disparos_arco=None),fila(local_disparos_arco=-1)]
    antes=deepcopy(rows)
    r=muestra(rows,'disparos_arco_1t')
    assert (r['denominador'],r['observados'],r['estimados'],r['ausentes'],r['invalidos']) == (3,0,1,1,1)
    assert rows==antes
    assert configurar_mercado('DISPAROS_LOCAL_ARCO_1T')['metric_key']=='disparos_arco_1t'


def test_muestra_pequena_es_aviso_y_falta_de_un_equipo_no_bloquea_otro():
    conjuntos={k:[fila()] for k in ('h2h','local_global','local_home','visitante_global','visitante_away','liga')}
    r=evaluar_mercado('CORNERS_FT',conjuntos,'l','v')
    assert r['calculable'] and r['estado']=='MUESTRA_LIMITADA'
    conjuntos['visitante_global']=[fila(visitante_corners_total=None)]
    assert not evaluar_mercado('CORNERS_FT',conjuntos,'l','v')['calculable']
    assert evaluar_mercado('CORNERS_LOCAL_FT',conjuntos,'l','v')['calculable']
    r=evaluar_mercado('DISPAROS_LOCAL_ARCO_1T',conjuntos,'l','v')
    assert r['estado']=='ESTIMADO' and r['muestras']['local_global']['observados']==0


def test_dto_historico_conserva_cero_y_elimina_negativo_sin_imputar_ft():
    from servicios.calidad_futbol import normalizar_estadistico
    p=fila(equipo_local='L',equipo_visitante='V',visitante_goles_total=0,
           visitante_goles_1t=1,visitante_goles_2t=-1,local_corners_1t=None)
    r=normalizar_estadistico(p)
    assert r['goles_visitante']==0
    assert r['goles_visitante_1t'] is None and r['goles_visitante_2t'] is None
    assert r['corners_local_1t'] is None and r['corners_local']==6


@pytest.fixture
def api_sintetica(monkeypatch):
    partido={'id':str(uuid4()),'competicion_id':str(uuid4()),'temporada_id':str(uuid4()),
             'equipo_local_id':str(uuid4()),'equipo_visitante_id':str(uuid4()),
             'competicion':'Competición sintética','competicion_codigo':'TEST',
             'equipo_local':'Local sintético','equipo_visitante':'Visitante sintético',
             'fecha_partido':datetime(2026,10,30,tzinfo=timezone.utc),'estado':'PROGRAMADO','jornada':1}
    datos=[fila(equipo_local_id=partido['equipo_local_id'],equipo_visitante_id=partido['equipo_visitante_id']) for _ in range(30)]
    class Cursor:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def execute(self,q,params=None): self.partido='JOIN equipos_futbol el' in q;return self
        def fetchone(self): return partido if self.partido else {'count':0}
    class Conn:
        def cursor(self,**kw): return Cursor()
        @contextmanager
        def transaction(self): yield
    class Pool:
        @contextmanager
        def connection(self): yield Conn()
    monkeypatch.setattr('servicios.horarios_agenda.horario_partido',lambda *a,**kw:None)
    monkeypatch.setattr(rutas,'obtener_pool',Pool)
    monkeypatch.setattr(rutas,'_obtener_predictor_futbol_ml',lambda pool:None)
    monkeypatch.setattr(rutas,'_resolver_filtro_temporal_futbol',lambda *a,**kw:{'temporada_ids':[partido['temporada_id']],'estrategia':'temporadas_explicitas'})
    for nombre in ('_obtener_partidos_h2h','_obtener_partidos_equipo','_obtener_partidos_liga'):
        monkeypatch.setattr(rutas,nombre,lambda *a,**kw:datos)
    monkeypatch.setattr(rutas,'_obtener_estado_mercados_futbol',lambda *a,**kw:{'GOLES_FT':'verde','CORNERS_FT':'verde','CORNERS_1T':'verde','DISPAROS_LOCAL_ARCO_1T':'verde'})
    monkeypatch.setattr(rutas,'_modo_estricto_futbol_activo',lambda *a:False)
    monkeypatch.setattr(rutas,'_obtener_modelo_version_futbol_id',lambda *a:None)
    registrados=[]
    monkeypatch.setattr(rutas,'_registrar_predicciones_futbol',lambda *a,**kw:registrados.append(set(kw['mercados'])) or 0)
    monkeypatch.setattr(rutas,'registrar_apuesta_analizada',lambda **kw:None)
    app=FastAPI();app.include_router(rutas.router)
    return TestClient(app),partido,datos,registrados


def peticion(api,mercado):
    cliente,partido,_,_=api
    r=cliente.post('/api/futbol/analizar',json={'partido_id':partido['id'],'mercado_objetivo':mercado,'lado_objetivo':'OVER','linea_objetivo':5.5})
    assert r.status_code==200,r.text
    return r.json()


def test_api_sin_mitades_conserva_ft_y_no_registra_objetivos_sin_soporte(api_sintetica):
    for p in api_sintetica[2]:
        for lado in ('local','visitante'):
            p[f'{lado}_corners_1t']=p[f'{lado}_corners_2t']=None
    r=peticion(api_sintetica,'CORNERS_1T')
    assert r['objetivo']['media_objetivo'] is None
    assert r['objetivo']['probabilidades_objetivo']=={'over':None,'under':None}
    assert r['mercados_corners']['CORNERS_LOCAL_FT']['media']>0
    assert 'CORNERS_1T' not in r['mercados_corners']
    assert 'CORNERS_1T' not in api_sintetica[3][0]
    assert r['objetivo']['calidad_datos']['elegibilidad']['muestras']['local_home']['ausentes']==30
    assert r['analisis_integral']['periodos'][0]['total'] is None


def test_api_negativo_excluido_y_tiros_por_tiempo_estimados(api_sintetica):
    api_sintetica[2][0]['local_disparos_arco']=-1
    r=peticion(api_sintetica,'DISPAROS_LOCAL_ARCO_1T')
    e=r['objetivo']['calidad_datos']['elegibilidad']
    assert e['estado']=='ESTIMADO'
    assert e['muestras']['local_home']['observados']==0
    assert e['muestras']['local_home']['estimados']==29
    assert e['muestras']['local_home']['invalidos']==1
    assert r['objetivo']['media_objetivo']>0


def test_api_sin_goles_no_inventa_ganador_y_conserva_corners(api_sintetica):
    for p in api_sintetica[2]:
        p['local_goles_total']=p['visitante_goles_total']=None
    r=peticion(api_sintetica,'CORNERS_FT')
    assert r['prediccion_ganador'] is None
    assert r['analisis_integral']['ganador']['local'] is None
    assert r['analisis_integral']['ganador']['marcador'] is None
    assert r['objetivo']['media_objetivo']>0


def test_api_fallo_contexto_no_se_presenta_como_cero_partidos(api_sintetica,monkeypatch):
    def roto(*a,**kw):raise RuntimeError('detalle privado')
    monkeypatch.setattr(rutas,'_obtener_partidos_h2h',roto)
    cliente,partido,_,_=api_sintetica
    r=cliente.post('/api/futbol/analizar',json={'partido_id':partido['id']})
    assert r.status_code==503 and 'privado' not in r.text
    assert 'ceros' in r.text


def test_registro_informativo_sin_goles_no_inventa_probabilidad_ni_confianza(api_sintetica,monkeypatch):
    for p in api_sintetica[2]:
        p['local_goles_total']=p['visitante_goles_total']=None
    monkeypatch.setattr(rutas,'_modo_estricto_futbol_activo',lambda *a:True)
    registros=[]
    monkeypatch.setattr(rutas,'registrar_apuesta_analizada',lambda **kw:registros.append(kw))
    peticion(api_sintetica,'CORNERS_FT')
    assert len(registros)==1
    assert registros[0]['mercado']=='ANALISIS_FT'
    assert registros[0]['probabilidad_sistema'] is None and registros[0]['confianza'] is None
