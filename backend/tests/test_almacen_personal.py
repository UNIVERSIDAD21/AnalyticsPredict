"""SQLite/API sintéticos: jamás usa datos personales, PostgreSQL ni un perfil web."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.rutas_personal import router
from servicios import almacen_personal as store


def entrada(id='id-original'):
    return dict(id=id,titulo='Peña — Bogotá',liga='nba',guardadoEn='2026-10-21T00:12:13.123Z',tipo='resultado',
       snapshot={'probabilidad':0.6281749820031,'cero':0,'ausente':None,'parciales':[None,0,23]},notas='Nota ñ',etiquetas=['revisar'],favorito=True)


def cambio(revision=0,entries=None):
    return dict(revision=revision,operacion=str(uuid4()),datos=dict(cuaderno=entries if entries is not None else [entrada()],favoritos=[],apariencia=None))


@pytest.fixture
def cliente(tmp_path,monkeypatch):
    monkeypatch.setenv('ANALYTICSPREDICT_DATOS_PERSONALES',str(tmp_path/'privado'))
    import db
    monkeypatch.setattr(db,'obtener_pool',lambda:pytest.fail('SQLite no debe usar PostgreSQL'))
    app=FastAPI();app.include_router(router)
    return TestClient(app,base_url='http://127.0.0.1:8000',client=('127.0.0.1',55000))


HEADERS={'X-AP-Personal':'1','Content-Type':'application/json','Origin':'http://127.0.0.1:5173'}
def post(c,body,path='/api/personal'):return c.post(path,json=body,headers=HEADERS)


def test_get_inexistente_no_crea_archivos(cliente,tmp_path):
    r=cliente.get('/api/personal');assert r.status_code==200 and r.json()['revision']==0 and not r.json()['existe']
    assert not (tmp_path/'privado').exists()


def test_guardado_reapertura_exacta_e_idempotencia(cliente):
    body=cambio();saved=post(cliente,body);assert saved.status_code==200
    assert saved.json()['estado']['datos']==body['datos']
    before=store.ruta().read_bytes()
    assert cliente.get('/api/personal').json()['datos']==body['datos']
    assert store.ruta().read_bytes()==before
    repeat=post(cliente,body);assert repeat.status_code==200 and repeat.json()['repetida']
    assert cliente.get('/api/personal').json()['revision']==1
    other=copy.deepcopy(body);other['datos']['cuaderno'][0]['notas']='Otra'
    assert post(cliente,other).status_code==409


def test_editar_notas_no_reescribe_snapshot_fecha_o_id(cliente):
    body=cambio();assert post(cliente,body).status_code==200
    edited=cambio(1);edited['datos']['cuaderno'][0].update(notas='Revisada',etiquetas=['cero'],favorito=False)
    assert post(cliente,edited).status_code==200
    current=cliente.get('/api/personal').json();assert current['revision']==2
    assert current['datos']['cuaderno'][0]['snapshot']==entrada()['snapshot']
    assert current['datos']['cuaderno'][0]['guardadoEn']==entrada()['guardadoEn']
    edited=cambio(2);edited['datos']['cuaderno'][0]['snapshot']['cero']=1
    assert post(cliente,edited).status_code==409
    assert cliente.get('/api/personal').json()==current


def test_revision_conflictiva_y_cas_dos_escritores(cliente):
    assert post(cliente,cambio()).status_code==200
    def write(text):
        b=cambio(1);b['datos']['cuaderno'][0]['notas']=text
        return store.guardar(store.Cambio.model_validate(b))
    with ThreadPoolExecutor(max_workers=2) as pool:
        fs=[pool.submit(write,s) for s in ('pestaña A','pestaña B')]
        results=[]
        for f in fs:
            try:results.append(f.result()['revision_guardada'])
            except store.Conflicto:results.append('conflicto')
    assert set(results)=={2,'conflicto'}
    assert cliente.get('/api/personal').json()['revision']==2


@pytest.mark.parametrize('headers',[
    {'Content-Type':'application/json'},
    {**HEADERS,'Origin':'https://evil.invalid'},
    {**HEADERS,'Origin':'http://127.0.0.1.evil.invalid:5173'},
    {**HEADERS,'Origin':'http://127.0.0.1:9999'},
    {**HEADERS,'Host':'evil.invalid:8000'},
    {**HEADERS,'Content-Type':'text/plain'},
])
def test_guardas_http_sin_escrituras(cliente,headers):
    assert cliente.post('/api/personal',json=cambio(),headers=headers).status_code==403
    assert not store.ruta().exists()


@pytest.mark.parametrize('alter',[
    lambda b:b['datos']['cuaderno'].append(copy.deepcopy(b['datos']['cuaderno'][0])),
    lambda b:b['datos']['cuaderno'][0].update(favorito=1),
    lambda b:b['datos']['cuaderno'][0].update(notas='😀'*3000),
    lambda b:b['datos']['cuaderno'][0].update(snapshot='x'*4_000_000),
    lambda b:b.update(ruta='C:/otro.sqlite3'),
    lambda b:b['datos'].update(favoritos=[dict(tipo='liga',liga='wnba',id='nba',nombre='NBA')]),
])
def test_validacion_capacidad_y_tipos_antes_de_escribir(cliente,alter):
    b=cambio();alter(b)
    assert post(cliente,b).status_code==422
    assert not store.ruta().exists()


def test_disco_lleno_rollback_real_y_sin_exito_falso(cliente,monkeypatch):
    assert post(cliente,cambio()).status_code==200
    old=store.leer();original=store.conectar
    def limited(path,escritura=False):
        c=original(path,escritura)
        if escritura:
            n=c.execute('PRAGMA page_count').fetchone()[0]
            c.execute('PRAGMA max_page_count='+str(n+1))
        return c
    monkeypatch.setattr(store,'conectar',limited)
    b=cambio(1,[entrada(),entrada('otra')]);b['datos']['cuaderno'][1]['snapshot']='x'*1_000_000
    assert post(cliente,b).status_code==507
    assert store.leer()==old


def test_backup_y_restore_en_destino_nuevo(cliente,tmp_path):
    assert post(cliente,cambio()).status_code==200
    backup=post(cliente,{},'/api/personal/respaldo');assert backup.status_code==200 and backup.json()['revision']==1
    paths=list((store.ruta().parent/'respaldos').glob('*.sqlite3'));assert len(paths)==1
    dest=tmp_path/'recuperado/mis_analisis.sqlite3'
    receipt=store.copiar_consistente(paths[0],dest)
    conn=store.conectar(dest)
    try:assert store.leer_conn(conn)==store.leer()
    finally:conn.close()
    assert receipt['archivo_sha256']==hashlib.sha256(dest.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):store.copiar_consistente(paths[0],dest)


def test_cierre_abrupto_no_pierde_commit_anterior_y_get_no_recupera_escribiendo(cliente):
    assert post(cliente,cambio()).status_code==200
    old=store.leer()
    script='''
import os,sqlite3,sys
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA cache_size=1');c.execute('BEGIN IMMEDIATE')
c.execute('UPDATE personal SET revision=900,documento=? WHERE id=1',('x'*2000000,))
os._exit(17)
'''
    child=subprocess.run([sys.executable,'-c',script,str(store.ruta())],capture_output=True,timeout=20)
    assert child.returncode==17
    dirty=store.ruta().read_bytes()
    result=cliente.get('/api/personal');assert result.status_code in (200,503)
    assert store.ruta().read_bytes()==dirty
    recovered=post(cliente,{},'/api/personal/recuperar');assert recovered.status_code==200
    assert recovered.json()==old


def test_archivo_vacio_de_primer_intento_revertido_se_puede_guardar(cliente):
    store.ruta().parent.mkdir();store.ruta().touch()
    before=store.ruta().read_bytes()
    assert cliente.get('/api/personal').json()['existe'] is False
    assert store.ruta().read_bytes()==before
    assert post(cliente,cambio()).status_code==200


def test_no_inicializa_base_ajena_ni_convierte_corrupcion_en_vacio(cliente):
    store.ruta().parent.mkdir()
    with sqlite3.connect(store.ruta()) as conn:conn.execute('CREATE TABLE ajena(valor TEXT)')
    assert cliente.get('/api/personal').status_code==422
    assert post(cliente,cambio()).status_code==422
    with sqlite3.connect(store.ruta()) as conn:
        assert conn.execute('SELECT name FROM sqlite_master WHERE type=\'table\'').fetchall()==[('ajena',)]


def test_profundidad_y_no_finitos_no_crean_archivos(cliente):
    b=cambio();nested=None
    for _ in range(65):nested={'x':nested}
    b['datos']['cuaderno'][0]['snapshot']=nested
    assert post(cliente,b).status_code==422
    assert cliente.post('/api/personal',content='{"revision":NaN}',headers=HEADERS).status_code==422
    assert not store.ruta().exists()
