"""Regresiones de bootstrap aislado, recuperación y propiedad de procesos propios."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS=Path(__file__).resolve().parents[2]/'scripts'


def cargar(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_bootstrap_resuelve_hermano_bajo_aislamiento(tmp_path):
    tools=tmp_path/'herramientas'; tools.mkdir()
    (tools/'verificar_bd.py').write_text('VALOR=731\n',encoding='utf-8')
    (tools/'exportar_vigente.py').write_text('from verificar_bd import VALOR\nassert VALOR==731\nprint("bootstrap_ok")\n',encoding='utf-8')
    result=subprocess.run([sys.executable,'-I','-B',str(SCRIPTS/'ejecutar_herramienta_local.py'),
        '--paquete',str(tmp_path),'exportar_vigente.py'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'bootstrap_ok' in result.stdout


def test_bootstrap_rechaza_traversal(tmp_path):
    mod=cargar('ejecutar_herramienta_local')
    with pytest.raises(ValueError,match='no permitida'): mod.ejecutar(tmp_path,'../externo.py',[])


def test_registro_inmediato_fallo_segundo_hijo_cierra_primero(tmp_path):
    mod=cargar('operar_instalacion_local'); reg=mod.Registro(tmp_path)
    child=reg.spawn('uno',[sys.executable,'-c','import time;time.sleep(60)'])
    try:
        saved=json.loads(reg.path.read_text(encoding='utf-8'))
        assert saved['hijos'][0]['pid']==child.pid
        assert saved['hijos'][0]['identidad']
        with pytest.raises(OSError): reg.spawn('dos',[str(tmp_path/'no_existe.exe')])
    finally: reg.stop()
    assert child.poll() is not None


def test_no_duplica_operacion_viva_ni_cierra_pid_con_otra_identidad(tmp_path):
    mod=cargar('operar_instalacion_local'); reg=mod.Registro(tmp_path)
    child=reg.spawn('uno',[sys.executable,'-c','import time;time.sleep(60)'])
    try:
        with pytest.raises(ValueError,match='activa'): mod.Registro(tmp_path)
        mod.stop_owned({'hijos':[dict(pid=child.pid,identidad='otra_creacion')]})
        assert child.poll() is None
    finally: reg.stop()


def test_espera_monotonica_arranque_en_frio(monkeypatch):
    mod=cargar('operar_instalacion_local'); clock=[0.0]
    monkeypatch.setattr(mod.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(mod.time,'sleep',lambda n:clock.__setitem__(0,clock[0]+n))
    class Response:
        status=200
        def __enter__(self): return self
        def __exit__(self,*args): pass
    def open_url(*args,**kwargs):
        if clock[0]<45: raise OSError('arranque_en_frio')
        return Response()
    monkeypatch.setattr(mod.urllib.request,'urlopen',open_url)
    class Registry: children=[]
    mod.esperar(Registry(),['http://127.0.0.1/salud'],90)
    assert 45<=clock[0]<90


def test_timeout_no_se_disfraza_como_disponible(monkeypatch):
    mod=cargar('operar_instalacion_local'); clock=[0.0]
    monkeypatch.setattr(mod.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(mod.time,'sleep',lambda n:clock.__setitem__(0,clock[0]+n))
    def unavailable(*args,**kwargs): raise OSError('no_disponible')
    monkeypatch.setattr(mod.urllib.request,'urlopen',unavailable)
    class Registry: children=[]
    with pytest.raises(TimeoutError): mod.esperar(Registry(),['http://127.0.0.1/salud'],1)


def test_arranque_fallido_cierra_automaticamente_hijo_ya_creado(tmp_path,monkeypatch):
    mod=cargar('operar_instalacion_local')
    backend=tmp_path/'producto/backend'; backend.mkdir(parents=True)
    (backend/'.env').write_text('# fixture sin datos\n',encoding='utf-8')
    original=mod.Registro; children=[]
    class Registry(original):
        def spawn(self,name,command,**kwargs):
            if name=='frontend': raise OSError('fallo_simulado_segundo_arranque')
            child=super().spawn(name,[sys.executable,'-c','import time;time.sleep(60)'])
            children.append(child); return child
    class Probe:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def connect_ex(self,*args): return 111
    monkeypatch.setattr(mod,'Registro',Registry)
    monkeypatch.setattr(mod.socket,'socket',Probe)
    try:
        with pytest.raises(OSError,match='segundo_arranque'): mod.iniciar(tmp_path)
        assert len(children)==1 and children[0].poll() is not None
        assert json.loads((tmp_path/'runtime/PROCESOS_ACTUALES.json').read_text())['estado']=='DETENIDO'
    finally:
        for child in children:
            if child.poll() is None: child.kill(); child.wait()


def test_creacion_unicode_es_explicita_y_no_reutiliza_locale_C_del_cluster(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS/'herramientas_windows'))
    spec=importlib.util.spec_from_file_location('restore_unicode',SCRIPTS/'herramientas_windows/restaurar_local.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    query=mod.crear_base_sql('ap_fixture','ap_rol').as_string()
    assert 'TEMPLATE template0' in query
    assert "LOCALE_PROVIDER builtin BUILTIN_LOCALE 'C.UTF-8'" in query
    with pytest.raises(ValueError,match='no permitido'): mod.crear_base_sql('ap_fixture','ap_rol','otro','x')


def test_acceso_diario_excluye_operaciones_simultaneas(tmp_path):
    mod=cargar('abrir_instalacion_local'); (tmp_path/'runtime').mkdir()
    with mod.exclusividad(tmp_path):
        with pytest.raises(ValueError,match='en curso'):
            with mod.exclusividad(tmp_path): pass


def test_acceso_diario_rechaza_url_remota_antes_de_iniciar_pg(tmp_path):
    mod=cargar('abrir_instalacion_local'); folder=tmp_path/'producto/backend';folder.mkdir(parents=True)
    (folder/'.env').write_text('DATABASE_URL=postgresql://fixture@remote.invalid:55433/fixture\n',encoding='utf-8')
    with pytest.raises(ValueError,match='destino local'): mod.parametros(tmp_path)


def test_acceso_diario_no_detiene_pg_preexistente_al_rechazar_identidad(tmp_path,monkeypatch):
    mod=cargar('abrir_instalacion_local'); (tmp_path/'runtime').mkdir()
    monkeypatch.setattr(mod,'parametros',lambda root:({'dbname':'fixture'},tmp_path,tmp_path))
    monkeypatch.setattr(mod,'ocupado',lambda port:True)
    def reject(*args): raise ValueError('identidad ajena')
    monkeypatch.setattr(mod,'acreditar_pg',reject)
    def forbidden(*args): raise AssertionError('No debe detener un clúster preexistente')
    monkeypatch.setattr(mod,'ctl',forbidden)
    with pytest.raises(ValueError,match='ajena'): mod.ejecutar(tmp_path,sin_abrir=True)
    assert json.loads((tmp_path/'runtime/SERVICIOS_LOCALES.json').read_text())['estado']=='FALLO_CONSERVADO'


def test_acceso_diario_no_duplica_hijos_propios_disponibles(tmp_path,monkeypatch):
    mod=cargar('abrir_instalacion_local'); (tmp_path/'runtime').mkdir()
    mod.operador.atomico(tmp_path/'runtime/PROCESOS_ACTUALES.json',dict(paquete=str(tmp_path),hijos=[
        dict(nombre='backend',pid=11,identidad='a'),dict(nombre='frontend',pid=12,identidad='a')]))
    monkeypatch.setattr(mod,'parametros',lambda root:({'dbname':'fixture'},tmp_path,tmp_path))
    monkeypatch.setattr(mod,'ocupado',lambda port:True)
    monkeypatch.setattr(mod,'acreditar_pg',lambda *args:dict(pid=10,identidad='a'))
    monkeypatch.setattr(mod.operador,'identidad_pid',lambda pid:'a')
    def forbidden(*args,**kwargs): raise AssertionError('No se deben duplicar hijos')
    monkeypatch.setattr(mod.operador,'iniciar',forbidden)
    class Response:
        status=200
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self):return b'{"bd":{"deshabilitada":false}}'
    monkeypatch.setattr(mod.operador.urllib.request,'urlopen',lambda *args,**kwargs:Response())
    result=mod.ejecutar(tmp_path,sin_abrir=True)
    assert result['reutilizado'] and result['estado']=='DISPONIBLE'
