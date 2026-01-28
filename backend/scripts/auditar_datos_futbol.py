#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de auditoría de datos de fútbol.

Este script valida la calidad e integridad de los datos de partidos
de fútbol en la base de datos, generando un reporte detallado de:

- Validaciones de integridad (sumas de goles/corners)
- Validaciones de rango (valores dentro de límites razonables)
- Validaciones de completitud (porcentaje de datos disponibles)
- Detección de valores atípicos

Uso:
    python auditar_datos_futbol.py
    python auditar_datos_futbol.py --competicion ESP_LALIGA
    python auditar_datos_futbol.py --exportar reporte.json
    python auditar_datos_futbol.py --verbose

Argumentos:
    --competicion: Código de competición a auditar (opcional)
    --temporada: Temporada específica a auditar (opcional)
    --exportar: Archivo para exportar reporte (JSON o CSV)
    --solo-errores: Mostrar solo problemas encontrados
    --verbose: Mostrar información detallada
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Añadir el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import obtener_pool, cerrar_pool
from scrapers.sofascore.monitoreo import configurar_logging

logger = logging.getLogger(__name__)

# Rangos normales para validación
RANGOS_NORMALES = {
    'corners_equipo': (0, 15),
    'corners_total': (0, 25),
    'disparos_equipo': (5, 30),
    'disparos_total': (10, 50),
    'xg_equipo': (0.0, 5.0),
    'posesion': (20.0, 80.0),
    'goles_equipo': (0, 8),
}


def parsear_argumentos() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Auditoría de datos de fútbol',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--competicion',
        type=str,
        default=None,
        help='Código de competición a auditar (opcional)'
    )

    parser.add_argument(
        '--temporada',
        type=str,
        default=None,
        help='Temporada específica a auditar (ej: 2024-25)'
    )

    parser.add_argument(
        '--exportar',
        type=str,
        default=None,
        help='Archivo para exportar reporte (JSON o CSV)'
    )

    parser.add_argument(
        '--solo-errores',
        action='store_true',
        help='Mostrar solo problemas encontrados'
    )

    parser.add_argument(
        '--listar-partidos',
        action='store_true',
        help='Listar partidos con problemas'
    )

    parser.add_argument(
        '--limite-partidos',
        type=int,
        default=50,
        help='Límite de partidos a listar por tipo de error'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )

    return parser.parse_args()


