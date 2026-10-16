"""Coeficientes reales, recarga sin entrenamiento, calidad y atomicidad SQL."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool
import pytest

from motor_futbol.entrenamiento.dataset import seleccionar, describir
from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.entrenamiento.gestor_versiones import GestorVersiones
from motor_futbol.modelos.artefacto import cargar, exportar, sha256
from motor_futbol.modelos.base import ModeloPrediccionBase
from motor_futbol.prediccion.predictor import PredictorFutbol
from motor_futbol.tipos import TipoModelo, ConfiguracionEntrenamiento
from motor_futbol.excepciones import EquipoNoEncontrado
from scripts.run_suite_global_testdb import validar_admin_local
from scripts.entrenar_futbol import ejecutar, main


@pytest.fixture
def partidos():
    return [dict(id=uuid4(), fecha_partido=datetime(2026, 1, 1, tzinfo=timezone.utc)+timedelta(days=i),
        equipo_local='Club A' if i % 2 else 'Club B', equipo_visitante='Club B' if i % 2 else 'Club A',
        competicion_id='liga', temporada_id='temporada', valido=True, estado='FINALIZADO',
        local_corners_1t=0, local_corners_2t=3, visitante_corners_1t=2, visitante_corners_2t=4,
        local_corners_total=3, visitante_corners_total=6,
        local_goles_1t=0, local_goles_2t=1, visitante_goles_1t=1, visitante_goles_2t=1,
        local_goles_total=1, visitante_goles_total=2,
        local_disparos_total=10, local_disparos_arco=0, visitante_disparos_total=12, visitante_disparos_arco=3)
        for i in range(12)]


@pytest.fixture
def modelos(partidos):
    e = EntrenadorFutbol(None, min_partidos=5)
    e._obtener_partidos_entrenamiento = lambda: partidos
    resultados = e.entrenar_completo()
    assert all(r.n_partidos == 12 for r in resultados.values())
    return [e.obtener_modelo_corners(), e.obtener_modelo_goles(), e.obtener_modelo_disparos()]


def test_codec_conserva_predicciones_metricas_y_dataset(modelos, tmp_path):
    for original in modelos:
        payload = exportar(original)
        recargado = cargar(payload)
        assert recargado.to_dict() == payload
        assert recargado.predecir_partido('Club A', 'Club B') == original.predecir_partido('Club A', 'Club B')
        assert recargado.metricas['ambito'] == 'AJUSTE_IN_SAMPLE_NO_VALIDACION'
        assert recargado.dataset['n_filas_diseno'] == 24
        ruta = tmp_path / (original.tipo.value + '.npz')
        original.guardar(str(ruta))
        assert ModeloPrediccionBase.cargar(str(ruta)).to_dict() == payload
        with pytest.raises(EquipoNoEncontrado):
            recargado.predecir_partido('Equipo sin entrenar', 'Club A')


@pytest.mark.parametrize('caso', ['target', 'dimension', 'nan', 'indice', 'std', 'dominio', 'calibrador'])
def test_codec_rechaza_artefactos_no_aptos(modelos, caso):
    p = exportar(modelos[0]); target = p['targets'][0]
    if caso == 'target': del p['pesos'][target]
    if caso == 'dimension': p['pesos'][target] = [1]
    if caso == 'nan': p['pesos'][target][0] = float('nan')
    if caso == 'indice': p['entidad_a_indice'] = {'club a': 1, 'club b': 1}
    if caso == 'std': p['std_residuales'][target] = -1
    if caso == 'dominio': p['dominio'] = 'NBA'
    if caso == 'calibrador': p['calibrador'] = {'inventado': True}
    with pytest.raises(ValueError): cargar(p)


def test_npz_legacy_no_es_un_artefacto_apto(tmp_path):
    ruta = tmp_path / 'legacy.npz'
    np.savez(ruta, pesos=np.ones(4))
    with pytest.raises(ValueError, match='legacy'):
        ModeloPrediccionBase.cargar(str(ruta))


def test_targets_null_no_se_imputan_y_ceros_si_son_datos(partidos):
    partidos[0]['local_disparos_arco'] = None
    partidos[1]['local_disparos_arco'] = 11
    partidos[2]['valido'] = False
    partidos[3]['local_goles_2t'] = None
    partidos[4]['local_goles_total'] = 10
    shots, motivos = seleccionar(partidos, TipoModelo.DISPAROS)
    assert len(shots) == 9 and motivos == {'target_ausente': 1, 'arco_mayor_que_total': 1, 'no_final_o_invalido': 1}
    assert any(p['local_disparos_arco'] == 0 for p in shots)
    goles, motivos = seleccionar(partidos, TipoModelo.GOLES)
    assert len(goles) == 9
    assert motivos['tiempos_incompatibles_con_total'] == 1
    partidos.append(deepcopy(partidos[5]))
    assert seleccionar(partidos, TipoModelo.CORNERS)[1]['id_duplicado'] == 2


def test_hash_cambia_con_valores_no_con_orden_y_poda_por_equipo(partidos):
    a = describir(partidos, TipoModelo.DISPAROS)
    assert a == describir(list(reversed(partidos)), TipoModelo.DISPAROS)
    partidos[0]['local_disparos_arco'] = 1
    assert describir(partidos, TipoModelo.DISPAROS)['hash_sha256'] != a['hash_sha256']
    partidos[0]['equipo_local'] = 'Equipo escaso'
    validos, excluidos = seleccionar(partidos, TipoModelo.DISPAROS, min_partidos_equipo=5)
    assert len(validos) == 11 and excluidos == {'equipo_sin_minimo': 1}


@pytest.fixture
def registro_db():
    url = os.getenv('TEST_PG_ADMIN_URL')
    if not url: pytest.skip('Requiere PostgreSQL sintético exclusivo')
    validar_admin_local(url)
    nombre = 'ap_futbol_ml_' + uuid4().hex
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
        try:
            with ConnectionPool(make_conninfo(url, dbname=nombre), min_size=1, max_size=2) as pool:
                with pool.connection() as c:
                    c.execute('''CREATE TYPE mercado_futbol AS ENUM('CORNERS_FT','GOLES_FT','DISPAROS_FT');
                        CREATE TABLE modelo_versiones_futbol(
                          id serial PRIMARY KEY, version integer, nombre varchar(255), mercado_principal mercado_futbol,
                          fecha_entrenamiento timestamptz DEFAULT now(), cutoff_entrenamiento date,
                          fecha_min_entrenamiento date, fecha_max_entrenamiento date, partidos_entrenamiento integer,
                          equipos integer, hash_datos varchar(32), config_entrenamiento jsonb, metadata jsonb,
                          activo boolean DEFAULT false, mae_general numeric);''')
                yield pool
        finally:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(nombre)))


@pytest.mark.integracion
def test_publicar_recargar_sin_reentrenar_ni_fingir_activacion(registro_db, modelos, partidos, monkeypatch):
    gestor = GestorVersiones(registro_db)
    ids = gestor.guardar_lote(modelos)
    assert PredictorFutbol(registro_db).modelos_entrenados is False
    for modelo in modelos:
        gestor.activar_version(modelo.tipo, ids[modelo.tipo.value])
    monkeypatch.setattr(EntrenadorFutbol, 'entrenar_completo', lambda *_: pytest.fail('Serving no debe entrenar'))
    predictor = PredictorFutbol(registro_db)
    assert predictor.modelos_entrenados is True
    assert all(s['estado'] == 'CARGADO' for s in predictor.estado_carga.values())
    for modelo in modelos:
        cargado = getattr(predictor, 'modelo_' + modelo.tipo.value)
        assert cargado.version_id == ids[modelo.tipo.value]
        assert cargado.predecir_partido('Club A', 'Club B') == modelo.predecir_partido('Club A', 'Club B')
    predictor.cargar_modelos()
    with registro_db.connection() as c:
        assert c.execute('SELECT count(*) FROM modelo_versiones_futbol').fetchone()[0] == 3
    for version in (-1, ids['goles']):
        with pytest.raises(ValueError): gestor.activar_version(TipoModelo.CORNERS, version)
    assert gestor.obtener_activa(TipoModelo.CORNERS)['id'] == ids['corners']
    # El CLI conserva el modelo, publica solo la familia solicitada y la recarga.
    monkeypatch.setattr(EntrenadorFutbol, '_obtener_partidos_entrenamiento', lambda *_: partidos)
    args = SimpleNamespace(competicion=None, temporada_id=None, fecha_corte=None, alpha=5.0,
                           min_partidos=5, min_partidos_equipo=5, entrenar=True, guardar=True,
                           activar=False, familia=['disparos'])
    informe = ejecutar(registro_db, args)
    assert list(informe['versiones_guardadas']) == ['disparos'] and not informe['activadas']
    assert gestor.obtener_activa(TipoModelo.DISPAROS)['id'] == ids['disparos']


@pytest.mark.integracion
def test_corrupto_no_se_sirve_ni_se_activa_y_recarga_retira_version_anterior(registro_db, modelos):
    gestor = GestorVersiones(registro_db)
    ids = gestor.guardar_lote(modelos, activar=True)
    predictor = PredictorFutbol(registro_db)
    assert predictor.modelo_corners is not None
    with registro_db.connection() as c:
        c.execute("UPDATE modelo_versiones_futbol SET metadata=jsonb_set(metadata,'{artefacto_sha256}','\"corrupto\"') WHERE id=%s", [ids['corners']])
    predictor.cargar_modelos()
    assert predictor.modelo_corners is None
    assert predictor.estado_carga['corners']['estado'] == 'ARTEFACTO_NO_APTO'
    assert predictor.modelo_goles is not None
    with pytest.raises(ValueError): gestor.activar_version(TipoModelo.CORNERS, ids['corners'])
    with registro_db.connection() as c:
        assert c.execute('SELECT count(*) FROM modelo_versiones_futbol WHERE activo').fetchone()[0] == 3


@pytest.mark.integracion
def test_publicacion_lote_atomica_si_falla_segunda_familia(registro_db, modelos):
    with registro_db.connection() as c:
        c.execute("ALTER TABLE modelo_versiones_futbol ADD CONSTRAINT fallo_sintetico CHECK(mercado_principal<>'DISPAROS_FT')")
    with pytest.raises(psycopg.errors.CheckViolation):
        GestorVersiones(registro_db).guardar_lote(modelos, activar=True)
    with registro_db.connection() as c:
        assert c.execute('SELECT count(*) FROM modelo_versiones_futbol').fetchone() == (0,)
    assert all(m.version_id is None for m in modelos)


@pytest.mark.integracion
def test_consulta_activa_rechaza_ambiguedad(registro_db, modelos):
    gestor = GestorVersiones(registro_db)
    gestor.guardar_lote(modelos, activar=True)
    segundo = gestor.guardar_lote([modelos[0]])['corners']
    with registro_db.connection() as c:
        c.execute('UPDATE modelo_versiones_futbol SET activo=true WHERE id=%s', [segundo])
    assert PredictorFutbol(registro_db).modelo_corners is None
    with pytest.raises(ValueError, match='Más de una'): gestor.obtener_activa(TipoModelo.CORNERS)


def test_cli_no_entrena_por_defecto_y_rechaza_guardado_implicito(partidos, monkeypatch):
    monkeypatch.setattr(EntrenadorFutbol, '_obtener_partidos_entrenamiento', lambda *_: partidos)
    monkeypatch.setattr(EntrenadorFutbol, 'entrenar_completo', lambda *_: pytest.fail('No solicitado'))
    args = SimpleNamespace(competicion=None, temporada_id=None, fecha_corte=None, alpha=5.0,
                           min_partidos=5, min_partidos_equipo=5, entrenar=False, guardar=False, activar=False)
    informe = ejecutar(None, args)
    assert informe['versiones_guardadas'] == {} and not informe['activadas']
    assert informe['dataset']['disparos']['n_partidos'] == 12
    with pytest.raises(SystemExit) as exc: main(['--guardar'])
    assert exc.value.code == 2


@pytest.mark.integracion
def test_selector_sql_filtra_invalido_estado_cutoff_temporada_y_copa(registro_db, partidos):
    from motor_futbol.entrenamiento.dataset import CAMPOS
    campos = sorted({k for lista in CAMPOS.values() for k in lista} | {'local_corners_total', 'visitante_corners_total', 'local_goles_total', 'visitante_goles_total'})
    with registro_db.connection() as c:
        c.execute('''CREATE TABLE equipos_futbol(id text,nombre text);
            INSERT INTO equipos_futbol VALUES('a','Club A'),('b','Club B');
            CREATE TABLE competiciones_futbol(id text,codigo text);
            INSERT INTO competiciones_futbol VALUES('liga','ESP_LALIGA'),('copa','EUR_CHAMPIONS');''')
        c.execute(sql.SQL('''CREATE TABLE partidos_futbol(id uuid,fecha_partido timestamptz,competicion_id text,temporada_id text,
            equipo_local_id text,equipo_visitante_id text,estado text,valido boolean,{})''').format(sql.SQL(',').join(sql.SQL('{} integer').format(sql.Identifier(k)) for k in campos)))
        for i, p in enumerate(partidos):
            valores = [p['id'], p['fecha_partido'], 'copa' if i == 3 else 'liga', 'otra' if i == 4 else 'temporada', 'a', 'b',
                       'PROGRAMADO' if i == 1 else 'FINALIZADO', i != 2, *[p[k] for k in campos]]
            c.execute(sql.SQL('INSERT INTO partidos_futbol VALUES({})').format(sql.SQL(',').join(sql.Placeholder() for _ in valores)), valores)
    config = ConfiguracionEntrenamiento(temporadas=['temporada'], fecha_corte=datetime(2026,1,10).date(), min_partidos_equipo=1)
    e = EntrenadorFutbol(registro_db, config=config, min_partidos=1)
    efectivos = e._obtener_partidos_entrenamiento()
    assert {p['id'] for p in efectivos} == {partidos[i]['id'] for i in (0,5,6,7,8)}
    informe = e.diagnosticar_dataset()
    assert all(d['n_partidos'] == 5 for d in informe.values())


@pytest.mark.integracion
def test_serving_no_aplica_modelo_nuevo_a_partido_historico(registro_db, modelos, monkeypatch):
    from motor_futbol.excepciones import ErrorPrediccion
    GestorVersiones(registro_db).guardar_lote(modelos, activar=True)
    p = PredictorFutbol(registro_db)
    monkeypatch.setattr(p, '_obtener_info_partido', lambda _: {'fecha_partido': datetime(2026, 1, 12, tzinfo=timezone.utc)})
    with pytest.raises(ErrorPrediccion, match='no existía antes'):
        p.predecir_partido(uuid4())


@pytest.mark.integracion
def test_metricas_sin_ejemplos_ni_reentrenamiento_ficticio(registro_db, modelos, monkeypatch):
    import asyncio
    from api import rutas_metricas_futbol as rutas
    from api import rutas_analisis_futbol as analisis
    monkeypatch.setattr(rutas, 'obtener_pool', lambda: registro_db)
    monkeypatch.setattr(analisis, '_predictor_futbol_ml', None)
    vacio = asyncio.run(rutas.obtener_estado_modelos())
    assert vacio.modelos == [] and vacio.proximo_reentrenamiento is None
    ids = GestorVersiones(registro_db).guardar_lote(modelos, activar=True)
    registrados = asyncio.run(rutas.obtener_estado_modelos())
    assert len(registrados.modelos) == 3
    assert all(m.ambito_metricas == 'AJUSTE_IN_SAMPLE_NO_VALIDACION' and not m.cargado for m in registrados.modelos)
    primero = analisis._obtener_predictor_futbol_ml(registro_db)
    assert all(m.cargado for m in asyncio.run(rutas.obtener_estado_modelos()).modelos)
    with registro_db.connection() as c:
        c.execute('UPDATE modelo_versiones_futbol SET activo=false WHERE id=%s', [ids['corners']])
    segundo = analisis._obtener_predictor_futbol_ml(registro_db)
    assert segundo is not primero and primero.modelo_corners is not None and segundo.modelo_corners is None
    with registro_db.connection() as c:
        c.execute("UPDATE modelo_versiones_futbol SET metadata='{}' WHERE id=%s", [ids['goles']])
    corrupto = asyncio.run(rutas.obtener_estado_modelos())
    assert corrupto.artefactos_no_aptos == 1
    assert [m.tipo_modelo for m in corrupto.modelos] == ['disparos']


def test_metricas_fallo_bd_no_devuelve_ejemplos_ni_detalle_privado(monkeypatch):
    import asyncio
    from api import rutas_metricas_futbol as rutas
    from fastapi import HTTPException
    def fallo(): raise RuntimeError('informacion privada')
    monkeypatch.setattr(rutas, 'obtener_pool', fallo)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(rutas.obtener_estado_modelos())
    assert exc.value.status_code == 503 and 'privada' not in str(exc.value.detail)
