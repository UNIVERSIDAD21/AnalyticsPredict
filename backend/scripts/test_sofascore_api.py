#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para validar acceso a la API de Sofascore.

Ejemplo:
    python backend/scripts/test_sofascore_api.py --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.sofascore.cliente import SofascoreClient
from scrapers.sofascore.monitoreo import configurar_logging


ENDPOINTS_PRUEBA = (
    "/unique-tournament/8",
    "/unique-tournament/17",
    "/unique-tournament/35",
)


def parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida el acceso a endpoints críticos de Sofascore",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Habilita logging DEBUG para ver headers/cookies",
    )
    return parser.parse_args()


def main() -> int:
    args = parsear_argumentos()
    configurar_logging(nivel=logging.DEBUG if args.verbose else logging.INFO)

    errores = []
    with SofascoreClient() as cliente:
        for endpoint in ENDPOINTS_PRUEBA:
            try:
                data = cliente.get(endpoint)
                if not data:
                    errores.append(f"{endpoint}: respuesta vacía")
                    logging.error("Endpoint %s sin datos válidos.", endpoint)
                else:
                    logging.info("Endpoint %s OK.", endpoint)
            except Exception as exc:
                errores.append(f"{endpoint}: {exc}")
                logging.error("Endpoint %s falló: %s", endpoint, exc)

    if errores:
        logging.error("Errores detectados:\n- %s", "\n- ".join(errores))
        return 1

    logging.info("Todos los endpoints respondieron correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
