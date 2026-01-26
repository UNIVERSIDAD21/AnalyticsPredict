#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de sincronización continua de datos de fútbol desde Sofascore.

Este script mantiene los datos actualizados sincronizando partidos
recientes y próximos. Está diseñado para ejecutarse periódicamente
(por ejemplo, diariamente) para mantener los datos al día.

Uso:
    python sincronizar_futbol.py --liga laliga --dias 7
    python sincronizar_futbol.py --liga todas --dias 3 --incluir-futuros
    python sincronizar_futbol.py --liga premier --forzar-estadisticas

Argumentos:
    --liga: Código de liga o "todas"
    --dias: Días hacia atrás a revisar (default: 7)
    --incluir-futuros: También sincronizar próximos partidos
    --dias-futuros: Días hacia adelante para partidos futuros (default: 14)
    --solo-resultados: Solo actualizar resultados, no estadísticas
    --forzar-estadisticas: Re-obtener estadísticas aunque ya existan
    --calcular-agregados: Recalcular estadísticas de equipos
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Añadir el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import obtener_pool, cerrar_pool
from scrapers.sofascore.cliente import SofascoreClient
from scrapers.sofascore.temporadas import obtener_temporada_activa
from scrapers.sofascore.partidos import (
    obtener_partidos_pasados,
    obtener_partidos_futuros,
    PartidoBasico,
)
from scrapers.sofascore.estadisticas import obtener_estadisticas_partido
from scrapers.sofascore.sincronizador import (
    resolver_competicion_id,
    sincronizar_partido_completo,
    verificar_partido_existe,
    obtener_partidos_sin_estadisticas,
    limpiar_cache,
)
from scrapers.sofascore.calculador_estadisticas import (
    actualizar_estadisticas_todos_equipos,
)
from scrapers.sofascore.monitoreo import (
    configurar_logging,
    RegistradorIngesta,
)

# Mapeo de códigos de liga
LIGAS_SOFASCORE = {
    'laliga': 8,
    'premier': 17,
    'bundesliga': 35,
    'seriea': 23,
    'ligue1': 34,
    'champions': 7,
    'europa': 679,
}

logger = logging.getLogger(__name__)


