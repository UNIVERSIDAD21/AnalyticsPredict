# -*- coding: utf-8 -*-
"""
Sincronizador de datos de Sofascore a PostgreSQL.

Este módulo implementa la persistencia de todos los datos extraídos
de Sofascore a la base de datos PostgreSQL, incluyendo:

- Resolución de IDs de equipos, temporadas y competiciones
- Upsert de partidos (inserción o actualización si existe)
- Sincronización de estadísticas detalladas
- Manejo de transacciones y rollback

Funciones principales:
- resolver_equipo_id: Obtiene o crea un equipo en la BD
- resolver_temporada_id: Obtiene ID de temporada
- upsert_partido: Inserta o actualiza un partido
- sincronizar_partido_completo: Orquesta la sincronización completa

Ejemplo de uso:
    from scrapers.sofascore.sincronizador import sincronizar_partido_completo

    with obtener_pool().connection() as conn:
        resultado = sincronizar_partido_completo(
            conn, cliente, partido, liga_id=8
        )
        print(f"Partido {'insertado' if resultado['insertado'] else 'actualizado'}")
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .excepciones import ErrorBaseDatos, SofascoreError
from .estadisticas import (
    EstadisticasPartido,
    obtener_estadisticas_partido,
    validar_consistencia_estadisticas,
)
from .partidos import PartidoBasico

if TYPE_CHECKING:
    from .cliente import SofascoreClient

# Configuración del logger
logger = logging.getLogger(__name__)


# Cache en memoria para evitar consultas repetidas
_cache_equipos: Dict[int, int] = {}  # sofascore_id -> bd_id
_cache_competiciones: Dict[int, int] = {}  # sofascore_id -> bd_id
_cache_temporadas: Dict[Tuple[int, str], int] = {}  # (competicion_id, nombre) -> bd_id


def limpiar_cache() -> None:
    """Limpia las caches en memoria."""
    global _cache_equipos, _cache_competiciones, _cache_temporadas
    _cache_equipos = {}
    _cache_competiciones = {}
    _cache_temporadas = {}
    logger.debug("Cache de sincronizador limpiada")


def resolver_equipo_id(
    conexion,
    sofascore_id: int,
    nombre_equipo: str,
    nombre_corto: Optional[str] = None,
    crear_si_no_existe: bool = True
) -> Optional[int]:
    """
    Obtiene el ID interno de un equipo, creándolo si es necesario.

    Busca el equipo en la tabla equipos_futbol por sofascore_id.
    Si no existe y crear_si_no_existe es True, crea un nuevo registro
    marcado para revisión posterior.

    Args:
        conexion: Conexión a la base de datos.
        sofascore_id: ID del equipo en Sofascore.
        nombre_equipo: Nombre completo del equipo.
        nombre_corto: Nombre abreviado del equipo (opcional).
        crear_si_no_existe: Si True, crea el equipo si no existe.

    Returns:
        ID interno del equipo en la base de datos, o None si no existe
        y crear_si_no_existe es False.

    Raises:
        ErrorBaseDatos: Si hay un error al consultar o insertar.

    Ejemplo:
        equipo_id = resolver_equipo_id(conn, 2829, "Real Madrid", "R. Madrid")
    """
    # Verificar cache
    if sofascore_id in _cache_equipos:
        return _cache_equipos[sofascore_id]

    try:
        with conexion.cursor() as cursor:
            # Buscar por sofascore_id
            cursor.execute(
                """
                SELECT id FROM equipos_futbol
                WHERE sofascore_id = %s
                """,
                (sofascore_id,)
            )
            resultado = cursor.fetchone()

            if resultado:
                equipo_id = resultado[0]
                _cache_equipos[sofascore_id] = equipo_id
                return equipo_id

            # No existe, crear si se permite
            if not crear_si_no_existe:
                return None

            # Normalizar nombre
            from .equipos import normalizar_nombre_equipo
            nombre_normalizado = normalizar_nombre_equipo(nombre_equipo)

            cursor.execute(
                """
                INSERT INTO equipos_futbol (
                    nombre, nombre_corto, nombre_normalizado,
                    sofascore_id, activo, requiere_revision
                ) VALUES (%s, %s, %s, %s, TRUE, TRUE)
                RETURNING id
                """,
                (
                    nombre_equipo,
                    nombre_corto or nombre_equipo,
                    nombre_normalizado,
                    sofascore_id
                )
            )
            nuevo_id = cursor.fetchone()[0]
            conexion.commit()

            _cache_equipos[sofascore_id] = nuevo_id
            logger.info(
                f"Equipo creado automáticamente: {nombre_equipo} "
                f"(ID: {nuevo_id}, Sofascore: {sofascore_id})"
            )

            return nuevo_id

    except Exception as e:
        logger.error(f"Error resolviendo equipo {sofascore_id}: {e}")
        raise ErrorBaseDatos(
            mensaje=f"Error resolviendo equipo {nombre_equipo}",
            operacion="SELECT/INSERT",
            tabla="equipos_futbol",
            excepcion_original=e
        )


def resolver_temporada_id(
    conexion,
    competicion_id: int,
    nombre_temporada: str
) -> Optional[int]:
    """
    Obtiene el ID interno de una temporada.

    Las temporadas deben existir previamente en la base de datos.
    Esta función no crea temporadas automáticamente.

    Args:
        conexion: Conexión a la base de datos.
        competicion_id: ID de la competición.
        nombre_temporada: Nombre de la temporada (ej: "2024-25").

    Returns:
        ID interno de la temporada, o None si no existe.

    Raises:
        ErrorBaseDatos: Si hay un error al consultar.
    """
    cache_key = (competicion_id, nombre_temporada)
    if cache_key in _cache_temporadas:
        return _cache_temporadas[cache_key]

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM temporadas_futbol
                WHERE competicion_id = %s AND nombre = %s
                """,
                (competicion_id, nombre_temporada)
            )
            resultado = cursor.fetchone()

            if resultado:
                temporada_id = resultado[0]
                _cache_temporadas[cache_key] = temporada_id
                return temporada_id

            return None

    except Exception as e:
        logger.error(f"Error resolviendo temporada {nombre_temporada}: {e}")
        raise ErrorBaseDatos(
            mensaje=f"Error resolviendo temporada {nombre_temporada}",
            operacion="SELECT",
            tabla="temporadas_futbol",
            excepcion_original=e
        )


