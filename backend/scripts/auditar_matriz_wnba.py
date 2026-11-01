#!/usr/bin/env python3
"""Audita todas las parejas por temporada WNBA desde el snapshot local, sin red ni BD."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motor.wnba import BOGOTA, huella
from servicios.predictor_wnba import cargar, escribir
from calidad.auditoria_wnba import auditar


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corte', default=datetime.now(BOGOTA).date().isoformat())
    p.add_argument('--salida', required=True, type=Path)
    args = p.parse_args(argv)
    if args.salida.exists():
        p.error('La salida debe ser un archivo nuevo; no se sobrescriben auditorías')
    m = cargar()
    antes = huella(m)
    reporte = auditar(m['datos'], corte=args.corte, progreso=lambda x: print(json.dumps(x, ensure_ascii=False), file=sys.stderr, flush=True))
    if huella(cargar()) != antes:
        raise RuntimeError('La publicación cambió durante la auditoría; repetir con snapshot estable')
    reporte.update(publicacion=m['version'], fuente='SNAPSHOT_LOCAL', observado_utc=datetime.now(timezone.utc).isoformat())
    escribir(args.salida, reporte)
    print(json.dumps({'estado':reporte['estado'], 'casos':reporte['casos_con_soporte'], 'fallos':len(reporte['fallos']), 'reporte':str(args.salida)}, ensure_ascii=False))
    return 0 if reporte['estado'] == 'VERIFICADO' else 1


if __name__ == '__main__':
    raise SystemExit(main())