def validar_integridad_goles(conexion, competicion_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Valida que la suma de goles por tiempo sea igual al total.

    Returns:
        Diccionario con resultados de validación.
    """
    resultado = {
        'nombre': 'Integridad de goles',
        'partidos_validados': 0,
        'errores': 0,
        'detalles': [],
    }

    query = """
        SELECT id, sofascore_match_id, fecha_partido,
               local_goles_1t, local_goles_2t, local_goles_total,
               visitante_goles_1t, visitante_goles_2t, visitante_goles_total
        FROM partidos_futbol
        WHERE estado = 'FINALIZADO'
          AND local_goles_1t IS NOT NULL
          AND local_goles_2t IS NOT NULL
    """
    params = []

    if competicion_id:
        query += " AND competicion_id = %s"
        params.append(competicion_id)

    with conexion.cursor() as cursor:
        cursor.execute(query, params)

        for row in cursor.fetchall():
            resultado['partidos_validados'] += 1

            partido_id = row[0]
            sofascore_id = row[1]
            fecha = row[2]

            # Validar goles local
            suma_local = (row[3] or 0) + (row[4] or 0)
            total_local = row[5] or 0

            if suma_local != total_local:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'partido_id': partido_id,
                    'sofascore_id': sofascore_id,
                    'fecha': str(fecha),
                    'tipo': 'goles_local',
                    'suma': suma_local,
                    'total': total_local,
                })

            # Validar goles visitante
            suma_visitante = (row[6] or 0) + (row[7] or 0)
            total_visitante = row[8] or 0

            if suma_visitante != total_visitante:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'partido_id': partido_id,
                    'sofascore_id': sofascore_id,
                    'fecha': str(fecha),
                    'tipo': 'goles_visitante',
                    'suma': suma_visitante,
                    'total': total_visitante,
                })

    return resultado


def validar_integridad_corners(conexion, competicion_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Valida que la suma de corners por tiempo sea igual al total.

    Returns:
        Diccionario con resultados de validación.
    """
    resultado = {
        'nombre': 'Integridad de corners',
        'partidos_validados': 0,
        'errores': 0,
        'tolerancia': 1,  # ±1 de tolerancia
        'detalles': [],
    }

    query = """
        SELECT id, sofascore_match_id, fecha_partido,
               local_corners_1t, local_corners_2t, local_corners_total,
               visitante_corners_1t, visitante_corners_2t, visitante_corners_total
        FROM partidos_futbol
        WHERE estado = 'FINALIZADO'
          AND local_corners_1t IS NOT NULL
          AND local_corners_2t IS NOT NULL
          AND local_corners_total IS NOT NULL
    """
    params = []

    if competicion_id:
        query += " AND competicion_id = %s"
        params.append(competicion_id)

    with conexion.cursor() as cursor:
        cursor.execute(query, params)

        for row in cursor.fetchall():
            resultado['partidos_validados'] += 1

            partido_id = row[0]
            sofascore_id = row[1]
            fecha = row[2]

            # Validar corners local
            suma_local = (row[3] or 0) + (row[4] or 0)
            total_local = row[5] or 0

            if abs(suma_local - total_local) > 1:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'partido_id': partido_id,
                    'sofascore_id': sofascore_id,
                    'fecha': str(fecha),
                    'tipo': 'corners_local',
                    'suma': suma_local,
                    'total': total_local,
                    'diferencia': suma_local - total_local,
                })

            # Validar corners visitante
            suma_visitante = (row[6] or 0) + (row[7] or 0)
            total_visitante = row[8] or 0

            if abs(suma_visitante - total_visitante) > 1:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'partido_id': partido_id,
                    'sofascore_id': sofascore_id,
                    'fecha': str(fecha),
                    'tipo': 'corners_visitante',
                    'suma': suma_visitante,
                    'total': total_visitante,
                    'diferencia': suma_visitante - total_visitante,
                })

    return resultado


def validar_disparos_arco(conexion, competicion_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Valida que disparos al arco <= disparos totales.

    Returns:
        Diccionario con resultados de validación.
    """
    resultado = {
        'nombre': 'Integridad de disparos',
        'partidos_validados': 0,
        'errores': 0,
        'detalles': [],
    }

    query = """
        SELECT id, sofascore_match_id, fecha_partido,
               local_disparos_total, local_disparos_arco,
               visitante_disparos_total, visitante_disparos_arco
        FROM partidos_futbol
        WHERE estado = 'FINALIZADO'
          AND local_disparos_total IS NOT NULL
          AND local_disparos_arco IS NOT NULL
    """
    params = []

    if competicion_id:
        query += " AND competicion_id = %s"
        params.append(competicion_id)

    with conexion.cursor() as cursor:
        cursor.execute(query, params)

        for row in cursor.fetchall():
            resultado['partidos_validados'] += 1

            partido_id = row[0]
            sofascore_id = row[1]
            fecha = row[2]

            # Validar disparos local
            total_local = row[3] or 0
            arco_local = row[4] or 0

            if arco_local > total_local:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'partido_id': partido_id,
                    'sofascore_id': sofascore_id,
                    'fecha': str(fecha),
                    'tipo': 'disparos_local',
                    'total': total_local,
                    'arco': arco_local,
                })

            # Validar disparos visitante
            total_visitante = row[5] or 0
            arco_visitante = row[6] or 0

            if arco_visitante > total_visitante:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'partido_id': partido_id,
                    'sofascore_id': sofascore_id,
                    'fecha': str(fecha),
                    'tipo': 'disparos_visitante',
                    'total': total_visitante,
                    'arco': arco_visitante,
                })

    return resultado


def validar_posesion(conexion, competicion_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Valida que la suma de posesión sea aproximadamente 100%.

    Returns:
        Diccionario con resultados de validación.
    """
    resultado = {
        'nombre': 'Integridad de posesión',
        'partidos_validados': 0,
        'errores': 0,
        'tolerancia': 2.0,  # ±2% de tolerancia
        'detalles': [],
    }

    query = """
        SELECT id, sofascore_match_id, fecha_partido,
               local_posesion, visitante_posesion
        FROM partidos_futbol
        WHERE estado = 'FINALIZADO'
          AND local_posesion IS NOT NULL
          AND visitante_posesion IS NOT NULL
    """
    params = []

    if competicion_id:
        query += " AND competicion_id = %s"
        params.append(competicion_id)

    with conexion.cursor() as cursor:
        cursor.execute(query, params)

        for row in cursor.fetchall():
            resultado['partidos_validados'] += 1

            partido_id = row[0]
            sofascore_id = row[1]
            fecha = row[2]
            pos_local = float(row[3] or 0)
            pos_visitante = float(row[4] or 0)

            suma_posesion = pos_local + pos_visitante

            if abs(suma_posesion - 100.0) > 2.0:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'partido_id': partido_id,
                    'sofascore_id': sofascore_id,
                    'fecha': str(fecha),
                    'pos_local': pos_local,
                    'pos_visitante': pos_visitante,
                    'suma': suma_posesion,
                    'diferencia': suma_posesion - 100.0,
                })

    return resultado


