#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
limpiar_partidos_duplicados.py — Elimina partidos duplicados de la BD.

EJECUTAR CON CUIDADO: Este script elimina datos.

Uso:
    python scripts/limpiar_partidos_duplicados.py --dry-run   # Ver qué eliminaría
    python scripts/limpiar_partidos_duplicados.py --execute   # Ejecutar limpieza
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")


def obtener_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    if "sslmode=" not in url:
        separador = "&" if "?" in url else "?"
        url = f"{url}{separador}sslmode=require"
    return url


def main() -> int:
    import argparse

    import psycopg
    from psycopg.rows import dict_row

    parser = argparse.ArgumentParser(description="Limpia partidos duplicados")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar, no eliminar")
    parser.add_argument("--execute", action="store_true", help="Ejecutar limpieza")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("❌ Debes especificar --dry-run o --execute")
        return 1

    db_url = obtener_database_url()

    query_duplicados = """
        WITH duplicados AS (
            SELECT
                id,
                fecha_partido,
                equipo_local_id,
                equipo_visitante_id,
                tipo_partido,
                local_total,
                ROW_NUMBER() OVER (
                    PARTITION BY fecha_partido, equipo_local_id, equipo_visitante_id, tipo_partido
                    ORDER BY
                        CASE
                            WHEN local_total IS NOT NULL AND local_total > 0 THEN 0
                            ELSE 1
                        END,
                        id DESC
                ) AS rn
            FROM partidos
        )
        SELECT id, fecha_partido, equipo_local_id, equipo_visitante_id, local_total
        FROM duplicados
        WHERE rn > 1
    """

    with psycopg.connect(db_url) as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query_duplicados)
            duplicados = cursor.fetchall()

            if not duplicados:
                print("✅ No se encontraron partidos duplicados")
                return 0

            print(f"🔍 Encontrados {len(duplicados)} partidos duplicados para eliminar:")
            for duplicado in duplicados[:10]:
                print(
                    "   - ID: {id}, Fecha: {fecha_partido}".format(
                        id=duplicado["id"],
                        fecha_partido=duplicado["fecha_partido"],
                    )
                )

            if len(duplicados) > 10:
                print(f"   ... y {len(duplicados) - 10} más")

            if args.execute:
                ids_eliminar = [duplicado["id"] for duplicado in duplicados]
                cursor.execute(
                    "DELETE FROM partidos WHERE id = ANY(%s)",
                    [ids_eliminar],
                )
                conexion.commit()
                print(f"✅ Eliminados {len(ids_eliminar)} partidos duplicados")
            else:
                print("\n⚠️  Modo dry-run: No se eliminó nada")
                print("   Ejecuta con --execute para limpiar")

    return 0


if __name__ == "__main__":
    sys.exit(main())
