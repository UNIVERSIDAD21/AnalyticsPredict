#!/usr/bin/env python3
"""Descarga independiente de Colombia a CSV/JSONL; no carga la BD."""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from scrapers.futbol_latam.cli import main as ejecutar_cli


def main(argv=None):
    return ejecutar_cli("colombia", argv)


if __name__ == "__main__":
    raise SystemExit(main())