def resolver_temporada_id_por_sofascore(
    conexion,
    competicion_id: int,
    sofascore_season_id: int
) -> Optional[int]:
    """
    Obtiene el ID interno de una temporada por su ID de Sofascore.

    Args:
        conexion: Conexión a la base de datos.
        competicion_id: ID de la competición.
        sofascore_season_id: ID de la temporada en Sofascore.

    Returns:
        ID interno de la temporada, o None si no existe.
    """
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM temporadas_futbol
                WHERE competicion_id = %s AND sofascore_season_id = %s
                """,
                (competicion_id, sofascore_season_id)
            )
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None

    except Exception as e:
        logger.error(f"Error resolviendo temporada por Sofascore ID {sofascore_season_id}: {e}")
        return None


def resolver_competicion_id(
    conexion,
    sofascore_liga_id: int
) -> Optional[int]:
    """
    Obtiene el ID interno de una competición por su ID de Sofascore.

    Las competiciones deben estar pre-configuradas en la base de datos
    con su sofascore_id mapeado.

    Args:
        conexion: Conexión a la base de datos.
        sofascore_liga_id: ID de la liga en Sofascore.

    Returns:
        ID interno de la competición, o None si no existe.

    Raises:
        ErrorBaseDatos: Si hay un error al consultar.
    """
    if sofascore_liga_id in _cache_competiciones:
        return _cache_competiciones[sofascore_liga_id]

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM competiciones_futbol
                WHERE sofascore_id = %s
                """,
                (sofascore_liga_id,)
            )
            resultado = cursor.fetchone()

            if resultado:
                competicion_id = resultado[0]
                _cache_competiciones[sofascore_liga_id] = competicion_id
                return competicion_id

            logger.warning(
                f"Competición con Sofascore ID {sofascore_liga_id} no encontrada"
            )
            return None

    except Exception as e:
        logger.error(f"Error resolviendo competición {sofascore_liga_id}: {e}")
        raise ErrorBaseDatos(
            mensaje=f"Error resolviendo competición Sofascore ID {sofascore_liga_id}",
            operacion="SELECT",
            tabla="competiciones_futbol",
            excepcion_original=e
        )


