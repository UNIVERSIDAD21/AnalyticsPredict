"""Verifica evidencia cruda y completa mitades de goles de vínculos ya acreditados.

Por defecto solo SELECT. No instala tablas, ingiere calendarios ni entrena.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import obtener_pool, cerrar_pool
from servicios.tiempos_espn_futbol import interpretar_tiempos, construir_plan, aplicar_observaciones


def cargar_evidencia(conn, archivo, directorio):
    lote = json.loads(archivo.read_text())
    if lote.get('rechazadas') or len(lote['validas']) != lote['n_cohorte']:
        raise ValueError('No aplicar un lote incompleto sin reconciliación explícita')
    observaciones = []
    for obs in lote['validas']:
        ruta = directorio / f"{obs['id_fuente']}.json"
        ev = conn.execute('SELECT evidencia FROM partidos_fuente_espn_futbol WHERE liga=%s AND id_fuente=%s',
                          (obs['liga'], obs['id_fuente'])).fetchone()
        if ev is None:
            raise ValueError('Evento no vinculado')
        interpretada = interpretar_tiempos(json.loads(ruta.read_text()), ev[0])
        if any(interpretada[k] != obs.get(k) for k in interpretada):
            raise ValueError('La evidencia cruda no acredita los valores del lote')
        observaciones.append(obs)
    return observaciones


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archivo', type=Path, required=True)
    parser.add_argument('--summaries', type=Path, required=True)
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args(argv)
    try:
        with obtener_pool().connection() as conn:
            conn.execute("SET LOCAL statement_timeout='30s'")
            if not args.aplicar:
                conn.execute('SET TRANSACTION READ ONLY')
            observaciones = cargar_evidencia(conn, args.archivo, args.summaries)
            if args.aplicar:
                salida = aplicar_observaciones(conn, observaciones)
            else:
                plan = construir_plan(conn, observaciones)
                salida = {'modo': 'SOLO_LECTURA', 'eventos_verificados': len(plan),
                          'partidos_a_completar': sum(x['cambia'] for x in plan)}
        print(json.dumps(salida))
        return 0
    finally:
        cerrar_pool()


if __name__ == '__main__':
    raise SystemExit(main())
