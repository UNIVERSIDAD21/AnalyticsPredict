"""Ejecuta una herramienta verificada del paquete sin relajar Python ._pth."""
from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys

HERRAMIENTAS = ('exportar_vigente.py', 'restaurar_local.py', 'verificar_windows.py',
                'verificar_bd.py', 'arrancar_backend.py')


def ejecutar(paquete: Path, herramienta: str, argumentos: list[str]):
    if herramienta not in HERRAMIENTAS:
        raise ValueError('Herramienta no permitida')
    raiz = paquete.resolve()
    directorio = raiz / 'herramientas'
    target = directorio / herramienta
    if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(raiz):
        raise ValueError('Herramienta ausente o fuera del paquete')
    # Python embebido ignora el directorio del script; solo se añade esta ruta confiable.
    sys.path.insert(0, str(directorio))
    sys.argv = [str(target), *argumentos]
    runpy.run_path(str(target), run_name='__main__')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paquete', type=Path, required=True)
    parser.add_argument('herramienta', choices=HERRAMIENTAS)
    parser.add_argument('argumentos', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    ejecutar(args.paquete, args.herramienta, args.argumentos)


if __name__ == '__main__':
    main()
