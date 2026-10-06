#!/usr/bin/env python3
"""Convierte un corte analítico JSON de solo lectura en scorecard local."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calidad.reglas_single_user import evaluar_corte


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corte", type=Path, help="JSON de auditar_corte_analitico.py")
    parser.add_argument("--fuentes", type=Path, help="JSON opcional de probes HTTP read-only por fuente")
    args = parser.parse_args()
    reporte = json.loads(args.corte.read_text(encoding="utf-8"))
    if args.fuentes:
        reporte["fuentes"] = json.loads(args.fuentes.read_text(encoding="utf-8"))
    print(json.dumps(evaluar_corte(reporte), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
