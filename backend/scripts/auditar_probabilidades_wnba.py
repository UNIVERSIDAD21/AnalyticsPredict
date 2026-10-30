"""Auditoría offline explícita de la cohorte original, sin fit ni activación."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motor.auditoria_probabilidades_wnba import auditar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--publicacion', type=Path, required=True)
    p.add_argument('--salida', type=Path, required=True)
    args = p.parse_args()
    origen, destino = args.publicacion.resolve(), args.salida.resolve()
    repo = Path(__file__).resolve().parents[2]
    if destino.is_relative_to(repo) or destino.is_relative_to(origen.parent):
        p.error('La salida debe estar fuera del repositorio y del directorio de publicación')
    if destino.exists(): p.error('No se sobrescriben recibos')
    datos = origen.read_bytes()
    r = auditar(json.loads(datos.decode('utf-8')))
    r['archivo_publicacion_sha256'] = hashlib.sha256(datos).hexdigest()
    if origen.read_bytes() != datos: raise RuntimeError('El origen cambió durante la auditoría')
    with destino.open('x', encoding='utf-8') as f: json.dump(r, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({'analizados': r['analizados'], 'abstenciones': r['abstenciones'],
                      'max_delta_proyeccion': r['max_delta_proyeccion'], 'activado': False}))


if __name__ == '__main__': main()
