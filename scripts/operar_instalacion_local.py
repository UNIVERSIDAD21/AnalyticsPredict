"""Arranque verificable de API/web, registro inmediato y cierre solo de hijos propios."""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid


def atomico(path: Path, value):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


def identidad_pid(pid: int):
    if os.name != 'nt':
        try:
            return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
        except (OSError, IndexError):
            return None
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4))
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        values = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *[ctypes.byref(v) for v in values]):
            return None
        return str((values[0].dwHighDateTime << 32) | values[0].dwLowDateTime)
    finally:
        kernel.CloseHandle(handle)


class Registro:
    def __init__(self, paquete: Path):
        self.paquete = paquete.resolve()
        runtime = self.paquete / 'runtime'
        runtime.mkdir(exist_ok=True)
        self.pointer = runtime / 'PROCESOS_ACTUALES.json'
        if self.pointer.exists():
            old = json.loads(self.pointer.read_text(encoding='utf-8'))
            if any(c.get('identidad') and identidad_pid(c['pid']) == c['identidad'] for c in old.get('hijos', [])):
                raise ValueError('Hay una operación propia activa; reanudarla o detenerla antes de duplicar')
        self.folder = runtime / ('operacion_' + uuid.uuid4().hex)
        self.folder.mkdir()
        self.path = self.folder / 'PROCESOS.json'
        self.value = dict(paquete=str(self.paquete), registro=str(self.path),
                          creado_utc=datetime.now(timezone.utc).isoformat(), estado='INICIANDO', hijos=[])
        self.children: list[subprocess.Popen] = []
        self.save()

    def save(self):
        atomico(self.path, self.value)
        atomico(self.pointer, self.value)

    def spawn(self, name: str, command: list[str], *, cwd=None, env=None):
        options = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else dict(start_new_session=True)
        log = self.folder / (name + '.log')
        with log.open('xb') as stream:
            child = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                                     stderr=subprocess.STDOUT, **options)
        self.children.append(child)
        self.value['hijos'].append(dict(nombre=name, pid=child.pid, identidad=identidad_pid(child.pid),
            log=str(log), comando_sha256=hashlib.sha256(json.dumps(command).encode()).hexdigest()))
        try:
            self.save()  # Antes de crear el siguiente hijo o esperar a HTTP.
        except Exception:
            self.stop()
            raise
        return child

    def stop(self):
        stop_owned(self.value)
        for child in self.children:
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                raise RuntimeError('Un hijo propio no confirmó cierre; conservar registro y revisar')
        self.value['estado'] = 'DETENIDO'
        self.save()


def stop_owned(record):
    for child in reversed(record.get('hijos', [])):
        if not child.get('identidad') or identidad_pid(child['pid']) != child['identidad']:
            continue  # PID terminado o reutilizado: jamás cerrar otro proceso.
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(child['pid']), '/T', '/F'], capture_output=True)
        else:
            try:
                os.killpg(child['pid'], signal.SIGTERM)
            except ProcessLookupError:
                pass


def esperar(registro: Registro, urls: list[str], seconds=90):
    if not 1 <= seconds <= 180:
        raise ValueError('Espera fuera del intervalo de 1 a 180 segundos')
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(child.poll() is not None for child in registro.children):
            raise RuntimeError('Un proceso propio terminó antes de estar disponible; revisar su log privado')
        ready = True
        for url in urls:
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    ready = ready and response.status == 200
            except (OSError, urllib.error.URLError):
                ready = False
        if ready:
            return
        time.sleep(min(.5, max(0, deadline-time.monotonic())))
    raise TimeoutError('El arranque no confirmó disponibilidad dentro del plazo monotónico')


def iniciar(paquete: Path, espera=90, comprobar=False):
    raiz = paquete.resolve()
    if not (raiz / 'producto/backend/.env').is_file():
        raise ValueError('Falta restauración local verificada; no se arranca con configuración remota')
    for port in (8000, 5173):
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                raise ValueError('Puerto ocupado: no se detiene un proceso existente')
    registro = Registro(raiz)
    python = str(raiz / 'runtime/python/python.exe')
    scripts = raiz / 'producto/scripts'
    try:
        registro.spawn('backend', [python, '-X', 'utf8', '-B', str(scripts/'ejecutar_herramienta_local.py'),
            '--paquete', str(raiz), 'arrancar_backend.py', '--puerto', '8000'])
        registro.spawn('frontend', [python, '-X', 'utf8', '-B', str(scripts/'servir_frontend_local.py'),
            '--directorio', str(raiz/'producto/frontend/dist'), '--puerto', '5173'])
        esperar(registro, ['http://127.0.0.1:8000/salud','http://127.0.0.1:5173/'], espera)
        if comprobar:
            result = subprocess.run([python, '-X', 'utf8', '-B', str(scripts/'ejecutar_herramienta_local.py'),
                '--paquete', str(raiz), 'verificar_windows.py'], capture_output=True, timeout=180)
            if result.returncode:
                raise RuntimeError('La comprobación local no terminó; conservar sus recibos/logs privados')
            registro.stop()
        else:
            registro.value['estado'] = 'DISPONIBLE'
            registro.save()
        return registro.value
    except BaseException:
        registro.stop()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paquete', type=Path, required=True)
    parser.add_argument('--espera-api', type=int, default=90)
    parser.add_argument('--comprobar', action='store_true')
    parser.add_argument('--detener', action='store_true')
    args = parser.parse_args()
    if args.detener:
        root = args.paquete.resolve()
        path = root / 'runtime/PROCESOS_ACTUALES.json'
        value = json.loads(path.read_text(encoding='utf-8'))
        if Path(value['paquete']).resolve() != root:
            raise ValueError('Registro ajeno a esta instalación')
        stop_owned(value)
        value['estado'] = 'CIERRE_SOLICITADO'
        atomico(path, value)
        atomico(Path(value['registro']), value)
        result = value
    else:
        result = iniciar(args.paquete,args.espera_api,args.comprobar)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps(dict(ok=False,error_type=type(exc).__name__,
                              reason='Operación incompleta: revisar registros propios, no repetir sin conciliarlos')))
        raise SystemExit(1)
