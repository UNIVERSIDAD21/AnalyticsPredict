"""Entrena y registra una versión NBA solo mediante invocación explícita del operador."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from db import cerrar_pool, obtener_pool  # noqa: E402
from motor_autoentrenamiento import GestorModelo  # noqa: E402
from motor_autoentrenamiento.artefacto_nba import ruta_artefacto  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Entrenamiento NBA explícito; escribe una versión en BD")
    parser.add_argument("--entrenar", action="store_true", help="Confirma la operación con escritura")
    argumentos = parser.parse_args()
    if not argumentos.entrenar:
        parser.error("Usa --entrenar para registrar una versión nueva y publicar el artefacto")
    load_dotenv(BACKEND / ".env", override=True)
    try:
        gestor = GestorModelo.obtener_instancia(obtener_pool())
        gestor.reentrenar()
        modelo = gestor.modelo
        print(json.dumps({
            "modelo_version_id": modelo.version,
            "equipos": modelo.cantidad_equipos,
            "dataset_hash": modelo.metricas.get("hash_datos"),
            "fecha_entrenamiento": modelo.fecha_entrenamiento.isoformat(),
            "artefacto": str(ruta_artefacto()),
            "certificacion_analitica": "NO_CERTIFICADO",
        }))
        return 0
    finally:
        cerrar_pool()


if __name__ == "__main__":
    raise SystemExit(main())
