# -*- coding: utf-8 -*-
"""
Sistema de monitoreo y logging para la ingesta de datos de Sofascore.

Este módulo proporciona herramientas para:
- Configuración centralizada de logging
- Registro de métricas de cada sesión de ingesta
- Detección de anomalías en los datos
- Generación de reportes de estado

Componentes principales:
- configurar_logging: Configura el sistema de logging
- RegistradorIngesta: Clase para registrar métricas de sesión
- detectar_anomalias: Detecta problemas en los datos
- generar_reporte_estado: Genera reporte de cobertura

Ejemplo de uso:
    from scrapers.sofascore.monitoreo import (
        configurar_logging,
        RegistradorIngesta
    )

    configurar_logging(nivel=logging.INFO, archivo_log='ingesta.log')

    registrador = RegistradorIngesta(conexion)
    registrador.iniciar_sesion('historico', liga_id=8)

    # ... procesar partidos ...
    registrador.registrar_partido(partido_id, fue_insercion=True)

    registrador.finalizar_sesion()
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional

from .excepciones import ErrorBaseDatos

# Logger del módulo
logger = logging.getLogger(__name__)


def configurar_logging(
    nivel: int = logging.INFO,
    archivo_log: Optional[str] = None,
    formato: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """
    Configura el sistema de logging para el módulo de Sofascore.

    Configura logging tanto a consola como opcionalmente a archivo,
    con rotación automática de archivos.

    Args:
        nivel: Nivel de logging (logging.DEBUG, INFO, WARNING, ERROR).
        archivo_log: Ruta del archivo de log (opcional).
        formato: Formato personalizado del log (opcional).
        max_bytes: Tamaño máximo del archivo antes de rotar (default: 10MB).
        backup_count: Número de archivos de backup a mantener (default: 5).

    Ejemplo:
        # Configuración básica
        configurar_logging(nivel=logging.INFO)

        # Con archivo de log
        configurar_logging(
            nivel=logging.DEBUG,
            archivo_log='logs/sofascore.log'
        )
    """
    if formato is None:
        formato = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"

    # Configurar logger raíz del módulo
    logger_sofascore = logging.getLogger('scrapers.sofascore')
    logger_sofascore.setLevel(nivel)

    # Limpiar handlers existentes
    logger_sofascore.handlers.clear()

    # Crear formatter
    formatter = logging.Formatter(formato, datefmt='%Y-%m-%d %H:%M:%S')

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(nivel)
    console_handler.setFormatter(formatter)
    logger_sofascore.addHandler(console_handler)

    # Handler para archivo con rotación
    if archivo_log:
        try:
            file_handler = RotatingFileHandler(
                archivo_log,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(nivel)
            file_handler.setFormatter(formatter)
            logger_sofascore.addHandler(file_handler)

            logger.info(f"Logging configurado. Archivo: {archivo_log}")
        except Exception as e:
            logger.warning(f"No se pudo configurar archivo de log: {e}")

    logger.debug(f"Nivel de logging: {logging.getLevelName(nivel)}")


class RegistradorIngesta:
    """
    Registra métricas de cada sesión de ingesta de datos.

    Esta clase mantiene contadores y registra el progreso de cada
    sesión de ingesta, guardando un resumen en la base de datos
    al finalizar.

    Atributos:
        conexion: Conexión a la base de datos.
        sesion_activa: True si hay una sesión en curso.
        tipo_ejecucion: 'historico' o 'sincronizacion'.
        liga_id: ID de la liga procesada.

    Ejemplo:
        registrador = RegistradorIngesta(conexion)
        registrador.iniciar_sesion('sincronizacion', liga_id=8)

        for partido in partidos:
            try:
                # procesar partido...
                registrador.registrar_partido(partido_id, True)
            except Exception as e:
                registrador.registrar_error(e, {'partido': partido_id})

        registrador.finalizar_sesion()
    """

    def __init__(self, conexion):
        """
        Inicializa el registrador de ingesta.

        Args:
            conexion: Conexión a la base de datos PostgreSQL.
        """
        self.conexion = conexion
        self.sesion_activa = False
        self.tipo_ejecucion: Optional[str] = None
        self.liga_id: Optional[int] = None
        self.competicion_id: Optional[int] = None

        # Contadores
        self.partidos_insertados = 0
        self.partidos_actualizados = 0
        self.partidos_con_estadisticas = 0
        self.errores = 0

        # Detalles
        self.inicio_sesion: Optional[datetime] = None
        self.errores_detalle: List[Dict[str, Any]] = []

        # Asegurar que existe la tabla
        self._crear_tabla_si_no_existe()

    def _crear_tabla_si_no_existe(self) -> None:
        """Crea la tabla de estado de ingesta si no existe."""
        try:
            with self.conexion.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ingestion_state_futbol (
                        id SERIAL PRIMARY KEY,
                        fecha_ejecucion TIMESTAMPTZ DEFAULT NOW(),
                        tipo_ejecucion VARCHAR(20) NOT NULL,
                        liga_id INTEGER,
                        competicion_id INTEGER,
                        partidos_insertados INTEGER DEFAULT 0,
                        partidos_actualizados INTEGER DEFAULT 0,
                        partidos_con_estadisticas INTEGER DEFAULT 0,
                        errores INTEGER DEFAULT 0,
                        duracion_segundos NUMERIC(10, 2),
                        estado VARCHAR(20) DEFAULT 'en_progreso',
                        detalle_errores JSONB,
                        creado_en TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
                self.conexion.commit()
        except Exception as e:
            logger.warning(f"No se pudo crear tabla de monitoreo: {e}")

    def iniciar_sesion(
        self,
        tipo_ejecucion: str,
        liga_id: Optional[int] = None,
        competicion_id: Optional[int] = None
    ) -> None:
        """
        Inicia una nueva sesión de ingesta.

        Args:
            tipo_ejecucion: 'historico' o 'sincronizacion'.
            liga_id: ID de la liga en Sofascore (opcional).
            competicion_id: ID de la competición en BD (opcional).
        """
        if self.sesion_activa:
            logger.warning("Ya hay una sesión activa. Finalizando anterior.")
            self.finalizar_sesion()

        self.sesion_activa = True
        self.tipo_ejecucion = tipo_ejecucion
        self.liga_id = liga_id
        self.competicion_id = competicion_id
        self.inicio_sesion = datetime.now()

        # Reiniciar contadores
        self.partidos_insertados = 0
        self.partidos_actualizados = 0
        self.partidos_con_estadisticas = 0
        self.errores = 0
        self.errores_detalle = []

        logger.info(
            f"Sesión de ingesta iniciada: tipo={tipo_ejecucion}, "
            f"liga_id={liga_id}"
        )

    def registrar_partido(
        self,
        partido_id: int,
        fue_insercion: bool,
        tiene_estadisticas: bool = False,
        tuvo_error: bool = False
    ) -> None:
        """
        Registra el procesamiento de un partido.

        Args:
            partido_id: ID del partido procesado.
            fue_insercion: True si fue inserción, False si actualización.
            tiene_estadisticas: True si se guardaron estadísticas.
            tuvo_error: True si hubo error procesando el partido.
        """
        if not self.sesion_activa:
            return

        if tuvo_error:
            self.errores += 1
        elif fue_insercion:
            self.partidos_insertados += 1
        else:
            self.partidos_actualizados += 1

        if tiene_estadisticas:
            self.partidos_con_estadisticas += 1

    def registrar_error(
        self,
        error: Exception,
        contexto: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra un error durante la ingesta.

        Args:
            error: Excepción que ocurrió.
            contexto: Diccionario con información de contexto.
        """
        if not self.sesion_activa:
            return

        self.errores += 1

        detalle = {
            'timestamp': datetime.now().isoformat(),
            'tipo_error': type(error).__name__,
            'mensaje': str(error),
            'contexto': contexto or {},
        }

        self.errores_detalle.append(detalle)
        logger.error(f"Error en ingesta: {error}")

    def finalizar_sesion(self) -> Dict[str, Any]:
        """
        Finaliza la sesión actual y guarda resumen en BD.

        Returns:
            Diccionario con resumen de la sesión.
        """
        if not self.sesion_activa:
            return {}

        fin_sesion = datetime.now()
        duracion = (fin_sesion - self.inicio_sesion).total_seconds()

        # Determinar estado
        if self.errores == 0:
            estado = 'exitoso'
        elif self.partidos_insertados + self.partidos_actualizados > 0:
            estado = 'parcial'
        else:
            estado = 'fallido'

        resumen = {
            'tipo_ejecucion': self.tipo_ejecucion,
            'liga_id': self.liga_id,
            'competicion_id': self.competicion_id,
            'partidos_insertados': self.partidos_insertados,
            'partidos_actualizados': self.partidos_actualizados,
            'partidos_con_estadisticas': self.partidos_con_estadisticas,
            'errores': self.errores,
            'duracion_segundos': duracion,
            'estado': estado,
        }

        # Guardar en BD
        try:
            with self.conexion.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ingestion_state_futbol (
                        tipo_ejecucion, liga_id, competicion_id,
                        partidos_insertados, partidos_actualizados,
                        partidos_con_estadisticas, errores,
                        duracion_segundos, estado, detalle_errores
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.tipo_ejecucion,
                        self.liga_id,
                        self.competicion_id,
                        self.partidos_insertados,
                        self.partidos_actualizados,
                        self.partidos_con_estadisticas,
                        self.errores,
                        duracion,
                        estado,
                        json.dumps(self.errores_detalle) if self.errores_detalle else None
                    )
                )
                self.conexion.commit()
        except Exception as e:
            logger.warning(f"No se pudo guardar resumen de sesión: {e}")

        self.sesion_activa = False

        logger.info(
            f"Sesión finalizada: {estado} - "
            f"{self.partidos_insertados} insertados, "
            f"{self.partidos_actualizados} actualizados, "
            f"{self.errores} errores, "
            f"{duracion:.1f}s"
        )

        return resumen


