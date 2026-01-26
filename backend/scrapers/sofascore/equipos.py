# -*- coding: utf-8 -*-
"""
Extractor de equipos desde Sofascore.

Este módulo proporciona funciones para obtener y sincronizar información
de equipos de fútbol desde la API de Sofascore.

Funciones principales:
- obtener_equipos_desde_standings: Obtiene equipos desde la clasificación
- obtener_equipos_desde_partidos: Obtiene equipos desde los partidos
- normalizar_nombre_equipo: Normaliza nombres para búsquedas
- sincronizar_equipos: Sincroniza equipos con la base de datos

Ejemplo de uso:
    from scrapers.sofascore.cliente import SofascoreClient
    from scrapers.sofascore.equipos import obtener_equipos_desde_standings

    cliente = SofascoreClient()
    equipos = obtener_equipos_desde_standings(cliente, liga_id=8, temporada_id=12345)
    for equipo in equipos:
        print(f"{equipo['nombre']} ({equipo['nombre_corto']})")
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from .excepciones import DatosIncompletos, SofascoreError

if TYPE_CHECKING:
    from .cliente import SofascoreClient

# Configuración del logger
logger = logging.getLogger(__name__)

# Sufijos comunes a eliminar en la normalización
SUFIJOS_ELIMINAR = [
    ' cf', ' fc', ' sc', ' ac', ' bc', ' rc', ' ud', ' cd',
    ' club', ' futbol', ' fútbol', ' deportivo', ' sporting',
    ' athletic', ' atlético', ' atletico', ' real',
    ' fussball', ' calcio', ' football',
]

# Prefijos comunes a eliminar
PREFIJOS_ELIMINAR = [
    'real ', 'club ', 'fc ', 'cf ', 'ud ', 'cd ', 'rc ',
    'sporting ', 'athletic ', 'atlético ', 'atletico ',
]


def obtener_equipos_desde_standings(
    cliente: 'SofascoreClient',
    liga_id: int,
    temporada_id: int
) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de equipos desde la clasificación de una liga.

    Este es el método preferido para obtener equipos ya que la clasificación
    contiene todos los equipos de la temporada con información completa.

    Args:
        cliente: Instancia de SofascoreClient.
        liga_id: ID de la liga en Sofascore.
        temporada_id: ID de la temporada en Sofascore.

    Returns:
        Lista de diccionarios con información de cada equipo:
        - sofascore_id: int - ID del equipo en Sofascore
        - nombre: str - Nombre completo del equipo
        - nombre_corto: str - Nombre abreviado
        - slug: str - Slug para URLs
        - nombre_normalizado: str - Nombre normalizado para búsquedas

    Raises:
        SofascoreError: Si hay un error al consultar Sofascore.

    Ejemplo:
        equipos = obtener_equipos_desde_standings(cliente, 8, 52376)
        for e in equipos:
            print(f"{e['nombre']} - ID: {e['sofascore_id']}")
    """
    endpoint = f"/unique-tournament/{liga_id}/season/{temporada_id}/standings/total"

    logger.debug(
        f"Obteniendo equipos desde standings: "
        f"liga={liga_id}, temporada={temporada_id}"
    )

    datos = cliente.get(endpoint)

    if datos is None:
        logger.warning(
            f"No se encontraron standings para liga={liga_id}, "
            f"temporada={temporada_id}"
        )
        return []

    equipos = []
    equipos_vistos: Set[int] = set()

    # La estructura puede variar: standings puede ser lista o dict
    standings_data = datos.get('standings', [])

    if isinstance(standings_data, dict):
        # Algunas ligas tienen formato diferente
        standings_data = [standings_data]

    for standings in standings_data:
        rows = standings.get('rows', [])

        for row in rows:
            equipo_json = row.get('team', {})

            if not equipo_json:
                continue

            sofascore_id = equipo_json.get('id')

            if sofascore_id is None or sofascore_id in equipos_vistos:
                continue

            equipos_vistos.add(sofascore_id)

            try:
                equipo = _parsear_equipo(equipo_json)
                equipos.append(equipo)
            except Exception as e:
                logger.warning(f"Error parseando equipo: {e}. Datos: {equipo_json}")

    logger.info(
        f"Obtenidos {len(equipos)} equipos desde standings de "
        f"liga={liga_id}, temporada={temporada_id}"
    )

    return equipos


