"""Captura/resuelve Q1 NBA de forma explícita. Por defecto solo lista el feed.

No instala tablas, no entrena, no registra apuestas ni toca predicciones legacy.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg

from motor_autoentrenamiento.artefacto_nba import ruta_artefacto
from scripts.actualizar_partidos_nba import request_json, ESPN_SCOREBOARD, db_url
from servicios.prospectiva_nba import congelar, resolver


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fecha', type=date.fromisoformat, required=True, help='Día del scoreboard ESPN')
    p.add_argument('--evento', help='ID exacto del evento; no selección automática')
    p.add_argument('--linea', type=float, default=55.5, help='Umbral técnico Q1 predeclarado, no cuota/línea real')
    p.add_argument('--congelar', action='store_true')
    p.add_argument('--resolver', metavar='PREDICCION_UUID')
    args = p.parse_args()
    if args.congelar and args.resolver or (args.congelar or args.resolver) and not args.evento:
        p.error('Elegir una operación y un ID exacto de evento')
    feed = request_json(ESPN_SCOREBOARD, {'dates': args.fecha.strftime('%Y%m%d'), 'limit': 100}, retries=2)
    ligas = feed.get('leagues', [])
    if len(ligas) != 1 or ligas[0].get('slug') != 'nba':
        raise ValueError('Feed fuera del dominio NBA')
    eventos = feed.get('events', [])
    if not args.congelar and not args.resolver:
        print(json.dumps([{'id': e['id'], 'inicio': e['date'], 'nombre': e['name'],
                           'estado': e['status']['type']['name']} for e in eventos], ensure_ascii=False))
        return
    elegidos = [e for e in eventos if str(e['id']) == args.evento]
    if len(elegidos) != 1:
        raise ValueError('Evento ausente o ambiguo en el feed NBA de esa fecha')
    with psycopg.connect(db_url(), connect_timeout=8) as conn:
        conn.execute("SET LOCAL statement_timeout='15s'")
        resultado = congelar(conn, elegidos[0], ruta_artefacto(), args.linea) if args.congelar else resolver(conn, args.resolver, elegidos[0])
    print(json.dumps(resultado))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Seguimiento detenido: '+type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
