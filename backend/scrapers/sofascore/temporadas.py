# -*- coding: utf-8 -*-
"""
Extractor de temporadas desde Sofascore.

Este módulo proporciona funciones para obtener y sincronizar información
de temporadas de las ligas de fútbol desde la API de Sofascore.

Funciones principales:
- obtener_temporadas_liga: Obtiene la lista de temporadas de una liga
- convertir_nombre_temporada: Convierte el formato de nombre de Sofascore
- sincronizar_temporadas: Sincroniza temporadas con la base de datos

Ejemplo de uso:
    from scrapers.sofascore.cliente import SofascoreClient
    from scrapers.sofascore.temporadas import obtener_temporadas_liga

    cliente = SofascoreClient()
    temporadas = obtener_temporadas_liga(cliente, liga_id=8)
    for temp in temporadas:
        print(f"{temp['nombre']}: ID {temp['id']}")
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .excepciones import DatosIncompletos, SofascoreError

if TYPE_CHECKING:
    from .cliente import SofascoreClient

# Configuración del logger
logger = logging.getLogger(__name__)


def obtener_temporadas_liga(
    cliente: 'SofascoreClient',
    liga_id: int
) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de temporadas de una liga desde Sofascore.

    Consulta el endpoint de temporadas de Sofascore y parsea la respuesta
    para extraer información estructurada de cada temporada.

    Args:
        cliente: Instancia de SofascoreClient para realizar peticiones.
        liga_id: ID de la liga en Sofascore (ej: 8 para La Liga).

    Returns:
        Lista de diccionarios con información de cada temporada, ordenada
        por año en orden descendente (más reciente primero). Cada diccionario
        contiene:
        - id: int - ID de la temporada en Sofascore
        - name: str - Nombre original de la temporada
        - year: str - Año o rango de años (ej: "24/25" o "2024")
        - nombre_normalizado: str - Nombre en formato estándar "2024-25"
        - anio_inicio: int - Año de inicio de la temporada
        - anio_fin: int - Año de fin de la temporada

    Raises:
        SofascoreError: Si hay un error al consultar Sofascore.
        DatosIncompletos: Si la respuesta no tiene el formato esperado.

    Ejemplo:
        cliente = SofascoreClient()
        temporadas = obtener_temporadas_liga(cliente, 8)

        # Obtener solo las últimas 3 temporadas
        ultimas = temporadas[:3]
        for t in ultimas:
            print(f"Temporada {t['nombre_normalizado']} (ID: {t['id']})")
    """
    endpoint = f"/unique-tournament/{liga_id}/seasons"

    logger.debug(f"Obteniendo temporadas de liga {liga_id}")

    datos = cliente.get(endpoint)

    if datos is None:
        raise SofascoreError(
            mensaje=f"No se pudo obtener temporadas de la liga {liga_id}",
            detalles={'liga_id': liga_id, 'endpoint': endpoint}
        )

    if 'seasons' not in datos:
        raise DatosIncompletos(
            mensaje="La respuesta de Sofascore no contiene 'seasons'",
            campos_faltantes=['seasons'],
            tipo_datos='temporadas',
            datos_recibidos=datos
        )

    temporadas_raw = datos['seasons']
    temporadas = []

    for temp_json in temporadas_raw:
        try:
            temporada = _parsear_temporada(temp_json)
            temporadas.append(temporada)
        except Exception as e:
            logger.warning(
                f"Error al parsear temporada: {e}. "
                f"Datos: {temp_json}"
            )
            continue

    # Ordenar por año de inicio descendente (más reciente primero)
    temporadas.sort(key=lambda x: x.get('anio_inicio', 0), reverse=True)

    logger.info(
        f"Obtenidas {len(temporadas)} temporadas de liga {liga_id}"
    )

    return temporadas