def validar_rangos(conexion, competicion_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Valida que los valores estén dentro de rangos razonables.

    Returns:
        Diccionario con resultados de validación.
    """
    resultado = {
        'nombre': 'Validación de rangos',
        'partidos_validados': 0,
        'warnings': 0,
        'detalles': [],
    }

    query = """
        SELECT id, sofascore_match_id, fecha_partido,
               local_corners_total, visitante_corners_total,
               local_disparos_total, visitante_disparos_total,
               local_xg, visitante_xg,
               local_posesion, visitante_posesion,
               local_goles_total, visitante_goles_total
        FROM partidos_futbol
        WHERE estado = 'FINALIZADO'
    """
    params = []

    if competicion_id:
        query += " AND competicion_id = %s"
        params.append(competicion_id)

    with conexion.cursor() as cursor:
        cursor.execute(query, params)

        for row in cursor.fetchall():
            resultado['partidos_validados'] += 1

            partido_id = row[0]
            sofascore_id = row[1]
            fecha = row[2]

            valores = {
                'corners_local': row[3],
                'corners_visitante': row[4],
                'disparos_local': row[5],
                'disparos_visitante': row[6],
                'xg_local': row[7],
                'xg_visitante': row[8],
                'posesion_local': row[9],
                'posesion_visitante': row[10],
                'goles_local': row[11],
                'goles_visitante': row[12],
            }

            # Validar rangos
            for campo, valor in valores.items():
                if valor is None:
                    continue

                # Determinar el tipo de rango
                if 'corners' in campo:
                    min_val, max_val = RANGOS_NORMALES['corners_equipo']
                elif 'disparos' in campo:
                    min_val, max_val = RANGOS_NORMALES['disparos_equipo']
                elif 'xg' in campo:
                    min_val, max_val = RANGOS_NORMALES['xg_equipo']
                elif 'posesion' in campo:
                    min_val, max_val = RANGOS_NORMALES['posesion']
                elif 'goles' in campo:
                    min_val, max_val = RANGOS_NORMALES['goles_equipo']
                else:
                    continue

                if valor < min_val or valor > max_val:
                    resultado['warnings'] += 1
                    resultado['detalles'].append({
                        'partido_id': partido_id,
                        'sofascore_id': sofascore_id,
                        'fecha': str(fecha),
                        'campo': campo,
                        'valor': float(valor),
                        'rango': f'{min_val}-{max_val}',
                    })

    return resultado


def calcular_cobertura_estadisticas(conexion, competicion_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Calcula el porcentaje de partidos con cada tipo de estadística.

    Returns:
        Diccionario con cobertura de estadísticas.
    """
    resultado = {
        'total_finalizados': 0,
        'cobertura': {},
    }

    base_query = """
        SELECT COUNT(*) as total,
            SUM(CASE WHEN local_corners_total IS NOT NULL THEN 1 ELSE 0 END) as con_corners_total,
            SUM(CASE WHEN local_corners_1t IS NOT NULL THEN 1 ELSE 0 END) as con_corners_tiempo,
            SUM(CASE WHEN local_disparos_total IS NOT NULL THEN 1 ELSE 0 END) as con_disparos,
            SUM(CASE WHEN local_xg IS NOT NULL THEN 1 ELSE 0 END) as con_xg,
            SUM(CASE WHEN local_posesion IS NOT NULL THEN 1 ELSE 0 END) as con_posesion,
            SUM(CASE WHEN datos_completos = TRUE THEN 1 ELSE 0 END) as completos
        FROM partidos_futbol
        WHERE estado = 'FINALIZADO'
    """
    params = []

    if competicion_id:
        base_query += " AND competicion_id = %s"
        params.append(competicion_id)

    with conexion.cursor() as cursor:
        cursor.execute(base_query, params)
        row = cursor.fetchone()

        if row and row[0] > 0:
            total = row[0]
            resultado['total_finalizados'] = total

            resultado['cobertura'] = {
                'corners_total': round(row[1] / total * 100, 1),
                'corners_por_tiempo': round(row[2] / total * 100, 1),
                'disparos': round(row[3] / total * 100, 1),
                'xg': round(row[4] / total * 100, 1),
                'posesion': round(row[5] / total * 100, 1),
                'completos': round(row[6] / total * 100, 1) if row[6] else 0,
            }

    return resultado


def generar_reporte_competicion(conexion, competicion_id: int, nombre: str) -> Dict[str, Any]:
    """
    Genera reporte completo para una competición.

    Returns:
        Diccionario con todas las validaciones.
    """
    reporte = {
        'competicion': nombre,
        'competicion_id': competicion_id,
        'fecha_reporte': datetime.now().isoformat(),
        'validaciones': [],
        'cobertura': {},
        'resumen': {
            'total_errores': 0,
            'total_warnings': 0,
        }
    }

    # Ejecutar validaciones
    val_goles = validar_integridad_goles(conexion, competicion_id)
    val_corners = validar_integridad_corners(conexion, competicion_id)
    val_disparos = validar_disparos_arco(conexion, competicion_id)
    val_posesion = validar_posesion(conexion, competicion_id)
    val_rangos = validar_rangos(conexion, competicion_id)

    reporte['validaciones'] = [
        val_goles, val_corners, val_disparos, val_posesion, val_rangos
    ]

    # Calcular cobertura
    cobertura = calcular_cobertura_estadisticas(conexion, competicion_id)
    reporte['cobertura'] = cobertura

    # Resumen
    reporte['resumen']['total_errores'] = (
        val_goles['errores'] +
        val_corners['errores'] +
        val_disparos['errores'] +
        val_posesion['errores']
    )
    reporte['resumen']['total_warnings'] = val_rangos.get('warnings', 0)

    return reporte


def imprimir_reporte(reporte: Dict[str, Any], solo_errores: bool = False, listar_partidos: bool = False, limite: int = 50):
    """Imprime el reporte de forma legible."""
    print(f"\n{'='*60}")
    print(f"AUDITORÍA: {reporte['competicion']}")
    print(f"{'='*60}")
    print(f"Fecha: {reporte['fecha_reporte']}")

    # Cobertura
    if not solo_errores:
        print(f"\n--- COBERTURA DE ESTADÍSTICAS ---")
        cob = reporte['cobertura']
        print(f"Total partidos finalizados: {cob.get('total_finalizados', 0)}")
        for stat, pct in cob.get('cobertura', {}).items():
            print(f"  {stat}: {pct}%")

    # Validaciones
    print(f"\n--- VALIDACIONES ---")
    for val in reporte['validaciones']:
        errores = val.get('errores', val.get('warnings', 0))
        validados = val.get('partidos_validados', 0)

        if solo_errores and errores == 0:
            continue

        estado = "✓ OK" if errores == 0 else f"✗ ERRORES: {errores}"
        print(f"\n{val['nombre']}: {estado}")
        print(f"  Partidos validados: {validados}")

        if listar_partidos and errores > 0:
            detalles = val.get('detalles', [])[:limite]
            for det in detalles:
                print(f"    - Partido {det.get('sofascore_id')} ({det.get('fecha')}): {det}")

    # Resumen
    print(f"\n--- RESUMEN ---")
    print(f"Total errores de integridad: {reporte['resumen']['total_errores']}")
    print(f"Total warnings de rango: {reporte['resumen']['total_warnings']}")
    print(f"{'='*60}")


def exportar_reporte(reporte: Dict[str, Any], archivo: str):
    """Exporta el reporte a archivo JSON o CSV."""
    if archivo.endswith('.json'):
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Reporte exportado a {archivo}")

    elif archivo.endswith('.csv'):
        # Exportar resumen a CSV
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Validación', 'Partidos', 'Errores/Warnings'])

            for val in reporte['validaciones']:
                writer.writerow([
                    val['nombre'],
                    val.get('partidos_validados', 0),
                    val.get('errores', val.get('warnings', 0))
                ])

        logger.info(f"Reporte exportado a {archivo}")

    else:
        logger.warning(f"Formato de archivo no soportado: {archivo}")


def main():
    """Función principal del script."""
    args = parsear_argumentos()

    # Configurar logging
    nivel = logging.DEBUG if args.verbose else logging.INFO
    configurar_logging(nivel=nivel)

    logger.info("=" * 60)
    logger.info("AUDITORÍA DE DATOS DE FÚTBOL")
    logger.info("=" * 60)

    # Conectar a BD
    try:
        pool = obtener_pool()
        conexion = pool.getconn()
        logger.info("Conexión a BD establecida")
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")
        sys.exit(1)

    reportes = []

    try:
        with conexion.cursor() as cursor:
            # Obtener competiciones a auditar
            if args.competicion:
                cursor.execute(
                    """
                    SELECT id, codigo, nombre
                    FROM competiciones_futbol
                    WHERE codigo = %s AND activo = TRUE
                    """,
                    (args.competicion,)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, codigo, nombre
                    FROM competiciones_futbol
                    WHERE activo = TRUE
                    ORDER BY nombre
                    """
                )

            competiciones = cursor.fetchall()

            if not competiciones:
                logger.warning("No se encontraron competiciones para auditar")
                sys.exit(0)

            for comp_id, codigo, nombre in competiciones:
                logger.info(f"Auditando: {nombre} ({codigo})")

                reporte = generar_reporte_competicion(conexion, comp_id, nombre)
                reportes.append(reporte)

                imprimir_reporte(
                    reporte,
                    args.solo_errores,
                    args.listar_partidos,
                    args.limite_partidos
                )

        # Exportar si se solicitó
        if args.exportar:
            if len(reportes) == 1:
                exportar_reporte(reportes[0], args.exportar)
            else:
                exportar_reporte({'reportes': reportes}, args.exportar)

    except KeyboardInterrupt:
        logger.warning("\nInterrumpido por usuario")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        pool.putconn(conexion)
        cerrar_pool()

    # Resumen final
    total_errores = sum(r['resumen']['total_errores'] for r in reportes)
    total_warnings = sum(r['resumen']['total_warnings'] for r in reportes)

    print(f"\n{'='*60}")
    print("RESUMEN GLOBAL")
    print(f"{'='*60}")
    print(f"Competiciones auditadas: {len(reportes)}")
    print(f"Total errores de integridad: {total_errores}")
    print(f"Total warnings de rango: {total_warnings}")
    print(f"{'='*60}")

    sys.exit(0 if total_errores == 0 else 1)


if __name__ == '__main__':
    main()