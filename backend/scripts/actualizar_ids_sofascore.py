#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar los IDs de Sofascore en la tabla competiciones_futbol.

Este script mapea los códigos internos de competiciones a los IDs de Sofascore,
verificando que cada ID sea válido haciendo una petición de prueba a la API.

Uso:
    python actualizar_ids_sofascore.py
    python actualizar_ids_sofascore.py --verificar
    python actualizar_ids_sofascore.py --dry-run
    python actualizar_ids_sofascore.py --verbose

Mapeos incluidos:
    - La Liga (España): ESP_LALIGA → 8
    - Premier League (Inglaterra): ENG_PREMIER → 17
    - Bundesliga (Alemania): GER_BUNDESLIGA → 35
    - Serie A (Italia): ITA_SERIEA → 23
    - Ligue 1 (Francia): FRA_LIGUE1 → 34
    - Champions League: EUR_CHAMPIONS → 7
    - Europa League: EUR_EUROPA → 679
    - Conference League: EUR_CONFERENCE → 17015
    - Copa del Rey: ESP_COPA → 329
    - FA Cup: ENG_FACUP → 29
    - DFB-Pokal: GER_DFBPOKAL → 44
    - Coppa Italia: ITA_COPPA → 327
    - Coupe de France: FRA_COUPE → 335
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Añadir el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import obtener_pool, cerrar_pool
from scrapers.sofascore.cliente import SofascoreClient
from scrapers.sofascore.excepciones import SofascoreError
from scrapers.sofascore.monitoreo import configurar_logging

# Mapeo completo de códigos internos a IDs de Sofascore
MAPEO_COMPETICIONES = {
    # Ligas principales
    'ESP_LALIGA': 8,
    'ENG_PREMIER': 17,
    'GER_BUNDESLIGA': 35,
    'ITA_SERIEA': 23,
    'FRA_LIGUE1': 34,

    # Competiciones europeas
    'EUR_CHAMPIONS': 7,
    'EUR_EUROPA': 679,
    'EUR_CONFERENCE': 17015,

    # Copas domésticas
    'ESP_COPA': 329,
    'ENG_FACUP': 29,
    'GER_DFBPOKAL': 44,
    'ITA_COPPA': 327,
    'FRA_COUPE': 335,

    # Segundas divisiones (opcional)
    'ESP_SEGUNDA': 54,
    'ENG_CHAMPIONSHIP': 18,
    'GER_2BUNDESLIGA': 36,
    'ITA_SERIEB': 53,
    'FRA_LIGUE2': 182,
}

logger = logging.getLogger(__name__)


def parsear_argumentos() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Actualiza IDs de Sofascore en competiciones_futbol',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--verificar',
        action='store_true',
        help='Verificar cada ID haciendo petición a Sofascore'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostrar cambios sin aplicarlos'
    )

    parser.add_argument(
        '--crear-faltantes',
        action='store_true',
        help='Crear competiciones que no existan en la BD'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )

    return parser.parse_args()


def verificar_id_sofascore(
    cliente: SofascoreClient,
    sofascore_id: int
) -> Tuple[bool, str]:
    """
    Verifica que un ID de Sofascore sea válido.

    Args:
        cliente: Cliente de Sofascore.
        sofascore_id: ID a verificar.

    Returns:
        Tupla (es_valido, nombre_torneo).
    """
    try:
        # Intentar obtener información del torneo
        datos = cliente.get(f'/unique-tournament/{sofascore_id}')

        if datos is None:
            return False, "No encontrado"

        # Extraer nombre del torneo
        torneo = datos.get('uniqueTournament', {})
        nombre = torneo.get('name', 'Desconocido')

        return True, nombre

    except SofascoreError as e:
        if e.codigo == 403:
            logger.error(
                "Sofascore bloqueó la petición (403). "
                "Revisar headers/cookies o usar una fuente alternativa."
            )
        return False, str(e)
    except Exception as e:
        return False, str(e)