def _parsear_temporada(temp_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parsea el JSON de una temporada de Sofascore.

    Args:
        temp_json: Diccionario con datos de la temporada desde la API.

    Returns:
        Diccionario con datos estructurados de la temporada.

    Raises:
        DatosIncompletos: Si faltan campos requeridos.
    """
    # Verificar campos requeridos
    if 'id' not in temp_json:
        raise DatosIncompletos(
            mensaje="Temporada sin ID",
            campos_faltantes=['id'],
            tipo_datos='temporada',
            datos_recibidos=temp_json
        )

    temporada_id = temp_json['id']
    nombre = temp_json.get('name', '')
    year = temp_json.get('year', '')

    # Convertir nombre al formato normalizado
    nombre_normalizado, anio_inicio, anio_fin = convertir_nombre_temporada(
        nombre, year
    )

    return {
        'id': temporada_id,
        'name': nombre,
        'year': str(year) if year else '',
        'nombre_normalizado': nombre_normalizado,
        'anio_inicio': anio_inicio,
        'anio_fin': anio_fin,
    }


def convertir_nombre_temporada(
    nombre_sofascore: str,
    year: Optional[str] = None
) -> Tuple[str, int, int]:
    """
    Convierte el formato de nombre de temporada de Sofascore al formato estándar.

    Sofascore usa varios formatos según la liga:
    - "LaLiga 24/25" → "2024-25"
    - "Premier League 2024/2025" → "2024-25"
    - "LaLiga 23/24" → "2023-24"
    - "Serie A 2023-2024" → "2023-24"
    - "2024" (año único) → "2024-25"

    Args:
        nombre_sofascore: Nombre de la temporada como viene de Sofascore.
        year: Campo year de Sofascore (puede ser "24/25", "2024", etc.).

    Returns:
        Tupla con:
        - nombre_normalizado: str en formato "2024-25"
        - anio_inicio: int del año de inicio (ej: 2024)
        - anio_fin: int del año de fin (ej: 2025)

    Ejemplo:
        nombre, inicio, fin = convertir_nombre_temporada("LaLiga 24/25")
        # Retorna: ("2024-25", 2024, 2025)

        nombre, inicio, fin = convertir_nombre_temporada("Serie A 2023-2024")
        # Retorna: ("2023-24", 2023, 2024)
    """
    # Primero intentar extraer del campo year si está disponible
    if year:
        year_str = str(year)

        # Formato "24/25" o "24-25"
        match = re.search(r'(\d{2})[/-](\d{2})$', year_str)
        if match:
            anio_corto_inicio = int(match.group(1))
            anio_corto_fin = int(match.group(2))

            # Determinar siglo
            anio_actual = datetime.now().year
            siglo = (anio_actual // 100) * 100

            # Si el año de inicio es mayor que los últimos 2 dígitos del año actual + 10,
            # probablemente es del siglo anterior
            if anio_corto_inicio > (anio_actual % 100) + 10:
                siglo -= 100

            anio_inicio = siglo + anio_corto_inicio
            anio_fin = siglo + anio_corto_fin

            # Manejar cambio de siglo (99 -> 00)
            if anio_corto_fin < anio_corto_inicio:
                anio_fin += 100

            nombre_normalizado = f"{anio_inicio}-{anio_corto_fin:02d}"
            return nombre_normalizado, anio_inicio, anio_fin

        # Formato "2024/2025" o "2024-2025"
        match = re.search(r'(\d{4})[/-](\d{4})', year_str)
        if match:
            anio_inicio = int(match.group(1))
            anio_fin = int(match.group(2))
            anio_corto_fin = anio_fin % 100
            nombre_normalizado = f"{anio_inicio}-{anio_corto_fin:02d}"
            return nombre_normalizado, anio_inicio, anio_fin

        # Formato año único "2024"
        match = re.search(r'^(\d{4})$', year_str)
        if match:
            anio_inicio = int(match.group(1))
            anio_fin = anio_inicio + 1
            anio_corto_fin = anio_fin % 100
            nombre_normalizado = f"{anio_inicio}-{anio_corto_fin:02d}"
            return nombre_normalizado, anio_inicio, anio_fin

    # Intentar extraer del nombre de la temporada
    # Formato "LaLiga 24/25" o similar
    match = re.search(r'(\d{2})[/-](\d{2})(?:\s|$)', nombre_sofascore)
    if match:
        anio_corto_inicio = int(match.group(1))
        anio_corto_fin = int(match.group(2))

        anio_actual = datetime.now().year
        siglo = (anio_actual // 100) * 100

        if anio_corto_inicio > (anio_actual % 100) + 10:
            siglo -= 100

        anio_inicio = siglo + anio_corto_inicio
        anio_fin = siglo + anio_corto_fin

        if anio_corto_fin < anio_corto_inicio:
            anio_fin += 100

        nombre_normalizado = f"{anio_inicio}-{anio_corto_fin:02d}"
        return nombre_normalizado, anio_inicio, anio_fin

    # Formato "2024/2025" o "2024-2025" en el nombre
    match = re.search(r'(\d{4})[/-](\d{4})', nombre_sofascore)
    if match:
        anio_inicio = int(match.group(1))
        anio_fin = int(match.group(2))
        anio_corto_fin = anio_fin % 100
        nombre_normalizado = f"{anio_inicio}-{anio_corto_fin:02d}"
        return nombre_normalizado, anio_inicio, anio_fin

    # Formato año único en el nombre
    match = re.search(r'(\d{4})', nombre_sofascore)
    if match:
        anio_inicio = int(match.group(1))
        anio_fin = anio_inicio + 1
        anio_corto_fin = anio_fin % 100
        nombre_normalizado = f"{anio_inicio}-{anio_corto_fin:02d}"
        return nombre_normalizado, anio_inicio, anio_fin

    # Si no se puede determinar, usar año actual
    logger.warning(
        f"No se pudo determinar años de temporada: '{nombre_sofascore}'. "
        f"Usando año actual."
    )
    anio_actual = datetime.now().year
    anio_fin = anio_actual + 1 if datetime.now().month >= 7 else anio_actual
    anio_inicio = anio_fin - 1
    anio_corto_fin = anio_fin % 100
    nombre_normalizado = f"{anio_inicio}-{anio_corto_fin:02d}"

    return nombre_normalizado, anio_inicio, anio_fin


def estimar_fechas_temporada(
    anio_inicio: int,
    anio_fin: int,
    tipo_competicion: str = 'liga'
) -> Tuple[date, date]:
    """
    Estima las fechas de inicio y fin de una temporada.

    Las ligas europeas típicamente corren de agosto a mayo.
    Las copas pueden tener calendarios diferentes.

    Args:
        anio_inicio: Año de inicio de la temporada.
        anio_fin: Año de fin de la temporada.
        tipo_competicion: 'liga' o 'copa' para ajustar las fechas.

    Returns:
        Tupla con (fecha_inicio, fecha_fin) como objetos date.

    Ejemplo:
        inicio, fin = estimar_fechas_temporada(2024, 2025)
        # Retorna: (date(2024, 8, 1), date(2025, 5, 31))
    """
    if tipo_competicion == 'copa':
        # Las copas suelen empezar un poco después y terminar en mayo/junio
        fecha_inicio = date(anio_inicio, 9, 1)
        fecha_fin = date(anio_fin, 6, 30)
    else:
        # Ligas: agosto a mayo
        fecha_inicio = date(anio_inicio, 8, 1)
        fecha_fin = date(anio_fin, 5, 31)

    return fecha_inicio, fecha_fin


def sincronizar_temporadas(
    conexion,
    cliente: 'SofascoreClient',
    liga_id: int,
    competicion_id: int,
    temporadas_a_sincronizar: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Sincroniza temporadas de Sofascore con la base de datos.

    Para cada temporada obtenida de Sofascore:
    1. Verifica si ya existe en la tabla temporadas_futbol
    2. Si no existe, inserta un nuevo registro
    3. Si existe, actualiza campos si es necesario
    4. Marca la temporada más reciente como activa

    Args:
        conexion: Conexión a la base de datos PostgreSQL.
        cliente: Instancia de SofascoreClient.
        liga_id: ID de la liga en Sofascore.
        competicion_id: ID de la competición en la tabla competiciones_futbol.
        temporadas_a_sincronizar: Lista opcional de nombres de temporadas
            a sincronizar (ej: ["2024-25", "2023-24"]). Si es None,
            sincroniza todas las temporadas disponibles.

    Returns:
        Diccionario con resumen de la sincronización:
        - insertadas: int - Número de temporadas insertadas
        - actualizadas: int - Número de temporadas actualizadas
        - sin_cambios: int - Número de temporadas sin cambios
        - errores: int - Número de errores
        - temporada_activa_id: int o None - ID de la temporada marcada como activa

    Raises:
        SofascoreError: Si hay un error al obtener temporadas de Sofascore.

    Ejemplo:
        from backend.db import obtener_pool

        with obtener_pool().connection() as conn:
            resultado = sincronizar_temporadas(
                conn, cliente, liga_id=8, competicion_id=1,
                temporadas_a_sincronizar=["2024-25", "2023-24"]
            )
            print(f"Insertadas: {resultado['insertadas']}")
    """
    logger.info(
        f"Sincronizando temporadas: liga_id={liga_id}, competicion_id={competicion_id}"
    )

    # Obtener temporadas de Sofascore
    temporadas_sofascore = obtener_temporadas_liga(cliente, liga_id)

    # Filtrar si se especificaron temporadas específicas
    if temporadas_a_sincronizar:
        temporadas_sofascore = [
            t for t in temporadas_sofascore
            if t['nombre_normalizado'] in temporadas_a_sincronizar
        ]
        logger.debug(
            f"Filtradas a {len(temporadas_sofascore)} temporadas: "
            f"{temporadas_a_sincronizar}"
        )

    resultado = {
        'insertadas': 0,
        'actualizadas': 0,
        'sin_cambios': 0,
        'errores': 0,
        'temporada_activa_id': None,
        'detalles': [],
    }

    temporada_mas_reciente_id = None
    anio_mas_reciente = 0

    with conexion.cursor() as cursor:
        for temp in temporadas_sofascore:
            try:
                sofascore_id = temp['id']
                nombre = temp['nombre_normalizado']
                anio_inicio = temp['anio_inicio']
                anio_fin = temp['anio_fin']

                # Estimar fechas
                fecha_inicio, fecha_fin = estimar_fechas_temporada(
                    anio_inicio, anio_fin
                )

                # Verificar si existe la temporada
                cursor.execute(
                    """
                    SELECT id, nombre, fecha_inicio, fecha_fin, activa,
                           sofascore_season_id
                    FROM temporadas_futbol
                    WHERE competicion_id = %s
                      AND (sofascore_season_id = %s OR nombre = %s)
                    """,
                    (competicion_id, sofascore_id, nombre)
                )
                existente = cursor.fetchone()

                if existente is None:
                    # Insertar nueva temporada
                    cursor.execute(
                        """
                        INSERT INTO temporadas_futbol (
                            competicion_id, nombre, anio_inicio, anio_fin,
                            fecha_inicio, fecha_fin, activa, sofascore_season_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            competicion_id, nombre, anio_inicio, anio_fin,
                            fecha_inicio, fecha_fin, False, sofascore_id
                        )
                    )
                    nuevo_id = cursor.fetchone()[0]
                    resultado['insertadas'] += 1
                    resultado['detalles'].append({
                        'temporada': nombre,
                        'accion': 'insertada',
                        'id': nuevo_id
                    })
                    logger.debug(f"Temporada insertada: {nombre} (ID: {nuevo_id})")

                    # Rastrear la más reciente
                    if anio_inicio > anio_mas_reciente:
                        anio_mas_reciente = anio_inicio
                        temporada_mas_reciente_id = nuevo_id

                else:
                    # Verificar si hay cambios
                    db_id = existente[0]
                    db_nombre = existente[1]
                    db_sofascore_id = existente[5]

                    cambios = []

                    # Actualizar sofascore_season_id si falta
                    if db_sofascore_id is None or db_sofascore_id != sofascore_id:
                        cambios.append(('sofascore_season_id', sofascore_id))

                    if cambios:
                        # Actualizar
                        set_clauses = [f"{campo} = %s" for campo, _ in cambios]
                        valores = [valor for _, valor in cambios]
                        valores.append(db_id)

                        cursor.execute(
                            f"""
                            UPDATE temporadas_futbol
                            SET {', '.join(set_clauses)}, actualizado_en = NOW()
                            WHERE id = %s
                            """,
                            valores
                        )
                        resultado['actualizadas'] += 1
                        resultado['detalles'].append({
                            'temporada': nombre,
                            'accion': 'actualizada',
                            'id': db_id,
                            'cambios': [c[0] for c in cambios]
                        })
                        logger.debug(f"Temporada actualizada: {nombre}")
                    else:
                        resultado['sin_cambios'] += 1

                    # Rastrear la más reciente
                    if anio_inicio > anio_mas_reciente:
                        anio_mas_reciente = anio_inicio
                        temporada_mas_reciente_id = db_id

            except Exception as e:
                resultado['errores'] += 1
                logger.error(f"Error sincronizando temporada {temp}: {e}")
                resultado['detalles'].append({
                    'temporada': temp.get('nombre_normalizado', 'desconocida'),
                    'accion': 'error',
                    'error': str(e)
                })

        # Marcar la temporada más reciente como activa
        if temporada_mas_reciente_id:
            # Primero desactivar todas las temporadas de esta competición
            cursor.execute(
                """
                UPDATE temporadas_futbol
                SET activa = FALSE
                WHERE competicion_id = %s AND activa = TRUE
                """,
                (competicion_id,)
            )

            # Activar la más reciente
            cursor.execute(
                """
                UPDATE temporadas_futbol
                SET activa = TRUE
                WHERE id = %s
                """,
                (temporada_mas_reciente_id,)
            )
            resultado['temporada_activa_id'] = temporada_mas_reciente_id
            logger.info(
                f"Temporada activa establecida: ID {temporada_mas_reciente_id}"
            )

        # Commit de los cambios
        conexion.commit()

    logger.info(
        f"Sincronización completada: "
        f"{resultado['insertadas']} insertadas, "
        f"{resultado['actualizadas']} actualizadas, "
        f"{resultado['sin_cambios']} sin cambios, "
        f"{resultado['errores']} errores"
    )

    return resultado


def obtener_temporada_activa(
    conexion,
    competicion_id: int
) -> Optional[Dict[str, Any]]:
    """
    Obtiene la temporada activa de una competición.

    Args:
        conexion: Conexión a la base de datos.
        competicion_id: ID de la competición.

    Returns:
        Diccionario con datos de la temporada activa o None si no hay ninguna.
    """
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin,
                   sofascore_season_id
            FROM temporadas_futbol
            WHERE competicion_id = %s AND activa = TRUE
            """,
            (competicion_id,)
        )
        resultado = cursor.fetchone()

        if resultado:
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'anio_inicio': resultado[2],
                'anio_fin': resultado[3],
                'fecha_inicio': resultado[4],
                'fecha_fin': resultado[5],
                'sofascore_season_id': resultado[6],
            }

    return None


def obtener_temporada_por_nombre(
    conexion,
    competicion_id: int,
    nombre_temporada: str
) -> Optional[Dict[str, Any]]:
    """
    Obtiene una temporada por su nombre normalizado.

    Args:
        conexion: Conexión a la base de datos.
        competicion_id: ID de la competición.
        nombre_temporada: Nombre de la temporada (ej: "2024-25").

    Returns:
        Diccionario con datos de la temporada o None si no existe.
    """
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin,
                   sofascore_season_id, activa
            FROM temporadas_futbol
            WHERE competicion_id = %s AND nombre = %s
            """,
            (competicion_id, nombre_temporada)
        )
        resultado = cursor.fetchone()

        if resultado:
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'anio_inicio': resultado[2],
                'anio_fin': resultado[3],
                'fecha_inicio': resultado[4],
                'fecha_fin': resultado[5],
                'sofascore_season_id': resultado[6],
                'activa': resultado[7],
            }

    return None