def detectar_anomalias(
    conexion,
    dias_sin_partidos: int = 14,
    umbral_tasa_errores: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Detecta anomalías en los datos de ingesta.

    Verifica:
    - Ligas sin partidos nuevos cuando debería haber
    - Tasa de errores alta en últimas ejecuciones
    - Partidos finalizados sin estadísticas

    Args:
        conexion: Conexión a la base de datos.
        dias_sin_partidos: Días sin partidos nuevos para alertar.
        umbral_tasa_errores: Tasa de errores para alertar (0-1).

    Returns:
        Lista de anomalías detectadas, cada una como diccionario con:
        - tipo: Tipo de anomalía
        - descripcion: Descripción del problema
        - severidad: 'baja', 'media', 'alta'
        - detalles: Información adicional
    """
    anomalias = []

    try:
        with conexion.cursor() as cursor:
            # 1. Verificar ligas sin partidos recientes
            cursor.execute(
                """
                SELECT c.id, c.nombre, c.codigo,
                       MAX(p.fecha_partido) as ultimo_partido
                FROM competiciones_futbol c
                LEFT JOIN partidos_futbol p ON p.competicion_id = c.id
                WHERE c.activa = TRUE
                GROUP BY c.id, c.nombre, c.codigo
                HAVING MAX(p.fecha_partido) < NOW() - INTERVAL '%s days'
                   OR MAX(p.fecha_partido) IS NULL
                """,
                (dias_sin_partidos,)
            )

            for row in cursor.fetchall():
                anomalias.append({
                    'tipo': 'LIGA_SIN_PARTIDOS_RECIENTES',
                    'descripcion': f"Liga {row[1]} sin partidos en los últimos {dias_sin_partidos} días",
                    'severidad': 'media',
                    'detalles': {
                        'competicion_id': row[0],
                        'codigo': row[2],
                        'ultimo_partido': row[3].isoformat() if row[3] else None,
                    }
                })

            # 2. Verificar tasa de errores alta
            cursor.execute(
                """
                SELECT
                    SUM(errores) as total_errores,
                    SUM(partidos_insertados + partidos_actualizados) as total_partidos
                FROM ingestion_state_futbol
                WHERE fecha_ejecucion > NOW() - INTERVAL '7 days'
                """
            )
            row = cursor.fetchone()

            if row and row[1] and row[1] > 0:
                tasa_errores = row[0] / row[1] if row[0] else 0
                if tasa_errores > umbral_tasa_errores:
                    anomalias.append({
                        'tipo': 'TASA_ERRORES_ALTA',
                        'descripcion': f"Tasa de errores del {tasa_errores*100:.1f}% en últimos 7 días",
                        'severidad': 'alta',
                        'detalles': {
                            'errores': row[0],
                            'partidos': row[1],
                            'tasa': tasa_errores,
                        }
                    })

            # 3. Verificar partidos finalizados sin estadísticas
            cursor.execute(
                """
                SELECT COUNT(*) as sin_stats
                FROM partidos_futbol
                WHERE estado = 'finished'
                  AND corners_local_total IS NULL
                  AND fecha_partido > NOW() - INTERVAL '90 days'
                """
            )
            row = cursor.fetchone()

            if row and row[0] > 50:
                anomalias.append({
                    'tipo': 'PARTIDOS_SIN_ESTADISTICAS',
                    'descripcion': f"{row[0]} partidos finalizados sin estadísticas",
                    'severidad': 'baja',
                    'detalles': {
                        'cantidad': row[0],
                    }
                })

    except Exception as e:
        logger.error(f"Error detectando anomalías: {e}")

    return anomalias


def generar_reporte_estado(conexion) -> Dict[str, Any]:
    """
    Genera un reporte completo del estado de los datos.

    Incluye:
    - Número de partidos por competición y temporada
    - Porcentaje de partidos con estadísticas completas
    - Última actualización por competición
    - Anomalías detectadas

    Args:
        conexion: Conexión a la base de datos.

    Returns:
        Diccionario con toda la información del reporte.
    """
    reporte = {
        'fecha_generacion': datetime.now().isoformat(),
        'competiciones': [],
        'resumen_global': {},
        'anomalias': [],
        'ultimas_ejecuciones': [],
    }

    try:
        with conexion.cursor() as cursor:
            # Estadísticas por competición
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.nombre,
                    c.codigo,
                    t.nombre as temporada,
                    COUNT(p.id) as total_partidos,
                    SUM(CASE WHEN p.estado = 'finished' THEN 1 ELSE 0 END) as finalizados,
                    SUM(CASE WHEN p.corners_local_total IS NOT NULL THEN 1 ELSE 0 END) as con_corners,
                    SUM(CASE WHEN p.xg_local IS NOT NULL THEN 1 ELSE 0 END) as con_xg,
                    MAX(p.fecha_partido) as ultimo_partido,
                    MAX(p.actualizado_en) as ultima_actualizacion
                FROM competiciones_futbol c
                LEFT JOIN temporadas_futbol t ON t.competicion_id = c.id AND t.activa = TRUE
                LEFT JOIN partidos_futbol p ON p.competicion_id = c.id AND p.temporada_id = t.id
                WHERE c.activa = TRUE
                GROUP BY c.id, c.nombre, c.codigo, t.nombre
                ORDER BY c.nombre
                """
            )

            total_partidos = 0
            total_con_stats = 0

            for row in cursor.fetchall():
                comp_stats = {
                    'id': row[0],
                    'nombre': row[1],
                    'codigo': row[2],
                    'temporada_activa': row[3],
                    'total_partidos': row[4] or 0,
                    'partidos_finalizados': row[5] or 0,
                    'partidos_con_corners': row[6] or 0,
                    'partidos_con_xg': row[7] or 0,
                    'ultimo_partido': row[8].isoformat() if row[8] else None,
                    'ultima_actualizacion': row[9].isoformat() if row[9] else None,
                }

                # Calcular porcentajes
                if comp_stats['partidos_finalizados'] > 0:
                    comp_stats['porcentaje_corners'] = round(
                        comp_stats['partidos_con_corners'] / comp_stats['partidos_finalizados'] * 100, 1
                    )
                    comp_stats['porcentaje_xg'] = round(
                        comp_stats['partidos_con_xg'] / comp_stats['partidos_finalizados'] * 100, 1
                    )
                else:
                    comp_stats['porcentaje_corners'] = 0
                    comp_stats['porcentaje_xg'] = 0

                reporte['competiciones'].append(comp_stats)

                total_partidos += comp_stats['total_partidos']
                total_con_stats += comp_stats['partidos_con_corners']

            # Resumen global
            reporte['resumen_global'] = {
                'total_partidos': total_partidos,
                'partidos_con_estadisticas': total_con_stats,
                'porcentaje_cobertura': round(
                    total_con_stats / total_partidos * 100, 1
                ) if total_partidos > 0 else 0,
            }

            # Últimas ejecuciones
            cursor.execute(
                """
                SELECT
                    fecha_ejecucion,
                    tipo_ejecucion,
                    liga_id,
                    partidos_insertados,
                    partidos_actualizados,
                    errores,
                    duracion_segundos,
                    estado
                FROM ingestion_state_futbol
                ORDER BY fecha_ejecucion DESC
                LIMIT 10
                """
            )

            for row in cursor.fetchall():
                reporte['ultimas_ejecuciones'].append({
                    'fecha': row[0].isoformat() if row[0] else None,
                    'tipo': row[1],
                    'liga_id': row[2],
                    'insertados': row[3],
                    'actualizados': row[4],
                    'errores': row[5],
                    'duracion': float(row[6]) if row[6] else None,
                    'estado': row[7],
                })

        # Detectar anomalías
        reporte['anomalias'] = detectar_anomalias(conexion)

    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        reporte['error'] = str(e)

    return reporte


