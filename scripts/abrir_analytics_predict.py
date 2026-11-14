"""Acceso personal: reutiliza servicios acreditados y recupera solo el faltante."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import urllib.request
import uuid
import webbrowser


def powershell_json(script):
    shell = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    completed = subprocess.run(
        [str(shell), '-NoProfile', '-NonInteractive', '-Command', script],
        capture_output=True, timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if completed.returncode:
        raise RuntimeError('No se pudo verificar el proceso que ocupa un puerto local.')
    return json.loads(completed.stdout.decode('utf-8-sig').strip() or 'null')


def identidad_puerto(port):
    # CreationDate de CIM conserva microsegundos cuando el proceso es de otra
    # sesión y QUERY_LIMITED_INFORMATION no está disponible para el usuario.
    script = (
        f"$c=@(Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction SilentlyContinue);"
        "if($c.Count -eq 0){'null';exit 0};"
        "$ids=@($c.OwningProcess|Select-Object -Unique);"
        "if($ids.Count -ne 1){throw 'Puerto ambiguo'};"
        "$p=Get-CimInstance Win32_Process -Filter ('ProcessId = '+$ids[0]);"
        "if($null -eq $p -or $null -eq $p.CreationDate){throw 'Identidad ausente'};"
        "[PSCustomObject]@{pid=[int]$p.ProcessId;nombre=$p.Name;"
        "creacion_filetime=[string]$p.CreationDate.ToUniversalTime().ToFileTimeUtc()}|ConvertTo-Json -Compress"
    )
    return powershell_json(script)


def comandos(root):
    python = str(root / 'runtime/python/python.exe')
    scripts = root / 'producto/scripts'
    return {
        'backend': [python, '-X', 'utf8', '-B', str(scripts / 'ejecutar_herramienta_local.py'),
                    '--paquete', str(root), 'arrancar_backend.py', '--puerto', '8000'],
        'frontend': [python, '-X', 'utf8', '-B', str(scripts / 'servir_frontend_local.py'),
                     '--directorio', str(root / 'producto/frontend/dist'), '--puerto', '5173'],
    }


def verificar_existente(root, old, name, port, command):
    current = identidad_puerto(port)
    if current is None:
        return None
    if not old or Path(old.get('paquete', '')).resolve() != root:
        raise RuntimeError('Puerto ocupado sin registro de esta instalación; se conserva el proceso.')
    records = [c for c in old.get('hijos', []) if c.get('nombre') == name]
    if len(records) != 1:
        raise RuntimeError('Registro del servicio incompleto; se conserva el proceso.')
    child = records[0]
    command_hash = hashlib.sha256(json.dumps(command).encode()).hexdigest()
    if (current['pid'] != child['pid'] or current['nombre'].lower() != 'python.exe'
            or not child.get('identidad')
            or int(current['creacion_filetime']) // 10 != int(child['identidad']) // 10
            or child.get('comando_sha256') != command_hash):
        raise RuntimeError('El puerto pertenece a un proceso distinto del registrado; no se modifica.')
    if name == 'frontend':
        expected = (root / 'producto/frontend/dist/index.html').read_bytes()
        with urllib.request.urlopen('http://127.0.0.1:5173/', timeout=5) as response:
            if response.read() != expected:
                raise RuntimeError('La interfaz abierta no corresponde a esta instalación.')
    verified = dict(child)
    verified['verificacion_reutilizacion'] = current
    return verified


def comprobar_http():
    for url in ('http://127.0.0.1:8000/salud', 'http://127.0.0.1:5173/hoy'):
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError('Un servicio no confirmó disponibilidad.')
    with urllib.request.urlopen('http://127.0.0.1:8000/api/local/estado', timeout=5) as response:
        if json.load(response)['bd']['deshabilitada']:
            raise RuntimeError('El backend no confirmó acceso a la base local.')


def asegurar_postgres(root, diario, params, run, pg):
    """Recupera la dependencia local sin detener servicios ya acreditados.

    El llamador conserva el lock diario. El recibo queda fuera del producto;
    un fallo nunca autoriza detener procesos cuya identidad no se acreditó.
    """
    if params.get('host') != '127.0.0.1' or params.get('port') != '55433' or params.get('hostaddr'):
        raise ValueError('La recuperación exige PostgreSQL local 127.0.0.1:55433.')
    if diario.ocupado(55433):
        return diario.acreditar_pg(params, run)
    folder = root / 'runtime' / ('recuperacion_pg_' + uuid.uuid4().hex)
    folder.mkdir()
    receipt = folder / 'POSTGRES.json'
    record = dict(paquete=str(root), estado='INICIANDO_POSTGRES', base=params['dbname'])
    diario.operador.atomico(receipt, record)
    try:
        diario.ctl(pg, run, 'start', record, receipt)
        postgres = diario.acreditar_pg(params, run)
    except BaseException:
        record['estado'] = 'FALLO_RECUPERACION_POSTGRES'
        diario.operador.atomico(receipt, record)
        raise
    record.update(estado='POSTGRES_VERIFICADO', postgres=postgres)
    diario.operador.atomico(receipt, record)
    return postgres


def abrir(root, *, sin_abrir=False, espera=90):
    root = root.resolve()
    spec = importlib.util.spec_from_file_location('acceso_diario_instalado', root / 'producto/scripts/abrir_instalacion_local.py')
    diario = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diario)
    operator = diario.operador
    params, run, pg = diario.parametros(root)
    pointer = root / 'runtime/PROCESOS_ACTUALES.json'
    services = root / 'runtime/SERVICIOS_LOCALES.json'
    commands = comandos(root)
    with diario.exclusividad(root):
        old = json.loads(pointer.read_text(encoding='utf-8')) if pointer.exists() else None
        existing = [verificar_existente(root, old, name, port, commands[name])
                    for name, port in (('backend', 8000), ('frontend', 5173))]
        existing = [child for child in existing if child is not None]
        if existing:
            postgres = asegurar_postgres(root, diario, params, run, pg)
            missing = [name for name in commands if name not in {c['nombre'] for c in existing}]
            if missing:
                folder = root / 'runtime' / ('recuperacion_' + uuid.uuid4().hex)
                folder.mkdir()
                record_path = folder / 'PROCESOS.json'
                record = dict(paquete=str(root), registro=str(record_path),
                              creado_utc=datetime.now(timezone.utc).isoformat(),
                              estado='RECUPERANDO', hijos=[], reutilizados=existing)
                # Conservar el registro anterior antes de publicar otro puntero.
                operator.atomico(folder / 'PROCESOS_ANTERIORES.json', old)
                operator.atomico(record_path, record)
                children = []
                environment = os.environ.copy()
                environment.pop('ANALYTICSPREDICT_SOLO_BASE_LOCAL', None)
                environment.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
                try:
                    for name in missing:
                        log = folder / (name + '.log')
                        with log.open('xb') as stream:
                            child = subprocess.Popen(commands[name], cwd=root, env=environment,
                                stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
                        children.append(child)
                        identity = operator.identidad_pid(child.pid)
                        record['hijos'].append(dict(nombre=name, pid=child.pid, identidad=identity,
                            log=str(log), comando_sha256=hashlib.sha256(json.dumps(commands[name]).encode()).hexdigest()))
                        operator.atomico(record_path, record)
                        operator.atomico(pointer, record)
                        if identity is None:
                            raise RuntimeError('No se pudo acreditar la identidad del proceso recién creado.')
                    operator.esperar(SimpleNamespace(children=children),
                        ['http://127.0.0.1:8000/salud', 'http://127.0.0.1:5173/hoy'], espera)
                    comprobar_http()
                except BaseException:
                    # Solo detener hijos creados por esta llamada, nunca los reutilizados.
                    for child in children:
                        if child.poll() is None:
                            child.terminate()
                            child.wait(timeout=15)
                    record['estado'] = 'FALLO_RECUPERACION'
                    operator.atomico(record_path, record)
                    operator.atomico(pointer, old)
                    raise
                record['hijos'].extend(existing)
                record['estado'] = 'DISPONIBLE'
                operator.atomico(record_path, record)
                operator.atomico(pointer, record)
                print('Servicios recuperados: ' + ', '.join(missing) + '.', flush=True)
            else:
                comprobar_http()
                print('Analytics Predict ya estaba encendido; se reutiliza la instalación.', flush=True)
            operator.atomico(services, dict(paquete=str(root), estado='DISPONIBLE',
                base=params['dbname'], postgres=postgres, registro_api=str(pointer),
                actualizado_utc=datetime.now(timezone.utc).isoformat()))
        else:
            # El lanzador original mantiene el control del arranque completo y PostgreSQL.
            pass
    if not existing:
        diario.ejecutar(root, sin_abrir=True, espera=espera)
    if not sin_abrir:
        webbrowser.open('http://127.0.0.1:5173/hoy')
    print('Analytics Predict disponible: http://127.0.0.1:5173/hoy', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paquete', type=Path, required=True)
    parser.add_argument('--sin-abrir', action='store_true')
    parser.add_argument('--espera-api', type=int, default=90, choices=range(1, 181))
    args = parser.parse_args()
    abrir(args.paquete, sin_abrir=args.sin_abrir, espera=args.espera_api)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Evitar imprimir parámetros de conexión o secretos de una excepción SQL.
        message = str(exc) if isinstance(exc, (RuntimeError, ValueError)) else type(exc).__name__
        print('No se pudo completar el arranque: ' + message, flush=True)
        sys.exit(1)
