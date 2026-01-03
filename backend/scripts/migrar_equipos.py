#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración de equipos desde CSV hacia PostgreSQL.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"

sys.path.append(str(BACKEND_PATH))

from db import obtener_database_url  # noqa: E402


@dataclass
class ErrorFila:
    abreviatura: str
    errores: List[str]


def normalizar_conferencia(valor: str) -> Optional[str]:
    if not valor:
        return None
    valor = valor.strip().lower()
    if valor in {"este", "east"}:
        return "Este"
    if valor in {"oeste", "west"}:
        return "Oeste"
    return None


def validar_filas(ruta_csv: Path) -> Tuple[List[Dict[str, str]], List[ErrorFila]]:
    filas: List[Dict[str, str]] = []
    errores: List[ErrorFila] = []
    abreviaturas_vistas: set[str] = set()

    with ruta_csv.open("r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for indice, fila in enumerate(lector, start=2):
            fila_limpia = {k.strip(): (v or "").strip() for k, v in fila.items()}
            errores_fila: List[str] = []

            abreviatura = fila_limpia.get("abreviatura", "")
            if not abreviatura:
                errores_fila.append("abreviatura requerida")
            elif len(abreviatura) != 3 or not abreviatura.isalpha() or abreviatura.upper() != abreviatura:
                errores_fila.append("abreviatura debe ser 3 letras mayúsculas")
            elif abreviatura in abreviaturas_vistas:
                errores_fila.append("abreviatura duplicada en CSV")
            else:
                abreviaturas_vistas.add(abreviatura)

            nombre = fila_limpia.get("nombre", "")
            if not nombre:
                errores_fila.append("nombre requerido")

            nombre_corto = fila_limpia.get("nombre_corto", "")
            if not nombre_corto:
                errores_fila.append("nombre_corto requerido")

            division = fila_limpia.get("division", "")
            if not division:
                errores_fila.append("division requerida")

            conferencia_raw = fila_limpia.get("conferencia", "")
            conferencia = normalizar_conferencia(conferencia_raw)
            if not conferencia:
                errores_fila.append("conferencia inválida (Este/Oeste)")
            else:
                fila_limpia["conferencia"] = conferencia

            if errores_fila:
                errores.append(ErrorFila(abreviatura or f"fila_{indice}", errores_fila))
            else:
                filas.append(fila_limpia)

    return filas, errores


def ejecutar_migracion(ruta_csv: Path) -> int:
    filas, errores = validar_filas(ruta_csv)
    if errores:
        print("❌ Se encontraron errores en el CSV:")
        for error in errores:
            print(f"- {error.abreviatura}: {', '.join(error.errores)}")
        print(f"Total de filas con error: {len(errores)}")
        return 1

    insertados = 0
    actualizados = 0

    with psycopg.connect(obtener_database_url()) as conexion:
        with conexion.transaction():
            for fila in filas:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO equipos (
                            nombre,
                            nombre_corto,
                            abreviatura,
                            conferencia,
                            division,
                            ciudad,
                            activo
                        ) VALUES (
                            %(nombre)s,
                            %(nombre_corto)s,
                            %(abreviatura)s,
                            %(conferencia)s,
                            %(division)s,
                            %(ciudad)s,
                            true
                        )
                        ON CONFLICT (abreviatura) DO UPDATE SET
                            nombre = EXCLUDED.nombre,
                            nombre_corto = EXCLUDED.nombre_corto,
                            conferencia = EXCLUDED.conferencia,
                            division = EXCLUDED.division,
                            ciudad = EXCLUDED.ciudad,
                            activo = true
                        RETURNING (xmax = 0) AS insertado
                        """,
                        {
                            "nombre": fila["nombre"],
                            "nombre_corto": fila["nombre_corto"],
                            "abreviatura": fila["abreviatura"],
                            "conferencia": fila["conferencia"],
                            "division": fila["division"],
                            "ciudad": fila.get("ciudad") or None,
                        },
                    )
                    resultado = cursor.fetchone()
                    if resultado and resultado[0]:
                        insertados += 1
                    else:
                        actualizados += 1

        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM equipos")
            total = cursor.fetchone()[0]

    print("✅ Migración completada")
    print(f"Insertados: {insertados}")
    print(f"Actualizados: {actualizados}")
    print(f"Total en tabla equipos: {total}")
    return 0


def main() -> int:
    ruta_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("equipos.csv")
    if not ruta_csv.exists():
        print(f"❌ No se encontró el archivo CSV en {ruta_csv}")
        return 1
    return ejecutar_migracion(ruta_csv)


if __name__ == "__main__":
    raise SystemExit(main())
