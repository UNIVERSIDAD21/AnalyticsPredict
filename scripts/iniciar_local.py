"""Inicio local no destructivo. Por defecto solo artefactos, sin conexión a BD.

Ejecutar con el Python de backend/.venv. Requiere frontend/dist ya compilado.
No instala dependencias, construye modelos, sincroniza fuentes ni libera puertos.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from urllib.request import urlopen
import webbrowser

RAIZ = Path(__file__).resolve().parents[1]


def cerrar_backend(backend):
    """Solo el Popen creado aquí; NT puede tener un redirector de la venv."""
    if backend is None or backend.poll() is not None:
        return
    if os.name == 'nt':
        # Terminar únicamente el redirector deja el Python real y sus handles
        # abiertos. /T se limita al árbol del PID que acabamos de crear.
        subprocess.run(['taskkill', '/PID', str(backend.pid), '/T', '/F'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    else:
        backend.terminate()
    try:
        backend.wait(timeout=5)
    except subprocess.TimeoutExpired:
        backend.kill(); backend.wait(timeout=5)


def comprobar_puertos(puertos):
    for puerto in puertos:
        with socket.socket() as s:
            try:
                s.bind(('127.0.0.1', puerto))
            except OSError as exc:
                raise ValueError(f'Puerto {puerto} ocupado o no disponible. No se detuvo ningún proceso.') from exc


class Interfaz(SimpleHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlsplit
        path = urlsplit(self.path).path
        # Fallback SPA únicamente para rutas sin extensión, no para assets rotos.
        if not Path(self.translate_path(path)).is_file() and '.' not in path.rsplit('/', 1)[-1]:
            self.path = '/index.html'
        super().do_GET()

    def log_message(self, *args):
        pass


def preparar_entorno(estado, con_bd):
    env = os.environ.copy()
    env.update({'PYTHONIOENCODING': 'utf-8', 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'ENTORNO': 'desarrollo'})
    if con_bd:
        # La migración se verifica aparte. Un host remoto no es una BD local.
        from dotenv import dotenv_values
        from psycopg.conninfo import conninfo_to_dict
        config = dotenv_values(RAIZ / 'backend/.env')
        url = config.get('DATABASE_URL')
        if not url or conninfo_to_dict(url).get('host') not in ('127.0.0.1', 'localhost', '::1'):
            raise ValueError('La configuración no acredita PostgreSQL local. Completa la restauración verificada antes de usar --con-bd.')
        env['DATABASE_URL'] = url
        env.pop('ANALYTICSPREDICT_SOLO_BASE_LOCAL', None)
    else:
        env['ANALYTICSPREDICT_SOLO_BASE_LOCAL'] = '1'
    if estado:
        estado = estado.expanduser().resolve()
        for nombre, variable in (('modelo_nba_activo.npz', 'ANALYTICSPREDICT_MODELO_NBA_ACTIVO'),
                                 ('euroliga/activo.json', 'ANALYTICSPREDICT_MODELO_EUROLIGA_ACTIVO'),
                                 ('wnba/activo.json', 'ANALYTICSPREDICT_MODELO_WNBA_ACTIVO')):
            path = estado / nombre
            if path.is_file():
                env[variable] = str(path)
        if not (estado / 'modelo_nba_activo.npz').is_file():
            raise ValueError('No se encontró el artefacto NBA en --estado. No se intentará entrenar.')
    return env


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--estado', type=Path, help='Directorio local de artefactos existentes, sin credenciales')
    parser.add_argument('--con-bd', action='store_true', help='Solo tras restaurar y verificar PostgreSQL local')
    parser.add_argument('--sin-abrir', action='store_true')
    parser.add_argument('--comprobar', action='store_true', help='Verifica el arranque y cierra solo sus propios procesos')
    args = parser.parse_args(argv)
    if not (RAIZ / 'frontend/dist/index.html').is_file():
        raise ValueError('Falta frontend/dist: ejecuta npm ci y npm run build en frontend antes de iniciar.')
    env = preparar_entorno(args.estado, args.con_bd)
    comprobar_puertos((8000, 5173))
    servidor = ThreadingHTTPServer(('127.0.0.1', 5173), partial(Interfaz, directory=str(RAIZ / 'frontend/dist')))
    servidor.daemon_threads = True
    backend = None
    try:
        backend = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8000'],
            cwd=RAIZ / 'backend', env=env, stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        for _ in range(60):
            if backend.poll() is not None:
                raise ValueError('La API no pudo iniciar. No se abrió la interfaz.')
            try:
                with urlopen('http://127.0.0.1:8000/salud', timeout=.5) as r:
                    if r.status == 200:
                        break
            except OSError:
                time.sleep(.25)
        else:
            raise ValueError('La API no confirmó disponibilidad. Solo se detendrá el proceso iniciado aquí.')
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        ruta = '/hoy' if args.con_bd else '/base-local'
        url = 'http://127.0.0.1:5173' + ruta
        print('Abre ' + url + ' · Ctrl+C cierra solo esta ejecución.', flush=True)
        if not args.con_bd:
            print('Modo base local: BD y sincronización deshabilitadas. No acredita migración terminada.', flush=True)
        if not args.sin_abrir and not args.comprobar:
            webbrowser.open(url)
        if not args.comprobar:
            backend.wait()
    except KeyboardInterrupt:
        pass
    finally:
        # Los procesos ajenos nunca se enumeran, matan ni reutilizan.
        cerrar_backend(backend)
        # shutdown requiere que serve_forever esté en curso.
        if backend is not None and 'ruta' in locals():
            servidor.shutdown()
        servidor.server_close()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print('No se inició: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