def imprimir_reporte_estado(conexion) -> None:
    """
    Imprime un reporte de estado formateado en consola.

    Args:
        conexion: Conexión a la base de datos.
    """
    reporte = generar_reporte_estado(conexion)

    print("\n" + "=" * 60)
    print("REPORTE DE ESTADO - INGESTA SOFASCORE")
    print("=" * 60)
    print(f"Generado: {reporte['fecha_generacion']}")

    print("\n--- RESUMEN GLOBAL ---")
    resumen = reporte['resumen_global']
    print(f"Total partidos: {resumen.get('total_partidos', 0)}")
    print(f"Con estadísticas: {resumen.get('partidos_con_estadisticas', 0)}")
    print(f"Cobertura: {resumen.get('porcentaje_cobertura', 0)}%")

    print("\n--- POR COMPETICIÓN ---")
    for comp in reporte['competiciones']:
        print(f"\n{comp['nombre']} ({comp['codigo']})")
        print(f"  Temporada: {comp['temporada_activa'] or 'N/A'}")
        print(f"  Partidos: {comp['total_partidos']} (finalizados: {comp['partidos_finalizados']})")
        print(f"  Corners: {comp['porcentaje_corners']}% | xG: {comp['porcentaje_xg']}%")
        print(f"  Último partido: {comp['ultimo_partido'] or 'N/A'}")

    if reporte['anomalias']:
        print("\n--- ANOMALÍAS DETECTADAS ---")
        for anomalia in reporte['anomalias']:
            print(f"  [{anomalia['severidad'].upper()}] {anomalia['descripcion']}")

    print("\n--- ÚLTIMAS EJECUCIONES ---")
    for ejec in reporte['ultimas_ejecuciones'][:5]:
        print(
            f"  {ejec['fecha']} | {ejec['tipo']} | "
            f"+{ejec['insertados']} ~{ejec['actualizados']} "
            f"E:{ejec['errores']} | {ejec['estado']}"
        )

    print("\n" + "=" * 60)
