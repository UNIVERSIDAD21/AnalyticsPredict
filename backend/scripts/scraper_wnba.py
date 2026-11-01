#!/usr/bin/env python3
"""Scraper ESPN WNBA. Por defecto muestra el plan: no red, no BD, no modelos."""
from __future__ import annotations

import argparse
import json
import signal
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfoNotFoundError

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scrapers.wnba import VERSION
from scrapers.wnba.archivo import Archivo, ArchivoError, bloqueo
from scrapers.wnba.cliente import ClienteESPN
from scrapers.wnba.pipeline import ejecutar, plan


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=f"WNBA {VERSION}")
    p.add_argument("--desde", required=True, type=date.fromisoformat, help="Primer día local, YYYY-MM-DD (2006+)")
    p.add_argument("--hasta", required=True, type=date.fromisoformat, help="Último día local inclusivo")
    p.add_argument("--zona", default="America/Bogota", help="Zona IANA para delimitar días; exporta también UTC y Colombia")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--fetch", action="store_true", help="Ejecutar extracción HTTP explícita a archivos; NO carga BD")
    mode.add_argument("--offline", action="store_true", help="Reprocesar solo respuestas archivadas, aunque estén antiguas")
    p.add_argument("--salida", type=Path, help="Directorio persistente de caché/evidencias FUERA del repositorio")
    p.add_argument("--estadisticas", action="store_true", help="Consultar boxscore de ambos equipos en cada final")
    p.add_argument("--refresh", action="store_true", help="Nueva observación HTTP sin borrar los raws anteriores")
    p.add_argument("--intervalo", type=float, default=1.5, help="Segundos entre inicios HTTP, mínimo 1.25")
    p.add_argument("--max-requests", type=int, default=1000, help="Presupuesto total incluyendo reintentos")
    p.add_argument("--intentos-http", type=int, default=5, help="Intentos por consulta transitoria, 1..8")
    p.add_argument("--rondas", type=int, default=3, help="Pasadas para recuperar consultas transitorias, 1..10")
    p.add_argument("--espera-rondas", type=float, default=15, help="Segundos entre pasadas, 0..60")
    p.add_argument("--checkpoint-cada", type=int, default=25, help="Exportar avance cada N operaciones (también cada 60 s)")
    return p


@contextmanager
def guardar_al_terminar():
    """SIGTERM recibe el mismo guardado ordenado que Ctrl+C; SIGKILL usa los raws."""
    def terminar(signum, frame):
        raise KeyboardInterrupt
    anterior = signal.signal(signal.SIGTERM, terminar)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, anterior)


def main(argv=None) -> int:
    p = parser()
    args = p.parse_args(argv)
    try:
        planned = plan(args.desde, args.hasta, args.zona)
        if args.refresh and not args.fetch:
            p.error("--refresh requiere --fetch")
        if not args.fetch and not args.offline:
            print(json.dumps({"modo": "PLAN_SIN_RED", **planned}, ensure_ascii=False, indent=2))
            return 0
        if args.salida is None:
            p.error("--fetch/--offline requieren --salida fuera del repositorio")
        root = args.salida.expanduser().resolve()
        if root == REPO or REPO in root.parents:
            p.error("Los datos/evidencias deben permanecer fuera del repositorio del producto")
        with bloqueo(root), guardar_al_terminar():
            client = ClienteESPN(Archivo(root), offline=args.offline, refresh=args.refresh,
                                 intervalo=args.intervalo, max_requests=args.max_requests,
                                 intentos=args.intentos_http)
            try:
                run, report, code = ejecutar(client, desde=args.desde, hasta=args.hasta, zona=args.zona,
                                            con_estadisticas=args.estadisticas,
                                            rondas=args.rondas, espera_rondas=args.espera_rondas,
                                            checkpoint_cada=args.checkpoint_cada,
                                            progreso=lambda v: print(json.dumps(v), file=sys.stderr, flush=True))
            finally:
                client.close()
        print(json.dumps({"estado": report["estado"], "partidos": report["partidos_exportados"],
                          "cuarentena": report["incidencias_cuarentena"], "reporte": str(run / "reporte.json"),
                          "pendientes": report["consultas_pendientes"],
                          "ventanas_pendientes": len(report["ventanas_pendientes"]),
                          "recorrido_completo": report["recorrido_completo"],
                          "resultados_pendientes": report["resultados_pendientes"],
                          "partidos_con_advertencias_estadisticas": report["partidos_con_advertencias_estadisticas"],
                          "campos_estadisticos_apartados": report["campos_estadisticos_apartados"],
                          "pendientes_reintentables": report["consultas_pendientes_reintentables"],
                          "error": report["error"], "exit_code": code}, ensure_ascii=False, indent=2))
        return code
    except (ValueError, ZoneInfoNotFoundError, ArchivoError, OSError) as exc:
        print(f"WNBA: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