def upsert_partido(
    conexion,
    partido: PartidoBasico,
    estadisticas: Optional[EstadisticasPartido] = None,
    competicion_id: Optional[int] = None,
    temporada_id: Optional[int] = None
) -> Tuple[int, bool, List[str]]:
    """
    Inserta o actualiza un partido en la base de datos.

    Si el partido existe (por sofascore_match_id), actualiza los campos
    que hayan cambiado. Si no existe, inserta un nuevo registro.

    Args:
        conexion: Conexión a la base de datos.
        partido: Objeto PartidoBasico con datos del partido.
        estadisticas: Objeto EstadisticasPartido opcional con estadísticas.
        competicion_id: ID de la competición (requerido si no existe).
        temporada_id: ID de la temporada (requerido si no existe).

    Returns:
        Tupla con:
        - partido_id: ID del partido en la base de datos
        - fue_insercion: True si se insertó, False si se actualizó
        - campos_actualizados: Lista de campos que cambiaron (solo si update)

    Raises:
        ErrorBaseDatos: Si hay un error de base de datos.
        ValueError: Si faltan competicion_id o temporada_id para inserción.

    Ejemplo:
        partido_id, insertado, cambios = upsert_partido(
            conn, partido, estadisticas,
            competicion_id=1, temporada_id=5
        )
    """
    try:
        with conexion.cursor() as cursor:
            # Verificar si existe el partido
            cursor.execute(
                """
                SELECT id, estado, local_goles_total, visitante_goles_total,
                       corners_local_total, disparos_local_total
                FROM partidos_futbol
                WHERE sofascore_match_id = %s
                """,
                (partido.sofascore_id,)
            )
            existente = cursor.fetchone()

            # Resolver IDs de equipos
            equipo_local_id = resolver_equipo_id(
                conexion,
                partido.equipo_local_id,
                partido.equipo_local_nombre,
                partido.equipo_local_nombre_corto
            )
            equipo_visitante_id = resolver_equipo_id(
                conexion,
                partido.equipo_visitante_id,
                partido.equipo_visitante_nombre,
                partido.equipo_visitante_nombre_corto
            )

            # Calcular campos derivados
            ganador_id = _calcular_ganador_id(
                partido, equipo_local_id, equipo_visitante_id
            )
            diferencia_goles = _calcular_diferencia_goles(partido)
            resultado_final = partido.obtener_resultado()

            if existente is None:
                # INSERTAR nuevo partido
                if competicion_id is None or temporada_id is None:
                    raise ValueError(
                        "competicion_id y temporada_id son requeridos para insertar"
                    )

                campos, valores, placeholders = _construir_insert_partido(
                    partido, estadisticas,
                    competicion_id, temporada_id,
                    equipo_local_id, equipo_visitante_id,
                    ganador_id, diferencia_goles, resultado_final
                )

                cursor.execute(
                    f"""
                    INSERT INTO partidos_futbol ({', '.join(campos)})
                    VALUES ({', '.join(placeholders)})
                    RETURNING id
                    """,
                    valores
                )
                partido_id = cursor.fetchone()[0]
                conexion.commit()

                logger.debug(
                    f"Partido insertado: {partido.equipo_local_nombre} vs "
                    f"{partido.equipo_visitante_nombre} (ID: {partido_id})"
                )

                return partido_id, True, []

            else:
                # ACTUALIZAR partido existente
                partido_id = existente[0]
                campos_actualizados = []

                # Construir UPDATE dinámico solo con campos que cambiaron
                updates, valores = _construir_update_partido(
                    partido, estadisticas, existente,
                    equipo_local_id, equipo_visitante_id,
                    ganador_id, diferencia_goles, resultado_final
                )

                if updates:
                    valores.append(partido_id)
                    cursor.execute(
                        f"""
                        UPDATE partidos_futbol
                        SET {', '.join(updates)}, actualizado_en = NOW()
                        WHERE id = %s
                        """,
                        valores
                    )
                    conexion.commit()
                    campos_actualizados = [u.split(' = ')[0] for u in updates]

                    logger.debug(
                        f"Partido actualizado: {partido.equipo_local_nombre} vs "
                        f"{partido.equipo_visitante_nombre} "
                        f"(cambios: {campos_actualizados})"
                    )
                else:
                    logger.debug(
                        f"Partido sin cambios: {partido.equipo_local_nombre} vs "
                        f"{partido.equipo_visitante_nombre}"
                    )

                return partido_id, False, campos_actualizados

    except Exception as e:
        conexion.rollback()
        logger.error(f"Error en upsert_partido: {e}")
        raise ErrorBaseDatos(
            mensaje=f"Error guardando partido {partido.sofascore_id}",
            operacion="UPSERT",
            tabla="partidos_futbol",
            excepcion_original=e
        )


