"""Operación local: exclusión mutua, respaldos y evidencia sin secretos."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from psycopg.conninfo import conninfo_to_dict

from servicios.transporte_agenda import guardar


def directorio_estado():
    return Path(os.environ.get('AP_AGENDA_ESTADO',str(Path.home()/'.local/share/analyticspredict/agenda-sinc')))


@contextmanager
def exclusion(raiz):
    raiz=Path(raiz);raiz.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(raiz/'ejecucion.lock',os.O_CREAT|os.O_RDWR,0o600)
    try:
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Ya hay una sincronización en curso') from exc
        yield
    finally:
        os.close(fd)


def respaldar(url, destino):
    """pg_dump completo; contraseña sólo por entorno del proceso, nunca argv/log."""
    destino=Path(destino)
    if destino.exists():
        raise ValueError('No sobrescribir un respaldo previo')
    if shutil.disk_usage(destino.parent).free < 300*1024*1024:
        raise RuntimeError('Espacio insuficiente para respaldo; BD conservada')
    binary=os.environ.get('AP_PG_DUMP') or shutil.which('pg_dump')
    if not binary:
        raise RuntimeError('pg_dump no disponible; no se aplica el lote')
    env=os.environ.copy()
    for k,v in conninfo_to_dict(url).items():
        if k in ('host','port','dbname','user','password','sslmode','channel_binding'):
            env['PGDATABASE' if k=='dbname' else 'PG'+k.upper().replace('_','')]=v
    result=subprocess.run([binary,'-Fc','--no-owner','--no-acl','-f',str(destino)],
        env=env,capture_output=True,timeout=180,check=False)
    if result.returncode or not destino.exists() or destino.stat().st_size<100:
        # No expone stderr de libpq, que podría incluir configuración sensible.
        raise RuntimeError('Falló pg_dump; no se aplica el lote')
    destino.chmod(0o600)
    restore=os.environ.get('AP_PG_RESTORE') or str(Path(binary).with_name('pg_restore'))
    check=subprocess.run([restore,'--list',str(destino)],env=env,capture_output=True,timeout=30,check=False)
    if check.returncode:
        raise RuntimeError('Archivo de respaldo inválido; no se aplica el lote')
    receipt={'archivo':str(destino),'sha256':hashlib.sha256(destino.read_bytes()).hexdigest(),
        'bytes':destino.stat().st_size,'creado_en':datetime.now(timezone.utc).isoformat(),
        'archivo_verificado':True,'restauracion_este_respaldo':'NO_ENSAYADA_AUTOMATICAMENTE'}
    guardar(destino.with_suffix('.json'),receipt)
    return receipt


def estado_local():
    p=directorio_estado()/'estado.json'
    if not p.exists():
        return {'estado':'SIN_SINCRONIZAR','detalle':'Consultar la agenda sólo lee la BD. No se verificó aún este mecanismo de fuentes.'}
    estado=json.loads(p.read_text())
    if estado.get('estado')=='EN_CURSO':
        fd=os.open(p.parent/'ejecucion.lock',os.O_CREAT|os.O_RDWR,0o600)
        try:
            try:
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                estado={**estado,'estado':'INTERRUMPIDA','detalle':'La ejecución no está activa. Puede reanudarse conservando caché y datos previos; revisar recibos si alcanzó el commit.'}
            except BlockingIOError:
                pass
        finally:
            os.close(fd)
    return estado
