#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crear_usuario_desarrollo.py — Crea un usuario de desarrollo en la BD.

Uso:
    python crear_usuario_desarrollo.py
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
import psycopg

# Cargar variables de entorno
load_dotenv()

# UUID del usuario de desarrollo (debe coincidir con dependencias.py)
USUARIO_ID = "00000000-0000-0000-0000-000000000001"


def obtener_database_url() -> str:
    """Obtiene la URL de la base de datos."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está configurada.\n"
            "Asegúrate de tener un archivo .env con DATABASE_URL"
        )
    if "sslmode=" not in url:
        separador = "&" if "?" in url else "?"
        url = f"{url}{separador}sslmode=require"
    return url


def main() -> int:
    print("=" * 60)
    print("👤 CREAR USUARIO DE DESARROLLO")
    print("=" * 60)
    print()
    
    try:
        print("🔌 Conectando a la base de datos...")
        with psycopg.connect(obtener_database_url()) as conexion:
            print("✅ Conexión establecida")
            print()
            
            with conexion.cursor() as cursor:
                # Verificar si la tabla usuarios existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'usuarios'
                    )
                """)
                existe_tabla = cursor.fetchone()[0]
                
                if not existe_tabla:
                    print("❌ La tabla 'usuarios' no existe.")
                    print("   Debes crear el esquema de la BD primero.")
                    return 1
                
                # Insertar o actualizar usuario de desarrollo
                cursor.execute("""
                    INSERT INTO usuarios (
                        id,
                        email,
                        nombre,
                        password_hash,
                        rol,
                        activo,
                        preferencias,
                        bankroll_inicial
                    ) VALUES (
                        %s,
                        'desarrollo@analizadornba.local',
                        'Usuario Desarrollo',
                        'no_auth_dev_only',
                        'admin',
                        true,
                        '{"tema": "oscuro", "notificaciones": false}'::jsonb,
                        1000.00
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        activo = true
                    RETURNING id, email, nombre
                """, [USUARIO_ID])
                
                resultado = cursor.fetchone()
                conexion.commit()
                
                print("✅ Usuario de desarrollo creado/actualizado:")
                print(f"   ID:     {resultado[0]}")
                print(f"   Email:  {resultado[1]}")
                print(f"   Nombre: {resultado[2]}")
                
    except psycopg.errors.UndefinedTable as e:
        print(f"❌ Error: {e}")
        print("   La tabla 'usuarios' no existe. Crea el esquema primero.")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print()
    print("=" * 60)
    print("✅ USUARIO DE DESARROLLO LISTO")
    print("=" * 60)
    print()
    print("Ahora puedes usar la bitácora sin configurar autenticación.")
    print(f"El sistema usará automáticamente el usuario: {USUARIO_ID}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())