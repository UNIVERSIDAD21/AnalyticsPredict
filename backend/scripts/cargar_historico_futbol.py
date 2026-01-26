#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de carga histórica de datos de fútbol desde Sofascore.

Este script permite cargar datos históricos de partidos de fútbol
para las principales ligas europeas, incluyendo estadísticas detalladas
como corners, disparos, posesión y xG.

Uso:
    python cargar_historico_futbol.py --liga laliga --temporadas 2024-25,2023-24
    python cargar_historico_futbol.py --liga todas --temporadas 2024-25 --verbose
    python cargar_historico_futbol.py --liga premier --solo-finalizados --sin-estadisticas

Argumentos:
    --liga: Código de liga (laliga, premier, bundesliga, seriea, ligue1) o "todas"
    --temporadas: Lista de temporadas separadas por coma (ej: "2023-24,2024-25")
    --desde-fecha: Fecha mínima en formato YYYY-MM-DD
    --hasta-fecha: Fecha máxima en formato YYYY-MM-DD
    --solo-finalizados: Solo procesar partidos terminados
    --con-estadisticas: Obtener estadísticas detalladas (default: True)
    --sin-estadisticas: Omitir estadísticas detalladas
    --dry-run: Simular sin guardar en BD
    --verbose: Mostrar información detallada
    --checkpoint-file: Archivo para guardar progreso
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Añadir el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import obtener_pool, cerrar_pool
from scrapers.sofascore.cliente import SofascoreClient
from scrapers.sofascore.temporadas import (
    obtener_temporadas_liga,
    sincronizar_temporadas,
)
from scrapers.sofascore.equipos import sincronizar_equipos
from scrapers.sofascore.partidos import (
    obtener_partidos_pasados,
    obtener_partidos_futuros,
    filtrar_partidos_finalizados,
)
from scrapers.sofascore.sincronizador import (
    sincronizar_lote_partidos,
    resolver_competicion_id,
    resolver_temporada_id_por_sofascore,
    limpiar_cache,
)
from scrapers.sofascore.calculador_estadisticas import (
    actualizar_estadisticas_todos_equipos,
)
from scrapers.sofascore.monitoreo import (
    configurar_logging,
    RegistradorIngesta,
)

# Mapeo de códigos de liga a IDs de Sofascore
LIGAS_SOFASCORE = {
    'laliga': 8,
    'premier': 17,
    'bundesliga': 35,
    'seriea': 23,
    'ligue1': 34,
    'champions': 7,
    'europa': 679,
    'conference': 17015,
    'copa_rey': 329,
    'fa_cup': 29,
    'dfb_pokal': 44,
    'coppa_italia': 327,
    'coupe_france': 335,
}

# Mapeo de códigos de liga a códigos internos
CODIGOS_COMPETICION = {
    'laliga': 'ESP_LALIGA',
    'premier': 'ENG_PREMIER',
    'bundesliga': 'GER_BUNDESLIGA',
    'seriea': 'ITA_SERIEA',
    'ligue1': 'FRA_LIGUE1',
    'champions': 'EUR_CHAMPIONS',
    'europa': 'EUR_EUROPA',
    'conference': 'EUR_CONFERENCE',
    'copa_rey': 'ESP_COPA',
    'fa_cup': 'ENG_FACUP',
    'dfb_pokal': 'GER_DFBPOKAL',
    'coppa_italia': 'ITA_COPPA',
    'coupe_france': 'FRA_COUPE',
}

logger = logging.getLogger(__name__)