def obtener_equipos_desde_partidos(
    cliente: 'SofascoreClient',
    partidos: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extrae equipos únicos desde una lista de partidos.

    Función alternativa para obtener equipos cuando no hay standings
    disponibles (por ejemplo, en copas).

    Args:
        cliente: Instancia de SofascoreClient (no usado pero mantenido
                por consistencia de API).
        partidos: Lista de partidos parseados (cada uno debe tener
                 equipo_local y equipo_visitante).

    Returns:
        Lista de diccionarios con información de cada equipo único.

    Ejemplo:
        partidos = obtener_partidos_pasados(cliente, 329, 52376)
        equipos = obtener_equipos_desde_partidos(cliente, partidos)
    """
    equipos: Dict[int, Dict[str, Any]] = {}

    for partido in partidos:
        # Extraer equipo local
        local_id = partido.get('equipo_local_id')
        if local_id and local_id not in equipos:
            equipos[local_id] = {
                'sofascore_id': local_id,
                'nombre': partido.get('equipo_local_nombre', ''),
                'nombre_corto': partido.get('equipo_local_nombre_corto', ''),
                'slug': '',
                'nombre_normalizado': normalizar_nombre_equipo(
                    partido.get('equipo_local_nombre', '')
                ),
            }

        # Extraer equipo visitante
        visitante_id = partido.get('equipo_visitante_id')
        if visitante_id and visitante_id not in equipos:
            equipos[visitante_id] = {
                'sofascore_id': visitante_id,
                'nombre': partido.get('equipo_visitante_nombre', ''),
                'nombre_corto': partido.get('equipo_visitante_nombre_corto', ''),
                'slug': '',
                'nombre_normalizado': normalizar_nombre_equipo(
                    partido.get('equipo_visitante_nombre', '')
                ),
            }

    logger.info(f"Extraídos {len(equipos)} equipos únicos desde partidos")

    return list(equipos.values())


def _parsear_equipo(equipo_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parsea el JSON de un equipo de Sofascore.

    Args:
        equipo_json: Diccionario con datos del equipo.

    Returns:
        Diccionario con datos estructurados del equipo.
    """
    sofascore_id = equipo_json.get('id')

    if sofascore_id is None:
        raise DatosIncompletos(
            mensaje="Equipo sin ID",
            campos_faltantes=['id'],
            tipo_datos='equipo'
        )

    nombre = equipo_json.get('name', '')
    nombre_corto = equipo_json.get('shortName', nombre)
    slug = equipo_json.get('slug', '')

    return {
        'sofascore_id': sofascore_id,
        'nombre': nombre,
        'nombre_corto': nombre_corto,
        'slug': slug,
        'nombre_normalizado': normalizar_nombre_equipo(nombre),
    }


def normalizar_nombre_equipo(nombre: str) -> str:
    """
    Crea una versión normalizada del nombre del equipo para búsquedas.

    La normalización incluye:
    1. Convertir a minúsculas
    2. Eliminar acentos y caracteres especiales
    3. Eliminar sufijos comunes (FC, CF, Club, etc.)
    4. Eliminar espacios extra

    Esta función es crítica para evitar duplicados y facilitar
    búsquedas fuzzy de equipos.

    Args:
        nombre: Nombre original del equipo.

    Returns:
        Nombre normalizado en minúsculas, sin acentos ni sufijos.

    Ejemplo:
        normalizar_nombre_equipo("Real Madrid CF")
        # Retorna: "madrid"

        normalizar_nombre_equipo("FC Barcelona")
        # Retorna: "barcelona"

        normalizar_nombre_equipo("Atlético de Madrid")
        # Retorna: "madrid"
    """
    if not nombre:
        return ''

    # Convertir a minúsculas
    normalizado = nombre.lower().strip()

    # Eliminar acentos y caracteres especiales
    normalizado = unicodedata.normalize('NFKD', normalizado)
    normalizado = normalizado.encode('ascii', 'ignore').decode('ascii')

    # Eliminar caracteres no alfanuméricos excepto espacios
    normalizado = re.sub(r'[^a-z0-9\s]', '', normalizado)

    # Eliminar sufijos comunes
    for sufijo in SUFIJOS_ELIMINAR:
        if normalizado.endswith(sufijo):
            normalizado = normalizado[:-len(sufijo)]

    # Eliminar prefijos comunes
    for prefijo in PREFIJOS_ELIMINAR:
        if normalizado.startswith(prefijo):
            normalizado = normalizado[len(prefijo):]

    # Eliminar "de" y "del" en el medio
    normalizado = re.sub(r'\s+de\s+', ' ', normalizado)
    normalizado = re.sub(r'\s+del\s+', ' ', normalizado)

    # Eliminar espacios extra
    normalizado = ' '.join(normalizado.split())

    return normalizado.strip()


def buscar_equipo_similar(
    nombre: str,
    equipos: List[Dict[str, Any]],
    umbral_similitud: float = 0.8
) -> Optional[Dict[str, Any]]:
    """
    Busca un equipo por similitud de nombre.

    Útil para encontrar equipos con nombres ligeramente diferentes
    (variaciones, errores tipográficos, etc.).

    Args:
        nombre: Nombre del equipo a buscar.
        equipos: Lista de equipos donde buscar.
        umbral_similitud: Umbral mínimo de similitud (0-1).

    Returns:
        Equipo más similar si supera el umbral, None si no hay coincidencias.
    """
    from difflib import SequenceMatcher

    nombre_normalizado = normalizar_nombre_equipo(nombre)

    if not nombre_normalizado:
        return None

    mejor_match = None
    mejor_ratio = 0.0

    for equipo in equipos:
        equipo_normalizado = equipo.get('nombre_normalizado', '')

        if not equipo_normalizado:
            continue

        # Calcular similitud
        ratio = SequenceMatcher(
            None,
            nombre_normalizado,
            equipo_normalizado
        ).ratio()

        # También verificar coincidencia exacta del nombre corto
        nombre_corto = equipo.get('nombre_corto', '').lower()
        if nombre.lower() == nombre_corto:
            return equipo

        if ratio > mejor_ratio:
            mejor_ratio = ratio
            mejor_match = equipo

    if mejor_ratio >= umbral_similitud:
        return mejor_match

    return None


def sincronizar_equipos(
    conexion,
    cliente: 'SofascoreClient',
    liga_id: int,
    temporada_id: int,
    competicion_id: int,
    usar_partidos_si_no_hay_standings: bool = True
) -> Dict[str, Any]:
    """
    Sincroniza equipos de Sofascore con la base de datos.

    Intenta primero obtener equipos desde standings. Si no hay standings
    disponibles (como en copas), usa la lista de partidos como alternativa.

    Para cada equipo:
    1. Busca en la tabla equipos_futbol por sofascore_id
    2. Si no existe, inserta nuevo registro
    3. Si existe, actualiza campos si han cambiado
    4. Asocia el equipo con la competición

    Args:
        conexion: Conexión a la base de datos PostgreSQL.
        cliente: Instancia de SofascoreClient.
        liga_id: ID de la liga en Sofascore.
        temporada_id: ID de la temporada en Sofascore.
        competicion_id: ID de la competición en la tabla competiciones_futbol.
        usar_partidos_si_no_hay_standings: Si True, usa partidos como fallback.

    Returns:
        Diccionario con resumen de la sincronización:
        - insertados: int - Número de equipos insertados
        - actualizados: int - Número de equipos actualizados
        - sin_cambios: int - Número de equipos sin cambios
        - errores: int - Número de errores
        - fuente: str - 'standings' o 'partidos'

    Ejemplo:
        with obtener_pool().connection() as conn:
            resultado = sincronizar_equipos(
                conn, cliente, liga_id=8, temporada_id=52376,
                competicion_id=1
            )
            print(f"Equipos insertados: {resultado['insertados']}")
    """
    logger.info(
        f"Sincronizando equipos: liga={liga_id}, temporada={temporada_id}, "
        f"competicion={competicion_id}"
    )

    # Intentar obtener equipos desde standings
    equipos = obtener_equipos_desde_standings(cliente, liga_id, temporada_id)
    fuente = 'standings'

    # Si no hay equipos en standings, intentar desde partidos
    if not equipos and usar_partidos_si_no_hay_standings:
        logger.info(
            "No hay standings disponibles, obteniendo equipos desde partidos"
        )
        from .partidos import obtener_partidos_pasados

        partidos_data = obtener_partidos_pasados(
            cliente, liga_id, temporada_id, limite_paginas=10
        )
        # Convertir a diccionarios si son dataclasses
        partidos_dict = []
        for p in partidos_data:
            if hasattr(p, '__dict__'):
                partidos_dict.append(vars(p))
            elif hasattr(p, '_asdict'):
                partidos_dict.append(p._asdict())
            else:
                partidos_dict.append(p)

        equipos = obtener_equipos_desde_partidos(cliente, partidos_dict)
        fuente = 'partidos'

    resultado = {
        'insertados': 0,
        'actualizados': 0,
        'sin_cambios': 0,
        'errores': 0,
        'fuente': fuente,
        'detalles': [],
    }

    if not equipos:
        logger.warning(f"No se encontraron equipos para sincronizar")
        return resultado

    with conexion.cursor() as cursor:
        for equipo in equipos:
            try:
                sofascore_id = equipo['sofascore_id']
                nombre = equipo['nombre']
                nombre_corto = equipo['nombre_corto']
                slug = equipo.get('slug', '')
                nombre_normalizado = equipo['nombre_normalizado']

                # Buscar equipo existente por sofascore_id
                cursor.execute(
                    """
                    SELECT id, nombre, nombre_corto, nombre_normalizado, slug
                    FROM equipos_futbol
                    WHERE sofascore_id = %s
                    """,
                    (sofascore_id,)
                )
                existente = cursor.fetchone()

                if existente is None:
                    # Insertar nuevo equipo
                    cursor.execute(
                        """
                        INSERT INTO equipos_futbol (
                            nombre, nombre_corto, nombre_normalizado,
                            sofascore_id, slug, activo
                        ) VALUES (%s, %s, %s, %s, %s, TRUE)
                        RETURNING id
                        """,
                        (nombre, nombre_corto, nombre_normalizado, sofascore_id, slug)
                    )
                    nuevo_id = cursor.fetchone()[0]

                    resultado['insertados'] += 1
                    resultado['detalles'].append({
                        'equipo': nombre,
                        'accion': 'insertado',
                        'id': nuevo_id
                    })
                    logger.debug(f"Equipo insertado: {nombre} (ID: {nuevo_id})")

                else:
                    # Verificar si hay cambios
                    db_id = existente[0]
                    db_nombre = existente[1]
                    db_nombre_corto = existente[2]
                    db_nombre_norm = existente[3]
                    db_slug = existente[4]

                    cambios = []

                    if db_nombre != nombre:
                        cambios.append(('nombre', nombre))
                    if db_nombre_corto != nombre_corto:
                        cambios.append(('nombre_corto', nombre_corto))
                    if db_nombre_norm != nombre_normalizado:
                        cambios.append(('nombre_normalizado', nombre_normalizado))
                    if slug and db_slug != slug:
                        cambios.append(('slug', slug))

                    if cambios:
                        set_clauses = [f"{campo} = %s" for campo, _ in cambios]
                        valores = [valor for _, valor in cambios]
                        valores.append(db_id)

                        cursor.execute(
                            f"""
                            UPDATE equipos_futbol
                            SET {', '.join(set_clauses)}, actualizado_en = NOW()
                            WHERE id = %s
                            """,
                            valores
                        )
                        resultado['actualizados'] += 1
                        resultado['detalles'].append({
                            'equipo': nombre,
                            'accion': 'actualizado',
                            'id': db_id,
                            'cambios': [c[0] for c in cambios]
                        })
                        logger.debug(
                            f"Equipo actualizado: {nombre} "
                            f"(cambios: {[c[0] for c in cambios]})"
                        )
                    else:
                        resultado['sin_cambios'] += 1

            except Exception as e:
                resultado['errores'] += 1
                logger.error(f"Error sincronizando equipo {equipo}: {e}")
                resultado['detalles'].append({
                    'equipo': equipo.get('nombre', 'desconocido'),
                    'accion': 'error',
                    'error': str(e)
                })

        # Commit de los cambios
        conexion.commit()

    logger.info(
        f"Sincronización de equipos completada ({fuente}): "
        f"{resultado['insertados']} insertados, "
        f"{resultado['actualizados']} actualizados, "
        f"{resultado['sin_cambios']} sin cambios, "
        f"{resultado['errores']} errores"
    )

    return resultado


def obtener_equipo_por_sofascore_id(
    conexion,
    sofascore_id: int
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un equipo por su ID de Sofascore.

    Args:
        conexion: Conexión a la base de datos.
        sofascore_id: ID del equipo en Sofascore.

    Returns:
        Diccionario con datos del equipo o None si no existe.
    """
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, nombre, nombre_corto, nombre_normalizado,
                   sofascore_id, slug, activo
            FROM equipos_futbol
            WHERE sofascore_id = %s
            """,
            (sofascore_id,)
        )
        resultado = cursor.fetchone()

        if resultado:
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'nombre_corto': resultado[2],
                'nombre_normalizado': resultado[3],
                'sofascore_id': resultado[4],
                'slug': resultado[5],
                'activo': resultado[6],
            }

    return None


