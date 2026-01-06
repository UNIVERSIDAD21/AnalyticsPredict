#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script CLI para sincronizar partidos recientes de forma incremental.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion import SyncConfig, formatear_resumen, sync_partidos_recientes


def construir_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sincroniza partidos recientes desde ESPN")
    parser.add_argument("--days", type=int, default=7, help="Ventana de días a revisar")
    parser.add_argument("--force", action="store_true", help="Ignorar cursor y recalcular ventana")
    parser.add_argument("--dry-run", action="store_true", help="No escribe en BD, solo muestra resumen")
    parser.add_argument("--source", type=str, default="espn", help="Fuente de datos (default: espn)")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = construir_argumentos()

    cfg = SyncConfig(
        days=args.days,
        force=args.force,
        dry_run=args.dry_run,
        source=args.source,
    )

    try:
        resultado = sync_partidos_recientes(cfg)
        print(formatear_resumen(resultado))
        return 0 if resultado.errores == 0 else 1
    except Exception as exc:
        print(f"❌ Error ejecutando sync: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
