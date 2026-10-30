"""Sirve únicamente el frontend compilado en loopback, sin Node ni acceso a BD."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class Interfaz(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if not Path(self.translate_path(path)).is_file() and '.' not in path.rsplit('/', 1)[-1]: self.path = '/index.html'
        super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directorio', type=Path, required=True)
    parser.add_argument('--puerto', type=int, default=5173)
    args = parser.parse_args()
    if not (args.directorio / 'index.html').is_file() or not 1 <= args.puerto <= 65535: raise ValueError('Frontend o puerto no disponible')
    with ThreadingHTTPServer(('127.0.0.1', args.puerto), partial(Interfaz, directory=str(args.directorio.resolve()))) as server:
        server.daemon_threads = True
        try: server.serve_forever()
        except KeyboardInterrupt: pass


if __name__ == '__main__': main()