class GestorCheckpoint:
    """Gestiona el guardado y carga de checkpoints para reanudar cargas."""

    def __init__(self, archivo: Optional[str] = None):
        self.archivo = archivo
        self.datos: Dict[str, Any] = {
            'liga_actual': None,
            'temporada_actual': None,
            'ultimo_partido_procesado': None,
            'partidos_procesados': set(),
            'fecha_inicio': None,
        }

    def cargar(self) -> bool:
        """Carga checkpoint desde archivo. Retorna True si se cargó."""
        if not self.archivo or not os.path.exists(self.archivo):
            return False

        try:
            with open(self.archivo, 'r') as f:
                datos = json.load(f)
                self.datos = datos
                self.datos['partidos_procesados'] = set(
                    datos.get('partidos_procesados', [])
                )
                logger.info(f"Checkpoint cargado desde {self.archivo}")
                return True
        except Exception as e:
            logger.warning(f"Error cargando checkpoint: {e}")
            return False

    def guardar(self) -> None:
        """Guarda checkpoint a archivo."""
        if not self.archivo:
            return

        try:
            datos_guardar = self.datos.copy()
            datos_guardar['partidos_procesados'] = list(
                self.datos['partidos_procesados']
            )
            with open(self.archivo, 'w') as f:
                json.dump(datos_guardar, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Error guardando checkpoint: {e}")

    def registrar_partido(self, partido_id: int) -> None:
        """Registra un partido como procesado."""
        self.datos['partidos_procesados'].add(partido_id)
        self.datos['ultimo_partido_procesado'] = partido_id

    def partido_procesado(self, partido_id: int) -> bool:
        """Verifica si un partido ya fue procesado."""
        return partido_id in self.datos['partidos_procesados']

    def actualizar_posicion(
        self,
        liga: Optional[str] = None,
        temporada: Optional[str] = None
    ) -> None:
        """Actualiza la posición actual de procesamiento."""
        if liga:
            self.datos['liga_actual'] = liga
        if temporada:
            self.datos['temporada_actual'] = temporada
        self.guardar()

    def limpiar(self) -> None:
        """Limpia el checkpoint al finalizar exitosamente."""
        if self.archivo and os.path.exists(self.archivo):
            os.remove(self.archivo)
            logger.info("Checkpoint eliminado")


def parsear_argumentos() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Carga histórica de datos de fútbol desde Sofascore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s --liga laliga --temporadas 2024-25
  %(prog)s --liga todas --temporadas 2024-25,2023-24 --verbose
  %(prog)s --liga premier --desde-fecha 2024-01-01 --solo-finalizados
  %(prog)s --liga laliga --dry-run --verbose
        """
    )

    parser.add_argument(
        '--liga',
        type=str,
        required=True,
        help='Código de liga (laliga, premier, bundesliga, seriea, ligue1) o "todas"'
    )

    parser.add_argument(
        '--temporadas',
        type=str,
        default=None,
        help='Temporadas separadas por coma (ej: "2024-25,2023-24"). '
             'Si no se especifica, se cargan todas las disponibles.'
    )

    parser.add_argument(
        '--desde-fecha',
        type=str,
        default=None,
        help='Fecha mínima en formato YYYY-MM-DD'
    )

    parser.add_argument(
        '--hasta-fecha',
        type=str,
        default=None,
        help='Fecha máxima en formato YYYY-MM-DD'
    )

    parser.add_argument(
        '--solo-finalizados',
        action='store_true',
        help='Solo procesar partidos terminados'
    )

    parser.add_argument(
        '--con-estadisticas',
        action='store_true',
        default=True,
        help='Obtener estadísticas detalladas (default)'
    )

    parser.add_argument(
        '--sin-estadisticas',
        action='store_true',
        help='No obtener estadísticas detalladas'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular sin guardar en BD'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )

    parser.add_argument(
        '--checkpoint-file',
        type=str,
        default=None,
        help='Archivo para guardar/cargar progreso'
    )

    parser.add_argument(
        '--calcular-agregados',
        action='store_true',
        default=True,
        help='Calcular estadísticas agregadas de equipos al finalizar'
    )

    parser.add_argument(
        '--limite-paginas',
        type=int,
        default=50,
        help='Límite de páginas a consultar por temporada (default: 50)'
    )

    return parser.parse_args()


def obtener_ligas_a_procesar(codigo_liga: str) -> List[str]:
    """Obtiene lista de códigos de liga a procesar."""
    if codigo_liga.lower() == 'todas':
        # Solo las principales para carga masiva
        return ['laliga', 'premier', 'bundesliga', 'seriea', 'ligue1']
    elif codigo_liga.lower() in LIGAS_SOFASCORE:
        return [codigo_liga.lower()]
    else:
        raise ValueError(
            f"Liga '{codigo_liga}' no reconocida. "
            f"Opciones: {', '.join(LIGAS_SOFASCORE.keys())}, todas"
        )


def procesar_liga(
    conexion,
    cliente: SofascoreClient,
    codigo_liga: str,
    temporadas_solicitadas: Optional[List[str]],
    args: argparse.Namespace,
    checkpoint: GestorCheckpoint,
    registrador: RegistradorIngesta
) -> Dict[str, Any]:
    """
    Procesa una liga completa.

    Returns:
        Diccionario con resumen del procesamiento.
    """
    liga_id = LIGAS_SOFASCORE[codigo_liga]
    codigo_competicion = CODIGOS_COMPETICION.get(codigo_liga)

    logger.info(f"\n{'='*60}")
    logger.info(f"Procesando: {codigo_liga.upper()} (Sofascore ID: {liga_id})")
    logger.info(f"{'='*60}")

    resultado = {
        'liga': codigo_liga,
        'temporadas_procesadas': 0,
        'partidos_insertados': 0,
        'partidos_actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0,
    }

    # Obtener competicion_id de la BD
    competicion_id = resolver_competicion_id(conexion, liga_id)

    if competicion_id is None:
        logger.error(
            f"Competición {codigo_liga} no encontrada en BD. "
            f"Ejecuta primero actualizar_ids_sofascore.py"
        )
        resultado['errores'] += 1
        return resultado

    # Sincronizar temporadas
    logger.info("Sincronizando temporadas...")
    sync_temps = sincronizar_temporadas(
        conexion, cliente, liga_id, competicion_id,
        temporadas_solicitadas
    )
    logger.info(
        f"Temporadas: {sync_temps['insertadas']} nuevas, "
        f"{sync_temps['actualizadas']} actualizadas"
    )

    # Obtener temporadas de Sofascore para iterar
    temporadas = obtener_temporadas_liga(cliente, liga_id)

    # Filtrar por temporadas solicitadas
    if temporadas_solicitadas:
        temporadas = [
            t for t in temporadas
            if t['nombre_normalizado'] in temporadas_solicitadas
        ]

    if not temporadas:
        logger.warning(f"No hay temporadas para procesar en {codigo_liga}")
        return resultado

    # Parsear fechas
    desde_fecha = None
    hasta_fecha = None
    if args.desde_fecha:
        desde_fecha = datetime.strptime(args.desde_fecha, '%Y-%m-%d')
    if args.hasta_fecha:
        hasta_fecha = datetime.strptime(args.hasta_fecha, '%Y-%m-%d')

    # Procesar cada temporada
    for temporada in temporadas:
        temp_nombre = temporada['nombre_normalizado']
        temp_sofascore_id = temporada['id']

        # Verificar checkpoint
        if (checkpoint.datos.get('liga_actual') == codigo_liga and
            checkpoint.datos.get('temporada_actual') and
            temp_nombre < checkpoint.datos['temporada_actual']):
            logger.info(f"Saltando temporada {temp_nombre} (checkpoint)")
            continue

        logger.info(f"\n--- Temporada {temp_nombre} ---")
        checkpoint.actualizar_posicion(liga=codigo_liga, temporada=temp_nombre)

        # Obtener temporada_id de la BD
        temporada_id = resolver_temporada_id_por_sofascore(
            conexion, competicion_id, temp_sofascore_id
        )

        if temporada_id is None:
            logger.warning(
                f"Temporada {temp_nombre} no encontrada en BD. Saltando."
            )
            continue

        # Sincronizar equipos
        logger.info("Sincronizando equipos...")
        sync_equipos = sincronizar_equipos(
            conexion, cliente, liga_id, temp_sofascore_id, competicion_id
        )
        logger.info(
            f"Equipos: {sync_equipos['insertados']} nuevos, "
            f"{sync_equipos['actualizados']} actualizados "
            f"(fuente: {sync_equipos['fuente']})"
        )

        # Obtener partidos pasados
        logger.info("Obteniendo partidos...")
        partidos = obtener_partidos_pasados(
            cliente, liga_id, temp_sofascore_id,
            desde_fecha=desde_fecha,
            hasta_fecha=hasta_fecha,
            limite_paginas=args.limite_paginas
        )

        logger.info(f"Encontrados {len(partidos)} partidos")

        # Filtrar solo finalizados si se especificó
        if args.solo_finalizados:
            partidos = filtrar_partidos_finalizados(partidos)
            logger.info(f"Después de filtrar finalizados: {len(partidos)}")

        # Filtrar partidos ya procesados (checkpoint)
        partidos_nuevos = [
            p for p in partidos
            if not checkpoint.partido_procesado(p.sofascore_id)
        ]

        if len(partidos_nuevos) < len(partidos):
            logger.info(
                f"Saltando {len(partidos) - len(partidos_nuevos)} "
                f"partidos ya procesados (checkpoint)"
            )
            partidos = partidos_nuevos

        if not partidos:
            logger.info("No hay partidos nuevos para procesar")
            resultado['temporadas_procesadas'] += 1
            continue

        # Sincronizar partidos
        if args.dry_run:
            logger.info(f"[DRY-RUN] Se procesarían {len(partidos)} partidos")
            resultado['temporadas_procesadas'] += 1
            continue

        obtener_stats = args.con_estadisticas and not args.sin_estadisticas

        def callback_progreso(actual, total, partido):
            if args.verbose or actual % 10 == 0:
                print(
                    f"\r  Procesando: {actual}/{total} "
                    f"({partido.equipo_local_nombre[:15]} vs "
                    f"{partido.equipo_visitante_nombre[:15]})",
                    end='', flush=True
                )
            checkpoint.registrar_partido(partido.sofascore_id)
            registrador.registrar_partido(
                partido.sofascore_id,
                fue_insercion=True,
                tiene_estadisticas=obtener_stats
            )

        sync_resultado = sincronizar_lote_partidos(
            conexion, cliente, partidos, liga_id,
            temporada_id=temporada_id,
            competicion_id=competicion_id,
            obtener_estadisticas_flag=obtener_stats,
            callback_progreso=callback_progreso
        )

        print()  # Nueva línea después del progreso

        resultado['partidos_insertados'] += sync_resultado['insertados']
        resultado['partidos_actualizados'] += sync_resultado['actualizados']
        resultado['con_estadisticas'] += sync_resultado['con_estadisticas']
        resultado['errores'] += sync_resultado['errores']
        resultado['temporadas_procesadas'] += 1

        logger.info(
            f"Temporada completada: "
            f"+{sync_resultado['insertados']} "
            f"~{sync_resultado['actualizados']} "
            f"stats:{sync_resultado['con_estadisticas']} "
            f"err:{sync_resultado['errores']}"
        )

        # Guardar checkpoint
        checkpoint.guardar()

    # Calcular estadísticas agregadas
    if args.calcular_agregados and not args.dry_run:
        logger.info("\nCalculando estadísticas agregadas de equipos...")
        for temporada in temporadas[:2]:  # Solo últimas 2 temporadas
            temp_nombre = temporada['nombre_normalizado']
            temporada_id = resolver_temporada_id_por_sofascore(
                conexion, competicion_id, temporada['id']
            )
            if temporada_id:
                stats_resultado = actualizar_estadisticas_todos_equipos(
                    conexion, competicion_id, temporada_id
                )
                logger.info(
                    f"  {temp_nombre}: {stats_resultado['actualizados']} equipos actualizados"
                )

    return resultado


def main():
    """Función principal del script."""
    args = parsear_argumentos()

    # Configurar logging
    nivel = logging.DEBUG if args.verbose else logging.INFO
    configurar_logging(nivel=nivel)

    logger.info("=" * 60)
    logger.info("CARGA HISTÓRICA DE DATOS DE FÚTBOL - SOFASCORE")
    logger.info("=" * 60)

    # Parsear temporadas
    temporadas_solicitadas = None
    if args.temporadas:
        temporadas_solicitadas = [t.strip() for t in args.temporadas.split(',')]
        logger.info(f"Temporadas solicitadas: {temporadas_solicitadas}")

    # Obtener ligas a procesar
    try:
        ligas = obtener_ligas_a_procesar(args.liga)
        logger.info(f"Ligas a procesar: {', '.join(ligas)}")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Gestionar checkpoint
    checkpoint = GestorCheckpoint(args.checkpoint_file)

    if args.checkpoint_file:
        if checkpoint.cargar():
            respuesta = input(
                f"Se encontró checkpoint. ¿Continuar desde donde quedó? (s/n): "
            )
            if respuesta.lower() != 's':
                checkpoint.datos['partidos_procesados'] = set()
                logger.info("Reiniciando desde el principio")

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
        'temporadas_procesadas': 0,
        'partidos_insertados': 0,
        'partidos_actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0,
    }

    inicio = datetime.now()

    try:
        for codigo_liga in ligas:
            registrador.iniciar_sesion(
                'historico',
                liga_id=LIGAS_SOFASCORE[codigo_liga]
            )

            resultado = procesar_liga(
                conexion, cliente, codigo_liga,
                temporadas_solicitadas, args,
                checkpoint, registrador
            )

            resumen_total['ligas_procesadas'] += 1
            resumen_total['temporadas_procesadas'] += resultado['temporadas_procesadas']
            resumen_total['partidos_insertados'] += resultado['partidos_insertados']
            resumen_total['partidos_actualizados'] += resultado['partidos_actualizados']
            resumen_total['con_estadisticas'] += resultado['con_estadisticas']
            resumen_total['errores'] += resultado['errores']

            registrador.finalizar_sesion()
            limpiar_cache()

    except KeyboardInterrupt:
        logger.warning("\n\nInterrumpido por usuario. Guardando checkpoint...")
        checkpoint.guardar()
        registrador.finalizar_sesion()

    except Exception as e:
        logger.error(f"Error durante la carga: {e}")
        import traceback
        traceback.print_exc()
        checkpoint.guardar()
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
    print("RESUMEN DE CARGA HISTÓRICA")
    print("=" * 60)
    print(f"Duración: {duracion/60:.1f} minutos")
    print(f"Ligas procesadas: {resumen_total['ligas_procesadas']}")
    print(f"Temporadas procesadas: {resumen_total['temporadas_procesadas']}")
    print(f"Partidos insertados: {resumen_total['partidos_insertados']}")
    print(f"Partidos actualizados: {resumen_total['partidos_actualizados']}")
    print(f"Con estadísticas: {resumen_total['con_estadisticas']}")
    print(f"Errores: {resumen_total['errores']}")
    print("=" * 60)

    # Limpiar checkpoint si todo fue exitoso
    if resumen_total['errores'] == 0:
        checkpoint.limpiar()
        logger.info("Carga completada exitosamente")
    else:
        logger.warning(f"Carga completada con {resumen_total['errores']} errores")

    sys.exit(0 if resumen_total['errores'] == 0 else 1)


if __name__ == '__main__':
    main()
