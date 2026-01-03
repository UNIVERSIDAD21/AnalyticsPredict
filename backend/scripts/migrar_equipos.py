#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrar_equipos.py — Migración de equipos desde CSV hacia PostgreSQL.

Uso:
    python migrar_equipos.py
    python migrar_equipos.py ruta/al/equipos.csv
"""

from __future__ import annotations

import csv
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
import psycopg

# Cargar variables de entorno
load_dotenv()


@dataclass
class ErrorFila:
    """Representa un error encontrado en una fila del CSV."""
    abreviatura: str
    errores: List[str]


def obtener_database_url() -> str:
    """Obtiene la URL de la base de datos."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está configurada.\n"
            "Asegúrate de tener un archivo .env con:\n"
            "DATABASE_URL=postgresql://usuario:password@host/database?sslmode=require"
        )
    # Asegurar SSL
    if "sslmode=" not in url:
        separador = "&" if "?" in url else "?"
        url = f"{url}{separador}sslmode=require"
    return url


def normalizar_conferencia(valor: str) -> Optional[str]:
    """Normaliza el valor de conferencia a Este/Oeste."""
    if not valor:
        return None
    valor = valor.strip().lower()
    if valor in {"este", "east"}:
        return "Este"
    if valor in {"oeste", "west"}:
        return "Oeste"
    return None


def validar_filas(ruta_csv: Path) -> Tuple[List[Dict[str, str]], List[ErrorFila]]:
    """
    Valida todas las filas del CSV.
    
    Retorna:
        Tuple con (filas_validas, errores_encontrados)
    """
    filas: List[Dict[str, str]] = []
    errores: List[ErrorFila] = []
    abreviaturas_vistas: set[str] = set()

    with ruta_csv.open("r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for indice, fila in enumerate(lector, start=2):
            # Limpiar valores
            fila_limpia = {k.strip(): (v or "").strip() for k, v in fila.items()}
            errores_fila: List[str] = []

            # Validar abreviatura
            abreviatura = fila_limpia.get("abreviatura", "")
            if not abreviatura:
                errores_fila.append("abreviatura requerida")
            elif len(abreviatura) != 3:
                errores_fila.append(f"abreviatura debe ser 3 letras (tiene {len(abreviatura)})")
            elif not abreviatura.isalpha():
                errores_fila.append("abreviatura debe contener solo letras")
            elif abreviatura.upper() != abreviatura:
                # Normalizar a mayúsculas
                abreviatura = abreviatura.upper()
                fila_limpia["abreviatura"] = abreviatura
            
            if abreviatura in abreviaturas_vistas:
                errores_fila.append("abreviatura duplicada en CSV")
            else:
                abreviaturas_vistas.add(abreviatura)

            # Validar nombre
            nombre = fila_limpia.get("nombre", "")
            if not nombre:
                errores_fila.append("nombre requerido")

            # Validar nombre_corto
            nombre_corto = fila_limpia.get("nombre_corto", "")
            if not nombre_corto:
                errores_fila.append("nombre_corto requerido")

            # Validar division
            division = fila_limpia.get("division", "")
            if not division:
                errores_fila.append("division requerida")

            # Validar y normalizar conferencia
            conferencia_raw = fila_limpia.get("conferencia", "")
            conferencia = normalizar_conferencia(conferencia_raw)
            if not conferencia:
                errores_fila.append(f"conferencia inválida: '{conferencia_raw}' (debe ser Este/Oeste)")
            else:
                fila_limpia["conferencia"] = conferencia

            # Agregar a resultados
            if errores_fila:
                errores.append(ErrorFila(abreviatura or f"fila_{indice}", errores_fila))
            else:
                filas.append(fila_limpia)

    return filas, errores


def ejecutar_migracion(ruta_csv: Path) -> int:
    """
    Ejecuta la migración del CSV a la base de datos.
    
    Retorna:
        0 si éxito, 1 si error
    """
    print("=" * 60)
    print("🏀 MIGRACIÓN DE EQUIPOS NBA")
    print("=" * 60)
    print(f"📁 Archivo CSV: {ruta_csv}")
    print()

    # Validar CSV
    print("📋 Validando datos del CSV...")
    filas, errores = validar_filas(ruta_csv)
    
    if errores:
        print()
        print("❌ Se encontraron errores en el CSV:")
        print("-" * 40)
        for error in errores:
            print(f"  • {error.abreviatura}:")
            for e in error.errores:
                print(f"      - {e}")
        print("-" * 40)
        print(f"Total de filas con error: {len(errores)}")
        print()
        print("⚠️  Corrige los errores y vuelve a ejecutar.")
        return 1

    print(f"✅ {len(filas)} equipos validados correctamente")
    print()

    # Conectar y migrar
    print("🔌 Conectando a la base de datos...")
    insertados = 0
    actualizados = 0

    try:
        with psycopg.connect(obtener_database_url()) as conexion:
            print("✅ Conexión establecida")
            print()
            print("📤 Migrando equipos...")
            
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
                            print(f"  ✅ INSERT: {fila['abreviatura']} - {fila['nombre']}")
                        else:
                            actualizados += 1
                            print(f"  🔄 UPDATE: {fila['abreviatura']} - {fila['nombre']}")

            # Verificar total
            with conexion.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM equipos WHERE activo = true")
                total = cursor.fetchone()[0]

    except psycopg.OperationalError as e:
        print()
        print(f"❌ Error de conexión: {e}")
        print()
        print("Verifica que:")
        print("  1. DATABASE_URL esté correctamente configurada en .env")
        print("  2. La base de datos sea accesible")
        print("  3. Las credenciales sean correctas")
        return 1
    except psycopg.errors.UndefinedTable:
        print()
        print("❌ Error: La tabla 'equipos' no existe en la base de datos.")
        print()
        print("Debes crear las tablas primero ejecutando el script SQL de esquema.")
        return 1
    except Exception as e:
        print()
        print(f"❌ Error inesperado: {e}")
        return 1

    # Reporte final
    print()
    print("=" * 60)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 60)
    print(f"  📥 Insertados:   {insertados}")
    print(f"  🔄 Actualizados: {actualizados}")
    print(f"  📊 Total en BD:  {total}")
    print("=" * 60)
    
    return 0


def main() -> int:
    """Punto de entrada principal."""
    # Determinar ruta del CSV
    if len(sys.argv) > 1:
        ruta_csv = Path(sys.argv[1])
    else:
        # Buscar equipos.csv en el directorio actual o en el directorio del script
        ruta_actual = Path("equipos.csv")
        ruta_script = Path(__file__).parent / "equipos.csv"
        
        if ruta_actual.exists():
            ruta_csv = ruta_actual
        elif ruta_script.exists():
            ruta_csv = ruta_script
        else:
            print("❌ No se encontró el archivo equipos.csv")
            print()
            print("Uso:")
            print("  python migrar_equipos.py")
            print("  python migrar_equipos.py ruta/al/equipos.csv")
            return 1

    if not ruta_csv.exists():
        print(f"❌ No se encontró el archivo CSV en: {ruta_csv}")
        return 1

    return ejecutar_migracion(ruta_csv)


if __name__ == "__main__":
    raise SystemExit(main())