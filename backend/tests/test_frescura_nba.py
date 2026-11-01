from servicios.frescura_nba import leer_frescura_nba


def modelo():
    return {'modelo_version_id':12,'metricas':{'hash_datos':'hash','training_data_latest_game_date':'2026-06-14'}}


def conexion(temporadas=None,hash_datos='hash'):
    class Cursor:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def execute(self,q,params=None):
            self.query=q;self.params=params;return self
        def fetchone(self): return {'tabla':'modelo_versiones'} if 'to_regclass' in self.query else {'hash_datos':hash_datos,'temporadas_incluidas':temporadas}
        def fetchall(self):
            return [{'fase':'PRE','n':66,'primero':'2026-10-03','ultimo':'2026-10-17'},
                    {'fase':'REG','n':13,'primero':'2026-10-20','ultimo':'2026-10-24'}]
    class Conn:
        def __init__(self):self.c=Cursor()
        def cursor(self,**kw):return self.c
    return Conn()


def test_pre_no_confunde_desfase_dentro_del_dominio():
    r=leer_frescura_nba(conexion(),modelo())
    assert r['finales_elegibles_nuevos']==13 and r['pretemporada_excluida']==66
    assert r['estado']=='HAY_FINALES_ELEGIBLES_NUEVOS'


def test_temporadas_restringidas_y_solo_select():
    c=conexion(['temporada-1']);r=leer_frescura_nba(c,modelo())
    assert c.c.params==['2026-06-14',['temporada-1']]
    assert 'p.temporada_id::text=ANY(%s)' in c.c.query
    assert "dominio.codigo = 'nba'" in c.c.query
    assert r['temporadas_restringidas']==['temporada-1']


def test_registro_no_conciliado_no_inventa_actualizacion():
    r=leer_frescura_nba(conexion(hash_datos='otro'),modelo())
    assert r['estado']=='NO_VERIFICABLE' and 'finales_elegibles_nuevos' not in r