def obtener_competiciones_bd(conexion) -> Dict[str, Dict]:
    """
    Obtiene las competiciones existentes en la BD.

    Returns:
        Diccionario {codigo: {id, nombre, sofascore_id}}.
    """
    competiciones = {}

    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, codigo, nombre, sofascore_id
            FROM competiciones_futbol
            WHERE activa = TRUE
            """
        )

        for row in cursor.fetchall():
            competiciones[row[1]] = {
                'id': row[0],
                'nombre': row[2],
                'sofascore_id': row[3],
            }

    return competiciones


def actualizar_sofascore_id(
    conexion,
    codigo: str,
    sofascore_id: int,
    dry_run: bool = False
) -> bool:
    """
    Actualiza el sofascore_id de una competición.

    Returns:
        True si se actualizó, False si no.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Actualizaría {codigo} → sofascore_id={sofascore_id}")
        return True

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                UPDATE competiciones_futbol
                SET sofascore_id = %s, actualizado_en = NOW()
                WHERE codigo = %s
                """,
                (sofascore_id, codigo)
            )
            conexion.commit()

            if cursor.rowcount > 0:
                logger.info(f"Actualizado: {codigo} → sofascore_id={sofascore_id}")
                return True
            else:
                logger.warning(f"No se encontró competición con código: {codigo}")
                return False

    except Exception as e:
        conexion.rollback()
        logger.error(f"Error actualizando {codigo}: {e}")
        return False


def crear_competicion(
    conexion,
    codigo: str,
    sofascore_id: int,
    nombre: str,
    dry_run: bool = False
) -> bool:
    """
    Crea una nueva competición en la BD.

    Returns:
        True si se creó, False si no.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Crearía competición: {codigo} ({nombre})")
        return True

    try:
        with conexion.cursor() as cursor:
            # Determinar tipo y país
            tipo = 'copa' if 'COPA' in codigo or 'CUP' in codigo or 'POKAL' in codigo else 'liga'

            if codigo.startswith('ESP_'):
                pais = 'España'
            elif codigo.startswith('ENG_'):
                pais = 'Inglaterra'
            elif codigo.startswith('GER_'):
                pais = 'Alemania'
            elif codigo.startswith('ITA_'):
                pais = 'Italia'
            elif codigo.startswith('FRA_'):
                pais = 'Francia'
            elif codigo.startswith('EUR_'):
                pais = 'Europa'
            else:
                pais = 'Desconocido'

            cursor.execute(
                """
                INSERT INTO competiciones_futbol (
                    codigo, nombre, pais, tipo, sofascore_id, activa
                ) VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
                """,
                (codigo, nombre, pais, tipo, sofascore_id)
            )
            nuevo_id = cursor.fetchone()[0]
            conexion.commit()

            logger.info(f"Creada competición: {codigo} (ID: {nuevo_id})")
            return True

    except Exception as e:
        conexion.rollback()
        logger.error(f"Error creando competición {codigo}: {e}")
        return False


def main():
    """Función principal del script."""
    args = parsear_argumentos()

    # Configurar logging
    nivel = logging.DEBUG if args.verbose else logging.INFO
    configurar_logging(nivel=nivel)

    logger.info("=" * 60)
    logger.info("ACTUALIZACIÓN DE IDS DE SOFASCORE")
    logger.info("=" * 60)

    # Conectar a BD
    try:
        pool = obtener_pool()
        conexion = pool.getconn()
        logger.info("Conexión a BD establecida")
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")
        sys.exit(1)

    # Crear cliente Sofascore (solo si vamos a verificar)
    cliente = None
    if args.verificar:
        cliente = SofascoreClient()
        logger.info("Cliente Sofascore inicializado")

    # Obtener competiciones existentes
    competiciones_bd = obtener_competiciones_bd(conexion)
    logger.info(f"Competiciones en BD: {len(competiciones_bd)}")

    # Estadísticas
    actualizados = 0
    creados = 0
    errores = 0
    sin_cambios = 0
    ids_invalidos = []

    try:
        for codigo, sofascore_id in MAPEO_COMPETICIONES.items():
            logger.debug(f"Procesando: {codigo} → {sofascore_id}")

            # Verificar ID si se solicitó
            if args.verificar and cliente:
                valido, nombre_torneo = verificar_id_sofascore(cliente, sofascore_id)

                if not valido:
                    logger.error(f"ID inválido: {codigo} → {sofascore_id} ({nombre_torneo})")
                    ids_invalidos.append((codigo, sofascore_id, nombre_torneo))
                    errores += 1
                    continue
                else:
                    logger.debug(f"ID válido: {codigo} → {sofascore_id} ({nombre_torneo})")

            # Verificar si existe en BD
            if codigo in competiciones_bd:
                comp_actual = competiciones_bd[codigo]

                # Verificar si ya tiene el ID correcto
                if comp_actual['sofascore_id'] == sofascore_id:
                    logger.debug(f"Sin cambios: {codigo} ya tiene sofascore_id={sofascore_id}")
                    sin_cambios += 1
                    continue

                # Actualizar
                if actualizar_sofascore_id(conexion, codigo, sofascore_id, args.dry_run):
                    actualizados += 1
                else:
                    errores += 1

            else:
                # No existe en BD
                if args.crear_faltantes:
                    # Obtener nombre del torneo si verificamos
                    nombre = codigo.replace('_', ' ').title()
                    if args.verificar and cliente:
                        _, nombre_torneo = verificar_id_sofascore(cliente, sofascore_id)
                        if nombre_torneo and nombre_torneo != "No encontrado":
                            nombre = nombre_torneo

                    if crear_competicion(conexion, codigo, sofascore_id, nombre, args.dry_run):
                        creados += 1
                    else:
                        errores += 1
                else:
                    logger.warning(
                        f"Competición {codigo} no existe en BD. "
                        f"Usa --crear-faltantes para crearla."
                    )

    except KeyboardInterrupt:
        logger.warning("\nInterrumpido por usuario")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cerrar conexiones
        if cliente:
            cliente.cerrar()
        pool.putconn(conexion)
        cerrar_pool()

    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Actualizados: {actualizados}")
    print(f"Creados: {creados}")
    print(f"Sin cambios: {sin_cambios}")
    print(f"Errores: {errores}")

    if ids_invalidos:
        print("\nIDs INVÁLIDOS:")
        for codigo, sofascore_id, error in ids_invalidos:
            print(f"  {codigo} → {sofascore_id}: {error}")

    print("=" * 60)

    sys.exit(0 if errores == 0 else 1)


if __name__ == '__main__':
    main()
