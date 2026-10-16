"""Regresión real del dominio/calidad NBA y artefactos incompatibles."""
import json
import os
from uuid import uuid4
from datetime import date

import numpy as np
import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from motor_autoentrenamiento.entrenador_bd import EntrenadorBD
from motor_autoentrenamiento.artefacto_nba import cargar_artefacto
from scripts.run_suite_global_testdb import validar_admin_local
from scripts.actualizar_partidos_nba import upsert_records


def test_artefacto_mixto_legacy_se_rechaza_antes_de_servir(tmp_path):
    ruta = tmp_path / 'legacy.npz'
    np.savez(ruta, metadata=np.array(json.dumps({'formato': 1})),
             entity_json=np.array('{}'), w_team=np.zeros((2, 4)),
             w_opp=np.zeros((2, 4)), std_team=np.ones(4), std_opp=np.ones(4))
    with pytest.raises(ValueError, match='incompatible'):
        cargar_artefacto(ruta)


def test_hash_incluye_identidad_de_equipos_y_dominio():
    base = {'id': '1', 'fecha_partido': date(2026, 1, 1), 'equipo_local': 'A'}
    entrenador = EntrenadorBD(None)
    assert len(entrenador._calcular_hash_datos([base])) == 64
    assert entrenador._calcular_hash_datos([base]) != entrenador._calcular_hash_datos([{**base, 'equipo_local': 'B'}])


@pytest.mark.integracion
def test_seleccion_conteo_y_temporadas_excluyen_otras_ligas_invalidos_y_futuros():
    admin_url = os.getenv('TEST_PG_ADMIN_URL')
    if not admin_url:
        pytest.skip('Requiere PostgreSQL local desechable')
    validar_admin_local(admin_url)
    nombre = 'ap_dominio_' + uuid4().hex
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
        try:
            url = make_conninfo(admin_url, dbname=nombre)
            with psycopg.connect(url, autocommit=True) as conn:
                conn.execute('''
                    CREATE TABLE competiciones_baloncesto (id int, codigo text);
                    INSERT INTO competiciones_baloncesto VALUES (1,'nba'),(2,'euroleague');
                    CREATE TABLE equipos (id int, nombre text);
                    INSERT INTO equipos VALUES (1,'NBA A'),(2,'NBA B'),(3,'Euro A'),(4,'Euro B');
                    CREATE TABLE partidos_baloncesto (
                        id int, competicion_id int, temporada_id text, fecha_partido date,
                        tipo_partido text, valido boolean, equipo_local_id int, equipo_visitante_id int,
                        local_q1 int,local_q2 int,local_q3 int,local_q4 int,local_total int,
                        visitante_q1 int,visitante_q2 int,visitante_q3 int,visitante_q4 int,visitante_total int
                    );
                ''')
                for ident, competicion, temporada, fecha, tipo, valido, q, total in [
                    (1,1,'NBA','2026-01-01','REG',True,20,80),
                    (2,2,'EURO','2026-01-01','REG',True,20,80),
                    (3,1,'INVALID','2026-01-01','REG',False,20,80),
                    (4,1,'ZERO','2026-01-01','REG',True,0,0),
                    (5,1,'PRE','2026-01-01','PRE',True,20,80),
                    (6,1,'NEG','2026-01-01','REG',True,-1,80),
                    (7,1,'NULL','2026-01-01','REG',True,None,80),
                    (8,1,'BAD_SUM','2026-01-01','REG',True,30,80),
                    (9,1,'FUTURE','2026-02-01','REG',True,20,80),
                ]:
                    conn.execute('INSERT INTO partidos_baloncesto VALUES (%s,%s,%s,%s,%s,%s,1,2,%s,%s,%s,%s,%s,20,20,20,20,80)',
                                 (ident,competicion,temporada,fecha,tipo,valido,q,q,q,q,total))

            class Pool:
                def connection(self):
                    return psycopg.connect(url)

            entrenador = EntrenadorBD(Pool())
            assert [p['id'] for p in entrenador._obtener_partidos()] == [1,9]
            assert entrenador._obtener_conteo_partidos() == 2
            assert [p['id'] for p in entrenador._obtener_partidos(cutoff_fecha=date(2026,2,1))] == [1]
            assert entrenador._obtener_temporadas_hasta_cutoff(date(2026,2,1),False) == ['NBA']
            assert [p['id'] for p in entrenador._obtener_partidos(incluir_pretemporada=True)] == [1,5,9]
            with psycopg.connect(url, autocommit=True) as conn:
                conn.execute('''ALTER TABLE partidos_baloncesto
                    ADD local_ot int, ADD visitante_ot int, ADD ganador_id int,
                    ADD diferencia_puntos int, ADD hubo_overtime boolean,
                    ADD fuente_datos text, ADD source text, ADD source_game_id text,
                    ADD espn_game_id text, ADD url_referencia text, ADD actualizado_en timestamptz,
                    ADD UNIQUE(source,source_game_id), ADD CHECK(visitante_total > 0)''')
                registro = dict(temporada_id='NBA',competicion_id='1',fecha_partido=date(2026,1,2),tipo_partido='PRE',
                    equipo_local_id='1',equipo_visitante_id='2',local_q1=20,local_q2=20,local_q3=20,local_q4=20,
                    local_ot=0,local_total=80,visitante_q1=20,visitante_q2=20,visitante_q3=20,visitante_q4=20,
                    visitante_ot=0,visitante_total=80,ganador_id=None,diferencia_puntos=0,hubo_overtime=False,
                    fuente_datos='ESPN',source='ESPN',source_game_id='a',espn_game_id='a',url_referencia=None)
                with pytest.raises(psycopg.errors.CheckViolation):
                    upsert_records(conn,[registro,{**registro,'source_game_id':'b','espn_game_id':'b','visitante_total':-1}],False)
                assert conn.execute("SELECT count(*) FROM partidos_baloncesto WHERE source='ESPN'").fetchone() == (0,)
        finally:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(nombre)))
