from datetime import datetime
import os
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

from servicios import estado_competiciones as estado
from calidad.elegibilidad_futbol import METRICAS
from scripts.run_suite_global_testdb import validar_admin_local


def test_ventana_tres_meses_calendario_no_noventa_dias():
    desde, hasta = estado.ventana_calendario(datetime(2026, 11, 30, 13, tzinfo=estado.BOGOTA))
    assert desde.date().isoformat() == '2026-11-30'
    assert hasta.date().isoformat() == '2027-02-28'
    assert hasta.hour == 13


def test_artefacto_roto_se_aisla_y_no_filtra_detalles_privados():
    def roto():
        raise ValueError('credencial privada')
    r = estado.modelo_local(roto, 'wnba')
    assert r == {'estado': 'NO_DISPONIBLE_O_NO_APTO', 'calibracion': 'NO_VERIFICADA'}
    assert 'privada' not in str(r)


def test_inventario_mide_null_sin_contar_ceros_como_faltantes():
    comandos = []
    class Cursor:
        def execute(self, sql, params):
            comandos.append((sql, params))
            return self
        def fetchall(self):
            return [{'codigo': 'TEST', 'nombre': 'Test', 'registros': 2, 'finales_con_marcador': 1,
                     'ultimo_final': None, 'invalidados': 0, 'proximos_registrados': 0,
                     **{f'falta_{campo}': int(campo == 'local_corners_total') for campo in estado.FT_CAMPOS}}]
    desde, hasta = estado.ventana_calendario()
    r = estado._inventario(Cursor(), 'partidos_futbol', 'competiciones_futbol', estado.FT_FINAL, estado.FT_CAMPOS, desde, hasta)
    assert r[0]['faltantes_por_campo']['local_corners_total'] == 1
    assert r[0]['faltantes_por_campo']['visitante_corners_total'] == 0
    assert r[0]['calendario']['proximos'] == 0
    assert r[0]['calendario']['completo_acreditado'] is False
    sql, params = comandos[0]
    assert params == (desde, hasta)
    assert all(f'p.{campo} IS NULL' in sql for campo in estado.FT_CAMPOS)
    assert 'SELECT' in sql and not any(x in sql for x in ('UPDATE ', 'INSERT ', 'DELETE '))


def test_modelo_wnba_muestra_publicacion_no_todo_el_snapshot():
    m = {'version': 'v1', 'ajuste_final': {'fecha_max': '2026-09-24', 'n': 1840}, 'datos': [1]*1997}
    r = estado.modelo_local(lambda: m, 'wnba')
    assert r['partidos'] == 1840 and r['calibracion'] == 'SIN_CALIBRAR'


def test_calendario_no_instalado_conserva_nd(monkeypatch):
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql): return self
        def fetchone(self): return {'tabla': None}
    class Conn:
        def cursor(self, **kwargs): return Cursor()
    def inventario(cursor, tabla, *args, **kwargs):
        return [{'codigo': 'wnba'}] if tabla == 'partidos_baloncesto' else []
    monkeypatch.setattr(estado, '_inventario', inventario)
    monkeypatch.setattr(estado, 'cargar_wnba', lambda: {'version': 'x', 'ajuste_final': {'n': 1, 'fecha_max': '2020-01-01'}})
    r = estado.leer_competiciones(Conn())
    calendario = r['baloncesto']['wnba']['calendario']
    assert calendario['proximos'] is None
    assert calendario['estado'] == 'ALMACEN_NO_INSTALADO'