def parsear_argumentos() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Sincronización continua de datos de fútbol desde Sofascore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s --liga laliga --dias 7
  %(prog)s --liga todas --dias 3 --incluir-futuros --verbose
  %(prog)s --liga premier --forzar-estadisticas
  %(prog)s --liga laliga --calcular-agregados
        """
    )

    parser.add_argument(
        '--liga',
        type=str,
        required=True,
        help='Código de liga o "todas"'
    )

    parser.add_argument(
        '--dias',
        type=int,
        default=7,
        help='Días hacia atrás a revisar (default: 7)'
    )

    parser.add_argument(
        '--incluir-futuros',
        action='store_true',
        default=True,
        help='También sincronizar próximos partidos (default: True)'
    )

    parser.add_argument(
        '--no-futuros',
        action='store_true',
        help='No sincronizar partidos futuros'
    )

    parser.add_argument(
        '--dias-futuros',
        type=int,
        default=14,
        help='Días hacia adelante para partidos futuros (default: 14)'
    )

    parser.add_argument(
        '--solo-resultados',
        action='store_true',
        help='Solo actualizar resultados, no estadísticas'
    )

    parser.add_argument(
        '--forzar-estadisticas',
        action='store_true',
        help='Re-obtener estadísticas aunque ya existan'
    )

    parser.add_argument(
        '--calcular-agregados',
        action='store_true',
        help='Recalcular estadísticas de equipos al finalizar'
    )

    parser.add_argument(
        '--completar-estadisticas',
        action='store_true',
        help='Obtener estadísticas de partidos finalizados que no las tienen'
    )

    parser.add_argument(
        '--limite-completar',
        type=int,
        default=50,
        help='Límite de partidos a completar estadísticas (default: 50)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )

    return parser.parse_args()


def obtener_ligas_a_procesar(codigo_liga: str) -> List[str]:
    """Obtiene lista de códigos de liga a procesar."""
    if codigo_liga.lower() == 'todas':
        return list(LIGAS_SOFASCORE.keys())
    elif codigo_liga.lower() in LIGAS_SOFASCORE:
        return [codigo_liga.lower()]
    else:
        raise ValueError(
            f"Liga '{codigo_liga}' no reconocida. "
            f"Opciones: {', '.join(LIGAS_SOFASCORE.keys())}, todas"
        )


def sincronizar_partidos_recientes(
    conexion,
    cliente: SofascoreClient,
    liga_id: int,
    competicion_id: int,
    temporada_sofascore_id: int,
    temporada_id: int,
    dias: int,
    obtener_stats: bool = True,
    registrador: Optional[RegistradorIngesta] = None
) -> Dict[str, Any]:
    """
    Sincroniza partidos de los últimos N días.

    Returns:
        Diccionario con resumen de la sincronización.
    """
    resultado = {
        'procesados': 0,
        'insertados': 0,
        'actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0,
    }

    desde_fecha = datetime.now() - timedelta(days=dias)

    logger.info(f"Obteniendo partidos desde {desde_fecha.strftime('%Y-%m-%d')}...")

    partidos = obtener_partidos_pasados(
        cliente, liga_id, temporada_sofascore_id,
        desde_fecha=desde_fecha,
        limite_paginas=10
    )

    logger.info(f"Encontrados {len(partidos)} partidos recientes")

    for partido in partidos:
        try:
            sync_resultado = sincronizar_partido_completo(
                conexion, cliente, partido, liga_id,
                temporada_id=temporada_id,
                competicion_id=competicion_id,
                obtener_estadisticas_flag=obtener_stats and partido.esta_finalizado()
            )

            resultado['procesados'] += 1

            if sync_resultado['insertado']:
                resultado['insertados'] += 1
                if registrador:
                    registrador.registrar_partido(
                        partido.sofascore_id, True, sync_resultado['tiene_estadisticas']
                    )
            elif sync_resultado['cambios']:
                resultado['actualizados'] += 1
                if registrador:
                    registrador.registrar_partido(
                        partido.sofascore_id, False, sync_resultado['tiene_estadisticas']
                    )

            if sync_resultado['tiene_estadisticas']:
                resultado['con_estadisticas'] += 1

            if sync_resultado['errores']:
                resultado['errores'] += 1

        except Exception as e:
            logger.error(f"Error procesando partido {partido.sofascore_id}: {e}")
            resultado['errores'] += 1
            if registrador:
                registrador.registrar_error(e, {'partido_id': partido.sofascore_id})

    return resultado


def sincronizar_partidos_futuros(
    conexion,
    cliente: SofascoreClient,
    liga_id: int,
    competicion_id: int,
    temporada_sofascore_id: int,
    temporada_id: int,
    dias: int,
    registrador: Optional[RegistradorIngesta] = None
) -> Dict[str, Any]:
    """
    Sincroniza partidos próximos.

    Returns:
        Diccionario con resumen de la sincronización.
    """
    resultado = {
        'procesados': 0,
        'insertados': 0,
        'actualizados': 0,
        'errores': 0,
    }

    logger.info(f"Obteniendo partidos futuros (próximos {dias} días)...")

    partidos = obtener_partidos_futuros(
        cliente, liga_id, temporada_sofascore_id,
        limite_dias=dias,
        limite_paginas=5
    )

    logger.info(f"Encontrados {len(partidos)} partidos futuros")

    for partido in partidos:
        try:
            sync_resultado = sincronizar_partido_completo(
                conexion, cliente, partido, liga_id,
                temporada_id=temporada_id,
                competicion_id=competicion_id,
                obtener_estadisticas_flag=False  # Futuros no tienen stats
            )

            resultado['procesados'] += 1

            if sync_resultado['insertado']:
                resultado['insertados'] += 1
                if registrador:
                    registrador.registrar_partido(partido.sofascore_id, True)
            elif sync_resultado['cambios']:
                resultado['actualizados'] += 1

        except Exception as e:
            logger.error(f"Error procesando partido futuro {partido.sofascore_id}: {e}")
            resultado['errores'] += 1
            if registrador:
                registrador.registrar_error(e, {'partido_id': partido.sofascore_id})

    return resultado


def completar_estadisticas_faltantes(
    conexion,
    cliente: SofascoreClient,
    competicion_id: int,
    temporada_id: int,
    limite: int = 50,
    registrador: Optional[RegistradorIngesta] = None
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de partidos finalizados que no las tienen.

    Returns:
        Diccionario con resumen.
    """
    resultado = {
        'procesados': 0,
        'con_estadisticas': 0,
        'sin_estadisticas': 0,
        'errores': 0,
    }

    logger.info("Buscando partidos sin estadísticas...")

    partidos_sin_stats = obtener_partidos_sin_estadisticas(
        conexion, competicion_id, temporada_id, limite
    )

    logger.info(f"Encontrados {len(partidos_sin_stats)} partidos sin estadísticas")

    for partido_info in partidos_sin_stats:
        try:
            sofascore_id = partido_info['sofascore_match_id']

            stats = obtener_estadisticas_partido(cliente, sofascore_id)

            if stats:
                # Actualizar partido con estadísticas
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE partidos_futbol
                        SET
                            corners_local_1t = %s,
                            corners_local_2t = %s,
                            corners_local_total = %s,
                            corners_visitante_1t = %s,
                            corners_visitante_2t = %s,
                            corners_visitante_total = %s,
                            disparos_local_total = %s,
                            disparos_local_arco = %s,
                            disparos_visitante_total = %s,
                            disparos_visitante_arco = %s,
                            posesion_local = %s,
                            posesion_visitante = %s,
                            xg_local = %s,
                            xg_visitante = %s,
                            datos_estadisticas_completos = %s,
                            actualizado_en = NOW()
                        WHERE id = %s
                        """,
                        (
                            stats.corners_local_1t,
                            stats.corners_local_2t,
                            stats.corners_local_total,
                            stats.corners_visitante_1t,
                            stats.corners_visitante_2t,
                            stats.corners_visitante_total,
                            stats.disparos_local_total,
                            stats.disparos_local_arco,
                            stats.disparos_visitante_total,
                            stats.disparos_visitante_arco,
                            stats.posesion_local,
                            stats.posesion_visitante,
                            stats.xg_local,
                            stats.xg_visitante,
                            stats.datos_completos,
                            partido_info['id']
                        )
                    )
                    conexion.commit()

                resultado['con_estadisticas'] += 1
                logger.debug(f"Estadísticas añadidas a partido {sofascore_id}")
            else:
                resultado['sin_estadisticas'] += 1

            resultado['procesados'] += 1

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de {partido_info['sofascore_match_id']}: {e}")
            resultado['errores'] += 1

    return resultado


def procesar_liga(
    conexion,
    cliente: SofascoreClient,
    codigo_liga: str,
    args: argparse.Namespace,
    registrador: RegistradorIngesta
) -> Dict[str, Any]:
    """
    Procesa una liga para sincronización.

    Returns:
        Diccionario con resumen del procesamiento.
    """
    liga_id = LIGAS_SOFASCORE[codigo_liga]

    logger.info(f"\n{'='*60}")
    logger.info(f"Sincronizando: {codigo_liga.upper()} (ID: {liga_id})")
    logger.info(f"{'='*60}")

    resultado = {
        'liga': codigo_liga,
        'partidos_procesados': 0,
        'insertados': 0,
        'actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0,
    }

    # Obtener competicion_id
    competicion_id = resolver_competicion_id(conexion, liga_id)

    if competicion_id is None:
        logger.error(f"Competición {codigo_liga} no encontrada en BD")
        resultado['errores'] += 1
        return resultado

    # Obtener temporada activa
    temporada = obtener_temporada_activa(conexion, competicion_id)

    if temporada is None:
        logger.error(f"No hay temporada activa para {codigo_liga}")
        resultado['errores'] += 1
        return resultado

    temporada_id = temporada['id']
    temporada_sofascore_id = temporada['sofascore_season_id']

    logger.info(f"Temporada activa: {temporada['nombre']} (ID: {temporada_sofascore_id})")

    # Sincronizar partidos recientes
    obtener_stats = not args.solo_resultados

    sync_recientes = sincronizar_partidos_recientes(
        conexion, cliente, liga_id, competicion_id,
        temporada_sofascore_id, temporada_id,
        args.dias, obtener_stats, registrador
    )

    resultado['partidos_procesados'] += sync_recientes['procesados']
    resultado['insertados'] += sync_recientes['insertados']
    resultado['actualizados'] += sync_recientes['actualizados']
    resultado['con_estadisticas'] += sync_recientes['con_estadisticas']
    resultado['errores'] += sync_recientes['errores']

    logger.info(
        f"Partidos recientes: "
        f"+{sync_recientes['insertados']} "
        f"~{sync_recientes['actualizados']} "
        f"stats:{sync_recientes['con_estadisticas']} "
        f"err:{sync_recientes['errores']}"
    )

    # Sincronizar partidos futuros
    if args.incluir_futuros and not args.no_futuros:
        sync_futuros = sincronizar_partidos_futuros(
            conexion, cliente, liga_id, competicion_id,
            temporada_sofascore_id, temporada_id,
            args.dias_futuros, registrador
        )

        resultado['partidos_procesados'] += sync_futuros['procesados']
        resultado['insertados'] += sync_futuros['insertados']
        resultado['actualizados'] += sync_futuros['actualizados']
        resultado['errores'] += sync_futuros['errores']

        logger.info(
            f"Partidos futuros: "
            f"+{sync_futuros['insertados']} "
            f"~{sync_futuros['actualizados']} "
            f"err:{sync_futuros['errores']}"
        )

    # Completar estadísticas faltantes
    if args.completar_estadisticas or args.forzar_estadisticas:
        completar = completar_estadisticas_faltantes(
            conexion, cliente, competicion_id, temporada_id,
            args.limite_completar, registrador
        )

        resultado['con_estadisticas'] += completar['con_estadisticas']
        resultado['errores'] += completar['errores']

        logger.info(
            f"Estadísticas completadas: "
            f"{completar['con_estadisticas']}/{completar['procesados']} "
            f"err:{completar['errores']}"
        )

    # Calcular estadísticas agregadas
    if args.calcular_agregados:
        logger.info("Calculando estadísticas agregadas...")
        stats_resultado = actualizar_estadisticas_todos_equipos(
            conexion, competicion_id, temporada_id
        )
        logger.info(
            f"Equipos actualizados: {stats_resultado['actualizados']}"
        )

    return resultado


def main():
    """Función principal del script."""
    args = parsear_argumentos()

    # Configurar logging
    nivel = logging.DEBUG if args.verbose else logging.INFO
    configurar_logging(nivel=nivel)

    logger.info("=" * 60)
    logger.info("SINCRONIZACIÓN DE DATOS DE FÚTBOL - SOFASCORE")
    logger.info("=" * 60)
    logger.info(f"Días hacia atrás: {args.dias}")
    logger.info(f"Incluir futuros: {args.incluir_futuros and not args.no_futuros}")

    # Obtener ligas a procesar
    try:
        ligas = obtener_ligas_a_procesar(args.liga)
        logger.info(f"Ligas a procesar: {', '.join(ligas)}")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Conectar a BD
    try:
        pool = obtener_pool()
        conexion = pool.getconn()
        logger.info("Conexión a BD establecida")
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")
        sys.exit(1)

    # Crear cliente Sofascore
    cliente = SofascoreClient()

    # Crear registrador de ingesta
    registrador = RegistradorIngesta(conexion)

    # Resumen total
    resumen_total = {
        'ligas_procesadas': 0,
        'partidos_procesados': 0,
        'insertados': 0,
        'actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0,
    }

    inicio = datetime.now()

    try:
        for codigo_liga in ligas:
            registrador.iniciar_sesion(
                'sincronizacion',
                liga_id=LIGAS_SOFASCORE[codigo_liga]
            )

            resultado = procesar_liga(
                conexion, cliente, codigo_liga, args, registrador
            )

            resumen_total['ligas_procesadas'] += 1
            resumen_total['partidos_procesados'] += resultado['partidos_procesados']
            resumen_total['insertados'] += resultado['insertados']
            resumen_total['actualizados'] += resultado['actualizados']
            resumen_total['con_estadisticas'] += resultado['con_estadisticas']
            resumen_total['errores'] += resultado['errores']

            registrador.finalizar_sesion()
            limpiar_cache()

    except KeyboardInterrupt:
        logger.warning("\n\nInterrumpido por usuario")
        registrador.finalizar_sesion()

    except Exception as e:
        logger.error(f"Error durante la sincronización: {e}")
        import traceback
        traceback.print_exc()
        registrador.registrar_error(e)
        registrador.finalizar_sesion()

    finally:
        # Cerrar conexiones
        cliente.cerrar()
        pool.putconn(conexion)
        cerrar_pool()

    # Mostrar resumen
    duracion = (datetime.now() - inicio).total_seconds()

    print("\n" + "=" * 60)
    print("RESUMEN DE SINCRONIZACIÓN")
    print("=" * 60)
    print(f"Duración: {duracion:.1f} segundos")
    print(f"Ligas procesadas: {resumen_total['ligas_procesadas']}")
    print(f"Partidos procesados: {resumen_total['partidos_procesados']}")
    print(f"Insertados: {resumen_total['insertados']}")
    print(f"Actualizados: {resumen_total['actualizados']}")
    print(f"Con estadísticas: {resumen_total['con_estadisticas']}")
    print(f"Errores: {resumen_total['errores']}")
    print("=" * 60)

    sys.exit(0 if resumen_total['errores'] == 0 else 1)


if __name__ == '__main__':
    main()