def _construir_insert_partido(
    partido: PartidoBasico,
    estadisticas: Optional[EstadisticasPartido],
    competicion_id: int,
    temporada_id: int,
    equipo_local_id: int,
    equipo_visitante_id: int,
    ganador_id: Optional[int],
    diferencia_goles: Optional[int],
    resultado_final: str
) -> Tuple[List[str], List[Any], List[str]]:
    """Construye las listas para el INSERT de un partido."""
    campos = [
        'sofascore_match_id', 'fecha_partido', 'competicion_id', 'temporada_id',
        'equipo_local_id', 'equipo_visitante_id',
        'local_goles_1t', 'local_goles_2t', 'local_goles_total',
        'visitante_goles_1t', 'visitante_goles_2t', 'visitante_goles_total',
        'estado', 'jornada', 'ganador_id', 'diferencia_goles', 'resultado_final',
        'tiene_prorroga', 'tiene_penales'
    ]

    valores = [
        partido.sofascore_id,
        partido.fecha_partido,
        competicion_id,
        temporada_id,
        equipo_local_id,
        equipo_visitante_id,
        partido.goles_local_1t,
        partido.goles_local_2t,
        partido.goles_local_total,
        partido.goles_visitante_1t,
        partido.goles_visitante_2t,
        partido.goles_visitante_total,
        partido.estado,
        partido.jornada,
        ganador_id,
        diferencia_goles,
        resultado_final,
        partido.tiene_prorroga,
        partido.tiene_penales
    ]

    # Agregar estadísticas si están disponibles
    if estadisticas:
        campos_stats = [
            'corners_local_1t', 'corners_local_2t', 'corners_local_total',
            'corners_visitante_1t', 'corners_visitante_2t', 'corners_visitante_total',
            'disparos_local_total', 'disparos_local_arco',
            'disparos_visitante_total', 'disparos_visitante_arco',
            'posesion_local', 'posesion_visitante',
            'xg_local', 'xg_visitante',
            'datos_estadisticas_completos'
        ]
        campos.extend(campos_stats)

        valores.extend([
            estadisticas.corners_local_1t,
            estadisticas.corners_local_2t,
            estadisticas.corners_local_total,
            estadisticas.corners_visitante_1t,
            estadisticas.corners_visitante_2t,
            estadisticas.corners_visitante_total,
            estadisticas.disparos_local_total,
            estadisticas.disparos_local_arco,
            estadisticas.disparos_visitante_total,
            estadisticas.disparos_visitante_arco,
            estadisticas.posesion_local,
            estadisticas.posesion_visitante,
            estadisticas.xg_local,
            estadisticas.xg_visitante,
            estadisticas.datos_completos
        ])

    placeholders = ['%s'] * len(valores)

    return campos, valores, placeholders