@pytest.mark.integracion
def test_inventario_sql_ceros_invalidos_y_limite_horario(monkeypatch):
    """Contrato SQL real únicamente contra una base sintética propia y desechable."""
    admin_url = os.getenv('TEST_PG_ADMIN_URL')
    if not admin_url:
        pytest.skip('PostgreSQL local sintético requerido')
    validar_admin_local(admin_url)
    nombre = 'ap_estado_test_' + uuid4().hex
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
        try:
            url = make_conninfo(**{**conninfo_to_dict(admin_url), 'dbname': nombre})
            with psycopg.connect(url) as conn:
                for tabla in ('competiciones_baloncesto', 'competiciones_futbol'):
                    conn.execute(f'CREATE TABLE {tabla}(id int PRIMARY KEY,codigo text,nombre text)')
                for tabla, campos, fecha in (
                    ('partidos_baloncesto', estado.BB_CAMPOS, 'date'),
                    ('partidos_futbol', sorted({c for cols in METRICAS.values() for c in cols}), 'timestamptz'),
                ):
                    columnas = ','.join(f'{campo} int' for campo in campos)
                    conn.execute(f'CREATE TABLE {tabla}(id int,competicion_id int,fecha_partido {fecha},valido bool,estado text,{columnas})')
                conn.execute('ALTER TABLE partidos_futbol ADD COLUMN temporada_id int, ADD COLUMN hubo_tiempo_extra bool DEFAULT false, ADD COLUMN local_goles_et int, ADD COLUMN visitante_goles_et int')
                conn.execute("CREATE TABLE temporadas_futbol(id int,nombre text)")
                conn.execute("INSERT INTO competiciones_baloncesto VALUES(1,'wnba','WNBA')")
                conn.execute("INSERT INTO competiciones_futbol VALUES(1,'TEST','Test'),(2,'VACIA','Sin partidos')")
                conn.execute("""INSERT INTO partidos_futbol
                    (id,competicion_id,fecha_partido,valido,estado,local_goles_total,visitante_goles_total,local_corners_total,visitante_corners_total,local_disparos_arco,visitante_disparos_arco)
                    VALUES(1,1,'2026-10-24',true,'FINALIZADO',0,0,NULL,0,0,0),
                          (2,1,'2026-10-26',false,'PROGRAMADO',NULL,NULL,NULL,NULL,NULL,NULL),
                          (3,1,'2026-10-26',true,'PROGRAMADO',NULL,NULL,NULL,NULL,NULL,NULL),
                          (4,1,'2026-10-24',true,'FINALIZADO',NULL,1,NULL,NULL,NULL,NULL)""")
                conn.execute('CREATE TABLE fixtures_wnba(fecha_local date,inicio_utc timestamptz,estado text,registro jsonb)')
                conn.execute("""INSERT INTO fixtures_wnba VALUES
                    ('2027-01-25','2027-01-25T19:00:00Z','PROGRAMADO','{}'),
                    ('2027-01-25','2027-01-25T21:00:00Z','PROGRAMADO','{}')""")
                conn.commit()
                conn.read_only = True
                monkeypatch.setattr(estado, 'cargar_wnba', lambda: {'version': 'prueba', 'ajuste_final': {'n': 1, 'fecha_max': '2020-01-01'}})
                r = estado.leer_competiciones(conn, datetime(2026, 10, 25, 15, tzinfo=estado.BOGOTA))
                futbol = {f['codigo']: f for f in r['futbol']}
                assert futbol['TEST']['finales_con_marcador'] == 1
                assert futbol['TEST']['faltantes_por_campo']['local_corners_total'] == 1
                assert futbol['TEST']['faltantes_por_campo']['visitante_corners_total'] == 0
                assert futbol['TEST']['faltantes_por_campo']['local_goles_total'] == 0
                assert futbol['TEST']['calendario']['proximos'] == 1
                assert futbol['VACIA']['registros'] == futbol['VACIA']['calendario']['proximos'] == 0
                assert r['baloncesto']['wnba']['calendario']['proximos'] == 1
                calidad = futbol['TEST']['elegibilidad']
                assert calidad['finales_validos'] == 2 and calidad['finales_sin_ft'] == 1
                assert calidad['mercados']['goles_ft']['denominador'] == 2
                assert calidad['mercados']['goles_ft']['observados'] == 1
                assert calidad['mercados']['corners_ft']['denominador'] == 1
                assert calidad['mercados']['corners_ft']['ausentes'] == 1
                assert calidad['mercados']['disparos_arco_1t']['observados'] == 0
                assert calidad['mercados']['disparos_arco_1t']['estimados'] == 1
                conn.rollback()
        finally:
            admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(nombre)))