def obtener_equipo_por_nombre(
    conexion,
    nombre: str,
    buscar_similar: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un equipo por su nombre (exacto o similar).

    Args:
        conexion: Conexión a la base de datos.
        nombre: Nombre del equipo a buscar.
        buscar_similar: Si True, busca también por nombre normalizado.

    Returns:
        Diccionario con datos del equipo o None si no existe.
    """
    with conexion.cursor() as cursor:
        # Primero intentar búsqueda exacta
        cursor.execute(
            """
            SELECT id, nombre, nombre_corto, nombre_normalizado,
                   sofascore_id, slug, activo
            FROM equipos_futbol
            WHERE nombre = %s OR nombre_corto = %s
            """,
            (nombre, nombre)
        )
        resultado = cursor.fetchone()

        if resultado:
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'nombre_corto': resultado[2],
                'nombre_normalizado': resultado[3],
                'sofascore_id': resultado[4],
                'slug': resultado[5],
                'activo': resultado[6],
            }

        # Si no hay coincidencia exacta, buscar por nombre normalizado
        if buscar_similar:
            nombre_norm = normalizar_nombre_equipo(nombre)
            cursor.execute(
                """
                SELECT id, nombre, nombre_corto, nombre_normalizado,
                       sofascore_id, slug, activo
                FROM equipos_futbol
                WHERE nombre_normalizado = %s
                """,
                (nombre_norm,)
            )
            resultado = cursor.fetchone()

            if resultado:
                return {
                    'id': resultado[0],
                    'nombre': resultado[1],
                    'nombre_corto': resultado[2],
                    'nombre_normalizado': resultado[3],
                    'sofascore_id': resultado[4],
                    'slug': resultado[5],
                    'activo': resultado[6],
                }

    return None