def _construir_update_partido(
    partido: PartidoBasico,
    estadisticas: Optional[EstadisticasPartido],
    existente: Tuple,
    equipo_local_id: int,
    equipo_visitante_id: int,
    ganador_id: Optional[int],
    diferencia_goles: Optional[int],
    resultado_final: str
) -> Tuple[List[str], List[Any]]:
    """Construye las cláusulas SET para el UPDATE de un partido."""
    updates = []
    valores = []

    db_estado = existente[1]
    db_goles_local = existente[2]
    db_goles_visitante = existente[3]
    db_corners_local = existente[4]
    db_disparos_local = existente[5]

    # Actualizar estado si cambió
    if partido.estado != db_estado:
        updates.append('estado = %s')
        valores.append(partido.estado)

    # Actualizar goles si cambiaron
    if partido.goles_local_total != db_goles_local:
        updates.extend([
            'local_goles_1t = %s',
            'local_goles_2t = %s',
            'local_goles_total = %s'
        ])
        valores.extend([
            partido.goles_local_1t,
            partido.goles_local_2t,
            partido.goles_local_total
        ])

    if partido.goles_visitante_total != db_goles_visitante:
        updates.extend([
            'visitante_goles_1t = %s',
            'visitante_goles_2t = %s',
            'visitante_goles_total = %s'
        ])
        valores.extend([
            partido.goles_visitante_1t,
            partido.goles_visitante_2t,
            partido.goles_visitante_total
        ])

    # Actualizar campos derivados si los goles cambiaron
    if (partido.goles_local_total != db_goles_local or
        partido.goles_visitante_total != db_goles_visitante):
        updates.extend([
            'ganador_id = %s',
            'diferencia_goles = %s',
            'resultado_final = %s'
        ])
        valores.extend([ganador_id, diferencia_goles, resultado_final])

    # Actualizar estadísticas si están disponibles y no existían
    if estadisticas and db_corners_local is None:
        updates.extend([
            'corners_local_1t = %s',
            'corners_local_2t = %s',
            'corners_local_total = %s',
            'corners_visitante_1t = %s',
            'corners_visitante_2t = %s',
            'corners_visitante_total = %s',
            'disparos_local_total = %s',
            'disparos_local_arco = %s',
            'disparos_visitante_total = %s',
            'disparos_visitante_arco = %s',
            'posesion_local = %s',
            'posesion_visitante = %s',
            'xg_local = %s',
            'xg_visitante = %s',
            'datos_estadisticas_completos = %s'
        ])
        valores.extend([
            estadisticas.corners_local_1t,
            estadisticas.corners_local_2t,
            estadisticas.corners_local_total,
            estadisticas.corners_visitante_1t,
            estadisticas.corners_visitante_2t,
            estadisticas.corners_visitante_total,
            estadisticas.disparos_local_total,
            estadisticas.disparos_local_arco,
            estadisticas.disparos_visitante_total,
            estadisticas.disparos_visitante_arco,
            estadisticas.posesion_local,
            estadisticas.posesion_visitante,
            estadisticas.xg_local,
            estadisticas.xg_visitante,
            estadisticas.datos_completos
        ])

    return updates, valores


def _calcular_ganador_id(
    partido: PartidoBasico,
    equipo_local_id: int,
    equipo_visitante_id: int
) -> Optional[int]:
    """Calcula el ID del equipo ganador."""
    if not partido.esta_finalizado():
        return None

    if partido.goles_local_total is None or partido.goles_visitante_total is None:
        return None

    if partido.goles_local_total > partido.goles_visitante_total:
        return equipo_local_id
    elif partido.goles_visitante_total > partido.goles_local_total:
        return equipo_visitante_id

    return None  # Empate


def _calcular_diferencia_goles(partido: PartidoBasico) -> Optional[int]:
    """Calcula la diferencia de goles (valor absoluto)."""
    if partido.goles_local_total is None or partido.goles_visitante_total is None:
        return None

    return abs(partido.goles_local_total - partido.goles_visitante_total)


