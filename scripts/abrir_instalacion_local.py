"""Acceso diario a una instalación ya restaurada. Nunca conecta a Neon ni migra datos."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import webbrowser

_spec = importlib.util.spec_from_file_location('operador_diario', Path(__file__).with_name('operar_instalacion_local.py'))
operador = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(operador)


@contextmanager
def exclusividad(raiz):
    path = raiz / 'runtime/ACCESO_DIARIO.lock'
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('Ya existe un arranque/cierre de esta instalación en curso') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def parametros(raiz):
    from dotenv import dotenv_values
    from psycopg.conninfo import conninfo_to_dict
    params = conninfo_to_dict(dotenv_values(raiz / 'producto/backend/.env')['DATABASE_URL'])
    if params.get('host') != '127.0.0.1' or params.get('port') != '55433' or params.get('hostaddr'):
        raise ValueError('El acceso diario exige el destino local 127.0.0.1:55433, sin redirecciones')
    config = json.loads((raiz / 'RUNTIME_LOCAL.json').read_text(encoding='utf-8'))
    run = Path(config['postgres_runtime']).resolve()
    pg = Path(config['pg_bin']).resolve()
    if (run / 'datos/PG_VERSION').read_text(encoding='utf-8').strip() != '18':
        raise ValueError('Versión/ruta del clúster propio no acreditada')
    return params, run, pg


def ocupado(port):
    with socket.socket() as probe:
        return probe.connect_ex(('127.0.0.1', port)) == 0


def acreditar_pg(params, run):
    import psycopg
    # Parámetros explícitos: no permitir que PGHOSTADDR/PGSERVICE suplanten el destino.
    for key in ('PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS'):
        os.environ.pop(key, None)
    with psycopg.connect(**params, connect_timeout=5, application_name='ap_acceso_diario') as conn:
        conn.read_only = True
        base, host, port = conn.execute("SELECT current_database(),host(inet_server_addr()),inet_server_port()").fetchone()
        if base != params['dbname'] or host != '127.0.0.1' or port != 55433:
            raise ValueError('La identidad SQL del clúster no coincide; no se modifica ningún servicio')
    # El rol de la aplicación conserva mínimos permisos; no conceder lectura global de settings.
    with psycopg.connect(host='127.0.0.1', port=55433, user='ap_migracion_admin', dbname='postgres',
                         passfile=str(run / 'pgpass.conf'), sslmode='disable', connect_timeout=5,
                         application_name='ap_identidad_diaria') as conn:
        conn.read_only = True
        data = conn.execute("SELECT current_setting('data_directory')").fetchone()[0]
        if Path(data).resolve() != (run / 'datos').resolve():
            raise ValueError('Ruta SQL ajena al clúster propio')
    pid = int((run / 'datos/postmaster.pid').read_text(encoding='utf-8').splitlines()[0])
    identity = operador.identidad_pid(pid)
    if identity is None:
        raise ValueError('No se acreditó identidad del PID PostgreSQL')
    return dict(pid=pid, identidad=identity, datos=str(run / 'datos'), puerto=55433, log=str(run / 'postgresql.log'))


def ctl(pg, run, action, record, path):
    args = [str(pg / 'pg_ctl.exe'), '-D', str(run / 'datos'), '-w', '-t', '30']
    args += ['-l', str(run / 'postgresql.log')] if action == 'start' else ['-m', 'fast']
    options = dict(creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    proc = subprocess.Popen(args + [action], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)
    record['pg_ctl'] = dict(pid=proc.pid, identidad=operador.identidad_pid(proc.pid), accion=action)
    operador.atomico(path, record)  # Registrar antes de esperar.
    if proc.wait(timeout=40) != 0:
        raise RuntimeError('pg_ctl no confirmó la operación; revisar el registro propio')


def detener_api(raiz):
    pointer = raiz / 'runtime/PROCESOS_ACTUALES.json'
    if not pointer.exists():
        return
    old = json.loads(pointer.read_text(encoding='utf-8'))
    if Path(old['paquete']).resolve() != raiz:
        raise ValueError('Registro API ajeno a la instalación')
    operador.stop_owned(old)
    deadline = time.monotonic() + 20
    while any(c.get('identidad') and operador.identidad_pid(c['pid']) == c['identidad'] for c in old['hijos']):
        if time.monotonic() >= deadline:
            raise RuntimeError('Cierre propio no confirmado; conservar el registro')
        time.sleep(.1)
    old['estado'] = 'DETENIDO_VERIFICADO'
    operador.atomico(pointer, old); operador.atomico(Path(old['registro']), old)


def ejecutar(raiz, *, detener=False, sin_abrir=False, espera=90):
    raiz = raiz.resolve()
    params, run, pg = parametros(raiz)
    path = raiz / 'runtime/SERVICIOS_LOCALES.json'
    with exclusividad(raiz):
        record = dict(paquete=str(raiz), estado='INICIANDO', base=params['dbname'], registro_api=str(raiz / 'runtime/PROCESOS_ACTUALES.json'))
        started = False
        if detener:
            if not path.exists():
                raise ValueError('Falta registro de acceso diario: no se detiene un servicio sin conciliarlo')
            record = json.loads(path.read_text(encoding='utf-8'))
            if Path(record['paquete']).resolve() != raiz:
                raise ValueError('Registro de servicios ajeno')
            detener_api(raiz)
            if ocupado(55433):
                current = acreditar_pg(params, run)
                if current != record.get('postgres'):
                    raise ValueError('Cambió la identidad PostgreSQL; no se detiene')
                ctl(pg, run, 'stop', record, path)
            record['estado'] = 'DETENIDO_VERIFICADO'; operador.atomico(path, record)
            return record
        operador.atomico(path, record)
        try:
            if not ocupado(55433):
                ctl(pg, run, 'start', record, path); started = True
                pid = int((run / 'datos/postmaster.pid').read_text(encoding='utf-8').splitlines()[0])
                record['postgres_iniciado'] = dict(pid=pid, identidad=operador.identidad_pid(pid), datos=str(run / 'datos'))
                operador.atomico(path, record)
            record['postgres'] = acreditar_pg(params, run)
            operador.atomico(path, record)
            pointer = raiz / 'runtime/PROCESOS_ACTUALES.json'
            old = json.loads(pointer.read_text(encoding='utf-8')) if pointer.exists() else None
            alive = [c for c in (old or {}).get('hijos', []) if c.get('identidad') and operador.identidad_pid(c['pid']) == c['identidad']]
            if alive:
                if Path(old['paquete']).resolve() != raiz or len(alive) != 2 or {c['nombre'] for c in alive} != {'backend', 'frontend'}:
                    raise ValueError('Operación parcial/ajena: conservar registros y conciliar antes de continuar')
                record['reutilizado'] = True
            else:
                os.environ.pop('ANALYTICSPREDICT_SOLO_BASE_LOCAL', None)
                os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
                operador.iniciar(raiz, espera=espera)
                record['reutilizado'] = False
            with operador.urllib.request.urlopen('http://127.0.0.1:8000/api/local/estado', timeout=10) as response:
                if json.load(response)['bd']['deshabilitada']:
                    raise ValueError('El backend no acredita el modo local con BD')
            with operador.urllib.request.urlopen('http://127.0.0.1:5173/hoy', timeout=10) as response:
                if response.status != 200:
                    raise ValueError('La interfaz no confirmó disponibilidad')
            record['estado'] = 'DISPONIBLE'; operador.atomico(path, record)
            if not sin_abrir:
                webbrowser.open('http://127.0.0.1:5173/hoy')
            return record
        except BaseException:
            # No detener una API reutilizada ni un PG que ya estaba encendido.
            if not record.get('reutilizado', True):
                detener_api(raiz)
            if started and record.get('postgres_iniciado'):
                own = record['postgres_iniciado']
                disk_pid = int((run / 'datos/postmaster.pid').read_text(encoding='utf-8').splitlines()[0])
                if disk_pid == own['pid'] and own['identidad'] and operador.identidad_pid(disk_pid) == own['identidad']:
                    ctl(pg, run, 'stop', record, path)
            record['estado'] = 'FALLO_CONSERVADO'; operador.atomico(path, record)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paquete', type=Path, required=True)
    parser.add_argument('--detener', action='store_true')
    parser.add_argument('--sin-abrir', action='store_true')
    parser.add_argument('--espera-api', type=int, default=90)
    args = parser.parse_args()
    ejecutar(args.paquete, detener=args.detener, sin_abrir=args.sin_abrir, espera=args.espera_api)
    print('AnalyticsPredict local: cierre verificado.' if args.detener else 'AnalyticsPredict local disponible: http://127.0.0.1:5173/hoy')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Operación incompleta (' + type(exc).__name__ + '): revisar registros locales; no se modifica Neon ni servicios ajenos.')
        raise SystemExit(1)
