#!/usr/bin/env python3
"""ESPN MLS -> CSV/JSONL: goles, córners y tiros. Sin BD ni modelos."""
from __future__ import annotations

import argparse
import json
import re
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
from scrapers.mls import VERSION
from scrapers.mls.archivo import Archivo, ArchivoError, bloqueo
from scrapers.mls.cliente import ClienteESPN, url_consulta
from scrapers.mls.pipeline import ejecutar, plan


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=f"MLS {VERSION}")
    p.add_argument("--desde", required=True, type=date.fromisoformat)
    p.add_argument("--hasta", required=True, type=date.fromisoformat)
    p.add_argument("--zona", default="America/Bogota")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--fetch", action="store_true", help="Descargar a archivos; no escribe BD")
    mode.add_argument(
        "--offline", action="store_true", help="Reconstruir solo desde el archivo existente"
    )
    p.add_argument("--salida", type=Path, help="Directorio persistente fuera del repositorio")
    stats = p.add_mutually_exclusive_group()
    stats.add_argument(
        "--estadisticas",
        dest="estadisticas",
        action="store_true",
        default=True,
        help="Incluidas por defecto",
    )
    stats.add_argument(
        "--solo-resultados",
        dest="estadisticas",
        action="store_false",
        help="No solicitar detalles estadísticos",
    )
    p.add_argument("--refresh", action="store_true", help="Observar de nuevo todas las consultas")
    p.add_argument(
        "--reintentar-pendientes",
        action="store_true",
        help="Refrescar solo consultas del último pendientes.jsonl",
    )
    p.add_argument(
        "--intervalo", type=float, default=2.5, help="Segundos entre inicios HTTP; mínimo 1.25"
    )
    p.add_argument(
        "--max-requests",
        type=int,
        default=1000,
        help="Presupuesto global, 1..20000, incluye reintentos",
    )
    p.add_argument(
        "--intentos-http", type=int, default=5, help="Intentos por consulta transitoria, 1..8"
    )
    p.add_argument(
        "--rondas", type=int, default=3, help="Pasadas para consultas transitorias, 1..10"
    )
    p.add_argument(
        "--espera-rondas", type=float, default=15, help="Espera entre pasadas, 0..60 segundos"
    )
    p.add_argument(
        "--checkpoint-cada",
        type=int,
        default=25,
        help="Exportar cada N operaciones y tras 60 segundos",
    )
    return p


@contextmanager
def guardar_al_terminar():
    def terminar(signum, frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, terminar)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def pendientes_previos(root):
    pointer = root / "ultima_ejecucion.json"
    if not pointer.exists():
        return set()
    try:
        name = json.loads(pointer.read_text())["ejecucion"]
        if not isinstance(name, str) or not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{12}", name):
            raise ValueError("Ruta inválida")
        items = [
            json.loads(x)
            for x in (root / "ejecuciones" / name / "pendientes.jsonl").read_text().splitlines()
        ]
        urls = set()
        for item in items:
            expected = url_consulta(item["endpoint"], item["parametro"])
            if item["url"] != expected:
                raise ValueError("URL alterada")
            urls.add(expected)
        return urls
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise ArchivoError("No se pueden leer los pendientes anteriores") from exc


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    try:
        planned = plan(args.desde, args.hasta, args.zona)
        if (args.refresh or args.reintentar_pendientes) and not args.fetch:
            p.error("--refresh/--reintentar-pendientes requieren --fetch")
        if not args.fetch and not args.offline:
            print(json.dumps({"modo": "PLAN_SIN_RED", **planned}, ensure_ascii=False, indent=2))
            return 0
        if args.salida is None:
            p.error("--fetch/--offline requieren --salida")
        root = args.salida.expanduser().resolve()
        if root == REPO or REPO in root.parents:
            p.error("La salida debe estar fuera del repositorio")
        with bloqueo(root), guardar_al_terminar():
            client = ClienteESPN(
                Archivo(root),
                offline=args.offline,
                refresh=args.refresh,
                intervalo=args.intervalo,
                max_requests=args.max_requests,
                intentos=args.intentos_http,
            )
            try:
                if args.reintentar_pendientes:
                    client.refrescar_urls = pendientes_previos(root)
                run, report, code = ejecutar(
                    client,
                    desde=args.desde,
                    hasta=args.hasta,
                    zona=args.zona,
                    con_estadisticas=args.estadisticas,
                    rondas=args.rondas,
                    espera_rondas=args.espera_rondas,
                    checkpoint_cada=args.checkpoint_cada,
                    progreso=lambda x: print(
                        json.dumps(x, ensure_ascii=False), file=sys.stderr, flush=True
                    ),
                )
            finally:
                client.close()
        keys = (
            "estado",
            "partidos_exportados",
            "finales_completos",
            "finales_con_estadisticas_completas",
            "no_finales",
            "recorrido_completo",
            "consultas_pendientes",
            "resultados_pendientes",
            "incidencias_cuarentena",
            "error",
            "exit_code",
        )
        print(
            json.dumps(
                {
                    **{k: report[k] for k in keys},
                    "csv": str(run / "partidos.csv"),
                    "csv_completos": str(run / "partidos_completos.csv"),
                    "reporte": str(run / "reporte.json"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return code
    except (ValueError, ZoneInfoNotFoundError, ArchivoError, OSError) as exc:
        print(f"MLS: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