def sincronizar_partido_completo(
    conexion,
    cliente: 'SofascoreClient',
    partido: PartidoBasico,
    liga_id: int,
    temporada_id: Optional[int] = None,
    competicion_id: Optional[int] = None,
    obtener_estadisticas_flag: bool = True
) -> Dict[str, Any]:
    """
    Sincroniza un partido completo con estadísticas a la base de datos.

    Esta función orquesta todo el proceso de sincronización:
    1. Resuelve IDs de competición y temporada
    2. Resuelve IDs de equipos (creándolos si es necesario)
    3. Obtiene estadísticas detalladas si el partido está finalizado
    4. Guarda todo en la base de datos

    Args:
        conexion: Conexión a la base de datos.
        cliente: Instancia de SofascoreClient.
        partido: Objeto PartidoBasico a sincronizar.
        liga_id: ID de la liga en Sofascore.
        temporada_id: ID de la temporada en BD (se resuelve si es None).
        competicion_id: ID de la competición en BD (se resuelve si es None).
        obtener_estadisticas_flag: Si obtener estadísticas de partidos finalizados.

    Returns:
        Diccionario con resumen de la operación:
        - partido_id: ID del partido en la BD
        - insertado: True si se insertó, False si se actualizó
        - tiene_estadisticas: True si se guardaron estadísticas
        - cambios: Lista de campos actualizados
        - errores: Lista de errores encontrados

    Raises:
        SofascoreError: Si hay error irrecuperable en la sincronización.

    Ejemplo:
        resultado = sincronizar_partido_completo(
            conn, cliente, partido, liga_id=8
        )
        if resultado['insertado']:
            print(f"Nuevo partido guardado: {resultado['partido_id']}")
    """
    resultado = {
        'partido_id': None,
        'insertado': False,
        'tiene_estadisticas': False,
        'cambios': [],
        'errores': [],
        'warnings': [],
    }

    try:
        # Resolver competicion_id si no se proporcionó
        if competicion_id is None:
            competicion_id = resolver_competicion_id(conexion, liga_id)
            if competicion_id is None:
                resultado['errores'].append(
                    f"Competición con Sofascore ID {liga_id} no encontrada"
                )
                return resultado

        # Resolver temporada_id si no se proporcionó
        if temporada_id is None:
            # Intentar obtener temporada activa
            from .temporadas import obtener_temporada_activa
            temp_activa = obtener_temporada_activa(conexion, competicion_id)
            if temp_activa:
                temporada_id = temp_activa['id']
            else:
                resultado['errores'].append(
                    f"No se pudo determinar la temporada para competición {competicion_id}"
                )
                return resultado

        # Obtener estadísticas si el partido está finalizado
        estadisticas = None
        if obtener_estadisticas_flag and partido.esta_finalizado():
            estadisticas = obtener_estadisticas_partido(cliente, partido.sofascore_id)

            if estadisticas:
                resultado['tiene_estadisticas'] = True

                # Validar consistencia
                inconsistencias = validar_consistencia_estadisticas(estadisticas)
                if inconsistencias:
                    resultado['warnings'].extend(inconsistencias)
                    for msg in inconsistencias:
                        logger.warning(f"Partido {partido.sofascore_id}: {msg}")

        # Guardar en base de datos
        partido_id, insertado, cambios = upsert_partido(
            conexion,
            partido,
            estadisticas,
            competicion_id,
            temporada_id
        )

        resultado['partido_id'] = partido_id
        resultado['insertado'] = insertado
        resultado['cambios'] = cambios

        return resultado

    except Exception as e:
        resultado['errores'].append(str(e))
        logger.error(f"Error sincronizando partido {partido.sofascore_id}: {e}")
        return resultado


