#!/usr/bin/env python3
"""Audita pendientes y outcomes históricos; solo SELECT, nunca repara registros."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from servicios.resolucion_analitica import procesar


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', required=True, type=Path)
    parser.add_argument('--limite', default=1000, type=int)
    args = parser.parse_args(argv)
    if args.salida.exists():
        parser.error('La salida debe ser nueva; no sobrescribir evidencia')
    raiz = Path(__file__).resolve().parents[2]
    if args.salida.resolve().is_relative_to(raiz):
        parser.error('Guardar evidencia fuera del repositorio del producto')
    reporte = procesar(simular=True, limite=args.limite, auditar_finalizadas=True)
    with args.salida.open('x', encoding='utf-8') as archivo:
        args.salida.chmod(0o600)
        json.dump(reporte, archivo, ensure_ascii=False, indent=2)
    print(json.dumps({k:v for k,v in reporte.items() if k != 'detalles'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
