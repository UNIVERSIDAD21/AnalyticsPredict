#!/usr/bin/env python3
"""Ajusta/evalúa WNBA offline desde BD READ ONLY; publica exclusivamente su artefacto."""
from pathlib import Path
import argparse, json, sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from servicios.predictor_wnba import construir, leer_datos, publicar, escribir


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corte", required=True)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--publicar", action="store_true")
    a = p.parse_args()
    m = construir(leer_datos(), a.corte)
    escribir(a.salida / "modelo.json", m)
    escribir(a.salida / "evaluacion.json", m["validacion"])
    if a.publicar:
        publicar(m)
    print(
        json.dumps(
            {
                "version": m["version"],
                "partidos": len(m["datos"]),
                "validacion": m["validacion"]["evaluacion"],
                "publicado": a.publicar,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