def sincronizar_lote_partidos(
    conexion,
    cliente: 'SofascoreClient',
    partidos: List[PartidoBasico],
    liga_id: int,
    temporada_id: Optional[int] = None,
    competicion_id: Optional[int] = None,
    obtener_estadisticas_flag: bool = True,
    callback_progreso=None
) -> Dict[str, Any]:
    """
    Sincroniza un lote de partidos a la base de datos.

    Procesa múltiples partidos en secuencia, manejando errores
    individuales sin detener el lote completo.

    Args:
        conexion: Conexión a la base de datos.
        cliente: Instancia de SofascoreClient.
        partidos: Lista de PartidoBasico a sincronizar.
        liga_id: ID de la liga en Sofascore.
        temporada_id: ID de la temporada en BD.
        competicion_id: ID de la competición en BD.
        obtener_estadisticas_flag: Si obtener estadísticas.
        callback_progreso: Función opcional para reportar progreso.

    Returns:
        Diccionario con resumen del lote:
        - total: Número total de partidos
        - insertados: Número de partidos insertados
        - actualizados: Número de partidos actualizados
        - con_estadisticas: Número con estadísticas guardadas
        - errores: Número de errores
        - detalles_errores: Lista de errores

    Ejemplo:
        resultado = sincronizar_lote_partidos(
            conn, cliente, partidos, liga_id=8
        )
        print(f"Procesados: {resultado['insertados'] + resultado['actualizados']}")
    """
    resumen = {
        'total': len(partidos),
        'insertados': 0,
        'actualizados': 0,
        'sin_cambios': 0,
        'con_estadisticas': 0,
        'errores': 0,
        'detalles_errores': [],
    }

    # Resolver IDs una sola vez
    if competicion_id is None:
        competicion_id = resolver_competicion_id(conexion, liga_id)
        if competicion_id is None:
            resumen['errores'] = len(partidos)
            resumen['detalles_errores'].append(
                f"Competición con Sofascore ID {liga_id} no encontrada"
            )
            return resumen

    if temporada_id is None:
        from .temporadas import obtener_temporada_activa
        temp_activa = obtener_temporada_activa(conexion, competicion_id)
        if temp_activa:
            temporada_id = temp_activa['id']

    for i, partido in enumerate(partidos):
        try:
            resultado = sincronizar_partido_completo(
                conexion, cliente, partido, liga_id,
                temporada_id, competicion_id,
                obtener_estadisticas_flag
            )

            if resultado['errores']:
                resumen['errores'] += 1
                resumen['detalles_errores'].extend(resultado['errores'])
            elif resultado['insertado']:
                resumen['insertados'] += 1
            elif resultado['cambios']:
                resumen['actualizados'] += 1
            else:
                resumen['sin_cambios'] += 1

            if resultado['tiene_estadisticas']:
                resumen['con_estadisticas'] += 1

            # Callback de progreso
            if callback_progreso:
                callback_progreso(i + 1, len(partidos), partido)

        except Exception as e:
            resumen['errores'] += 1
            resumen['detalles_errores'].append(
                f"Partido {partido.sofascore_id}: {str(e)}"
            )
            logger.error(f"Error procesando partido {partido.sofascore_id}: {e}")

    return resumen


def verificar_partido_existe(
    conexion,
    sofascore_match_id: int
) -> bool:
    """
    Verifica si un partido ya existe en la base de datos.

    Args:
        conexion: Conexión a la base de datos.
        sofascore_match_id: ID del partido en Sofascore.

    Returns:
        True si el partido existe, False si no.
    """
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM partidos_futbol
                WHERE sofascore_match_id = %s
                """,
                (sofascore_match_id,)
            )
            return cursor.fetchone() is not None

    except Exception as e:
        logger.error(f"Error verificando partido {sofascore_match_id}: {e}")
        return False


def obtener_partidos_sin_estadisticas(
    conexion,
    competicion_id: Optional[int] = None,
    temporada_id: Optional[int] = None,
    limite: int = 100
) -> List[Dict[str, Any]]:
    """
    Obtiene partidos finalizados que no tienen estadísticas.

    Útil para completar datos de partidos que se sincronizaron
    sin estadísticas inicialmente.

    Args:
        conexion: Conexión a la base de datos.
        competicion_id: Filtrar por competición (opcional).
        temporada_id: Filtrar por temporada (opcional).
        limite: Máximo número de partidos a retornar.

    Returns:
        Lista de diccionarios con datos básicos de partidos.
    """
    try:
        with conexion.cursor() as cursor:
            query = """
                SELECT id, sofascore_match_id, fecha_partido,
                       equipo_local_id, equipo_visitante_id
                FROM partidos_futbol
                WHERE estado = 'finished'
                  AND corners_local_total IS NULL
            """
            params = []

            if competicion_id:
                query += " AND competicion_id = %s"
                params.append(competicion_id)

            if temporada_id:
                query += " AND temporada_id = %s"
                params.append(temporada_id)

            query += " ORDER BY fecha_partido DESC LIMIT %s"
            params.append(limite)

            cursor.execute(query, params)
            resultados = cursor.fetchall()

            return [
                {
                    'id': r[0],
                    'sofascore_match_id': r[1],
                    'fecha_partido': r[2],
                    'equipo_local_id': r[3],
                    'equipo_visitante_id': r[4],
                }
                for r in resultados
            ]

    except Exception as e:
        logger.error(f"Error obteniendo partidos sin estadísticas: {e}")
        return []
