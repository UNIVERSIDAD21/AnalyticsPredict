# -*- coding: utf-8 -*-
"""
Extractor de partidos básicos desde Sofascore.

Este módulo proporciona funciones para obtener información de partidos
de fútbol sin estadísticas detalladas. Los partidos incluyen información
básica como equipos, goles por tiempo, estado y jornada.

Funciones principales:
- obtener_partidos_pasados: Obtiene partidos ya jugados
- obtener_partidos_futuros: Obtiene partidos programados
- parsear_partido: Convierte JSON de Sofascore a PartidoBasico

Ejemplo de uso:
    from scrapers.sofascore.cliente import SofascoreClient
    from scrapers.sofascore.partidos import obtener_partidos_pasados

    cliente = SofascoreClient()
    partidos = obtener_partidos_pasados(cliente, liga_id=8, temporada_id=52376)
    for p in partidos:
        print(f"{p.equipo_local_nombre} {p.goles_local_total} - "
              f"{p.goles_visitante_total} {p.equipo_visitante_nombre}")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .excepciones import DatosIncompletos, SofascoreError

if TYPE_CHECKING:
    from .cliente import SofascoreClient

# Configuración del logger
logger = logging.getLogger(__name__)

# Mapeo de estados de Sofascore a estados internos
MAPEO_ESTADOS = {
    'finished': 'finished',
    'ended': 'finished',
    'notstarted': 'notstarted',
    'not_started': 'notstarted',
    'inprogress': 'inprogress',
    'in_progress': 'inprogress',
    '1st_half': 'inprogress',
    '2nd_half': 'inprogress',
    'halftime': 'inprogress',
    'postponed': 'postponed',
    'canceled': 'cancelled',
    'cancelled': 'cancelled',
    'suspended': 'suspended',
    'awarded': 'finished',
    'aet': 'finished',  # After Extra Time
    'pen': 'finished',  # Penalties
    'walkover': 'finished',
}


@dataclass
class PartidoBasico:
    """
    Representa un partido de fútbol con datos básicos.

    Esta clase contiene la información esencial de un partido sin
    estadísticas detalladas como corners o disparos. Es el formato
    usado para listar partidos antes de obtener estadísticas completas.

    Atributos:
        sofascore_id: ID único del partido en Sofascore.
        fecha_timestamp: Timestamp Unix del partido (segundos).
        fecha_partido: Fecha y hora del partido como datetime.
        equipo_local_id: ID del equipo local en Sofascore.
        equipo_local_nombre: Nombre completo del equipo local.
        equipo_local_nombre_corto: Nombre abreviado del equipo local.
        equipo_visitante_id: ID del equipo visitante en Sofascore.
        equipo_visitante_nombre: Nombre completo del equipo visitante.
        equipo_visitante_nombre_corto: Nombre abreviado del equipo visitante.
        goles_local_1t: Goles del equipo local en el primer tiempo.
        goles_local_2t: Goles del equipo local en el segundo tiempo.
        goles_local_total: Total de goles del equipo local.
        goles_visitante_1t: Goles del equipo visitante en el primer tiempo.
        goles_visitante_2t: Goles del equipo visitante en el segundo tiempo.
        goles_visitante_total: Total de goles del equipo visitante.
        estado: Estado del partido (finished, notstarted, inprogress, etc.).
        jornada: Número de jornada si está disponible.
        tiene_prorroga: Si el partido tuvo tiempo extra.
        tiene_penales: Si el partido se decidió por penales.
    """
    sofascore_id: int
    fecha_timestamp: int
    fecha_partido: datetime
    equipo_local_id: int
    equipo_local_nombre: str
    equipo_local_nombre_corto: str
    equipo_visitante_id: int
    equipo_visitante_nombre: str
    equipo_visitante_nombre_corto: str
    goles_local_1t: Optional[int] = None
    goles_local_2t: Optional[int] = None
    goles_local_total: Optional[int] = None
    goles_visitante_1t: Optional[int] = None
    goles_visitante_2t: Optional[int] = None
    goles_visitante_total: Optional[int] = None
    estado: str = 'notstarted'
    jornada: Optional[int] = None
    tiene_prorroga: bool = False
    tiene_penales: bool = False
    slug: str = ''

    def esta_finalizado(self) -> bool:
        """Retorna True si el partido ha terminado."""
        return self.estado == 'finished'

    def esta_programado(self) -> bool:
        """Retorna True si el partido aún no ha comenzado."""
        return self.estado == 'notstarted'

    def esta_en_curso(self) -> bool:
        """Retorna True si el partido está en progreso."""
        return self.estado == 'inprogress'

    def obtener_resultado(self) -> str:
        """
        Retorna el resultado en formato "X-Y" o "vs" si no ha comenzado.
        """
        if self.goles_local_total is not None and self.goles_visitante_total is not None:
            return f"{self.goles_local_total}-{self.goles_visitante_total}"
        return "vs"

    def obtener_ganador(self) -> Optional[str]:
        """
        Retorna 'local', 'visitante', 'empate' o None si no ha terminado.
        """
        if not self.esta_finalizado():
            return None

        if self.goles_local_total is None or self.goles_visitante_total is None:
            return None

        if self.goles_local_total > self.goles_visitante_total:
            return 'local'
        elif self.goles_visitante_total > self.goles_local_total:
            return 'visitante'
        else:
            return 'empate'

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el partido a diccionario."""
        return {
            'sofascore_id': self.sofascore_id,
            'fecha_timestamp': self.fecha_timestamp,
            'fecha_partido': self.fecha_partido.isoformat(),
            'equipo_local_id': self.equipo_local_id,
            'equipo_local_nombre': self.equipo_local_nombre,
            'equipo_local_nombre_corto': self.equipo_local_nombre_corto,
            'equipo_visitante_id': self.equipo_visitante_id,
            'equipo_visitante_nombre': self.equipo_visitante_nombre,
            'equipo_visitante_nombre_corto': self.equipo_visitante_nombre_corto,
            'goles_local_1t': self.goles_local_1t,
            'goles_local_2t': self.goles_local_2t,
            'goles_local_total': self.goles_local_total,
            'goles_visitante_1t': self.goles_visitante_1t,
            'goles_visitante_2t': self.goles_visitante_2t,
            'goles_visitante_total': self.goles_visitante_total,
            'estado': self.estado,
            'jornada': self.jornada,
            'tiene_prorroga': self.tiene_prorroga,
            'tiene_penales': self.tiene_penales,
        }


def obtener_partidos_pasados(
    cliente: 'SofascoreClient',
    liga_id: int,
    temporada_id: int,
    desde_fecha: Optional[datetime] = None,
    hasta_fecha: Optional[datetime] = None,
    limite_paginas: int = 50
) -> List[PartidoBasico]:
    """
    Obtiene la lista de partidos pasados de una temporada.

    Consulta el endpoint de eventos pasados de Sofascore con paginación,
    comenzando desde la página 0 y continuando hasta que no haya más
    partidos o se alcance el límite de páginas.

    Args:
        cliente: Instancia de SofascoreClient.
        liga_id: ID de la liga en Sofascore.
        temporada_id: ID de la temporada en Sofascore.
        desde_fecha: Fecha mínima de los partidos (opcional).
                    Partidos anteriores a esta fecha serán ignorados.
        hasta_fecha: Fecha máxima de los partidos (opcional).
                    Partidos posteriores a esta fecha serán ignorados.
        limite_paginas: Máximo número de páginas a consultar (default: 50).
                       Cada página contiene aproximadamente 20 partidos.

    Returns:
        Lista de PartidoBasico ordenada por fecha descendente
        (más recientes primero).

    Raises:
        SofascoreError: Si hay un error al consultar Sofascore.

    Ejemplo:
        # Obtener todos los partidos de La Liga 2024-25
        partidos = obtener_partidos_pasados(cliente, 8, 52376)

        # Obtener solo partidos del último mes
        desde = datetime.now() - timedelta(days=30)
        partidos = obtener_partidos_pasados(cliente, 8, 52376, desde_fecha=desde)
    """
    logger.info(
        f"Obteniendo partidos pasados: liga={liga_id}, temporada={temporada_id}"
    )

    partidos: List[PartidoBasico] = []
    pagina = 0
    partidos_vistos = set()

    while pagina < limite_paginas:
        endpoint = (
            f"/unique-tournament/{liga_id}/season/{temporada_id}"
            f"/events/last/{pagina}"
        )

        logger.debug(f"Consultando página {pagina} de partidos pasados")

        datos = cliente.get(endpoint)

        if datos is None:
            logger.debug(f"Página {pagina} no encontrada, finalizando")
            break

        eventos = datos.get('events', [])

        if not eventos:
            logger.debug(f"Página {pagina} vacía, finalizando")
            break

        nuevos_partidos = 0
        partidos_fuera_rango = 0

        for evento in eventos:
            try:
                partido = parsear_partido(evento)

                # Evitar duplicados
                if partido.sofascore_id in partidos_vistos:
                    continue

                # Filtrar por fecha si se especificó
                if desde_fecha and partido.fecha_partido < desde_fecha:
                    partidos_fuera_rango += 1
                    continue

                if hasta_fecha and partido.fecha_partido > hasta_fecha:
                    partidos_fuera_rango += 1
                    continue

                partidos_vistos.add(partido.sofascore_id)
                partidos.append(partido)
                nuevos_partidos += 1

            except Exception as e:
                logger.warning(
                    f"Error parseando partido: {e}. "
                    f"ID: {evento.get('id', 'desconocido')}"
                )

        logger.debug(
            f"Página {pagina}: {nuevos_partidos} nuevos, "
            f"{partidos_fuera_rango} fuera de rango"
        )

        # Si todos los partidos de la página están fuera del rango de fechas,
        # podemos terminar (asumiendo que están ordenados por fecha)
        if nuevos_partidos == 0 and partidos_fuera_rango > 0:
            if desde_fecha and partidos:
                # Verificar si ya pasamos la fecha mínima
                ultimo_procesado = partidos[-1] if partidos else None
                if ultimo_procesado and ultimo_procesado.fecha_partido < desde_fecha:
                    logger.debug("Todos los partidos restantes están antes de desde_fecha")
                    break

        pagina += 1

    # Ordenar por fecha descendente
    partidos.sort(key=lambda p: p.fecha_partido, reverse=True)

    logger.info(
        f"Obtenidos {len(partidos)} partidos pasados de "
        f"liga={liga_id}, temporada={temporada_id}"
    )

    return partidos


def obtener_partidos_futuros(
    cliente: 'SofascoreClient',
    liga_id: int,
    temporada_id: int,
    limite_dias: int = 30,
    limite_paginas: int = 10
) -> List[PartidoBasico]:
    """
    Obtiene la lista de partidos futuros programados.

    Consulta el endpoint de eventos próximos de Sofascore.
    Los partidos futuros no tienen goles (serán None).

    Args:
        cliente: Instancia de SofascoreClient.
        liga_id: ID de la liga en Sofascore.
        temporada_id: ID de la temporada en Sofascore.
        limite_dias: Días hacia adelante para obtener partidos (default: 30).
        limite_paginas: Máximo número de páginas a consultar (default: 10).

    Returns:
        Lista de PartidoBasico ordenada por fecha ascendente
        (próximos primero).

    Ejemplo:
        # Obtener próximos partidos de La Liga
        proximos = obtener_partidos_futuros(cliente, 8, 52376)

        # Obtener solo partidos de la próxima semana
        proximos = obtener_partidos_futuros(cliente, 8, 52376, limite_dias=7)
    """
    logger.info(
        f"Obteniendo partidos futuros: liga={liga_id}, temporada={temporada_id}, "
        f"limite_dias={limite_dias}"
    )

    fecha_limite = datetime.now(timezone.utc) + timedelta(days=limite_dias)
    partidos: List[PartidoBasico] = []
    pagina = 0
    partidos_vistos = set()

    while pagina < limite_paginas:
        endpoint = (
            f"/unique-tournament/{liga_id}/season/{temporada_id}"
            f"/events/next/{pagina}"
        )

        logger.debug(f"Consultando página {pagina} de partidos futuros")

        datos = cliente.get(endpoint)

        if datos is None:
            logger.debug(f"Página {pagina} no encontrada, finalizando")
            break

        eventos = datos.get('events', [])

        if not eventos:
            logger.debug(f"Página {pagina} vacía, finalizando")
            break

        nuevos_partidos = 0
        partidos_fuera_limite = 0

        for evento in eventos:
            try:
                partido = parsear_partido(evento)

                # Evitar duplicados
                if partido.sofascore_id in partidos_vistos:
                    continue

                # Verificar si está dentro del límite de días
                if partido.fecha_partido > fecha_limite:
                    partidos_fuera_limite += 1
                    continue

                partidos_vistos.add(partido.sofascore_id)
                partidos.append(partido)
                nuevos_partidos += 1

            except Exception as e:
                logger.warning(
                    f"Error parseando partido futuro: {e}. "
                    f"ID: {evento.get('id', 'desconocido')}"
                )

        logger.debug(
            f"Página {pagina}: {nuevos_partidos} nuevos, "
            f"{partidos_fuera_limite} fuera de límite"
        )

        # Si todos los partidos están fuera del límite, terminar
        if nuevos_partidos == 0 and partidos_fuera_limite > 0:
            logger.debug("Todos los partidos restantes están fuera del límite de días")
            break

        pagina += 1

    # Ordenar por fecha ascendente
    partidos.sort(key=lambda p: p.fecha_partido)

    logger.info(
        f"Obtenidos {len(partidos)} partidos futuros de "
        f"liga={liga_id}, temporada={temporada_id}"
    )

    return partidos


def parsear_partido(evento_json: Dict[str, Any]) -> PartidoBasico:
    """
    Convierte el JSON de un evento de Sofascore a PartidoBasico.

    Extrae todos los campos relevantes del JSON y los mapea a la
    estructura interna de PartidoBasico.

    Args:
        evento_json: Diccionario con datos del evento desde la API.

    Returns:
        Objeto PartidoBasico con todos los campos mapeados.

    Raises:
        DatosIncompletos: Si faltan campos requeridos (id, equipos).

    Ejemplo:
        evento = {"id": 12345, "homeTeam": {...}, "awayTeam": {...}, ...}
        partido = parsear_partido(evento)
    """
    # Campos requeridos
    sofascore_id = evento_json.get('id')
    if sofascore_id is None:
        raise DatosIncompletos(
            mensaje="Evento sin ID",
            campos_faltantes=['id'],
            tipo_datos='partido'
        )

    # Equipos
    equipo_local = evento_json.get('homeTeam', {})
    equipo_visitante = evento_json.get('awayTeam', {})

    equipo_local_id = equipo_local.get('id')
    equipo_visitante_id = equipo_visitante.get('id')

    if equipo_local_id is None or equipo_visitante_id is None:
        raise DatosIncompletos(
            mensaje="Partido sin equipos",
            campos_faltantes=['homeTeam.id', 'awayTeam.id'],
            tipo_datos='partido'
        )

    # Nombres de equipos
    equipo_local_nombre = equipo_local.get('name', '')
    equipo_local_nombre_corto = equipo_local.get('shortName', equipo_local_nombre)
    equipo_visitante_nombre = equipo_visitante.get('name', '')
    equipo_visitante_nombre_corto = equipo_visitante.get('shortName', equipo_visitante_nombre)

    # Fecha del partido
    fecha_timestamp = evento_json.get('startTimestamp', 0)
    fecha_partido = datetime.fromtimestamp(fecha_timestamp, tz=timezone.utc)

    # Estado del partido
    status = evento_json.get('status', {})
    tipo_estado = status.get('type', 'notstarted').lower()
    estado = MAPEO_ESTADOS.get(tipo_estado, tipo_estado)

    # Goles
    goles_local_1t = None
    goles_local_2t = None
    goles_local_total = None
    goles_visitante_1t = None
    goles_visitante_2t = None
    goles_visitante_total = None
    tiene_prorroga = False
    tiene_penales = False

    home_score = evento_json.get('homeScore', {})
    away_score = evento_json.get('awayScore', {})

    if home_score and away_score:
        # Goles por tiempo
        goles_local_1t = home_score.get('period1')
        goles_local_2t = home_score.get('period2')
        goles_visitante_1t = away_score.get('period1')
        goles_visitante_2t = away_score.get('period2')

        # Total (puede ser 'current', 'display', o 'normaltime')
        goles_local_total = (
            home_score.get('current') or
            home_score.get('display') or
            home_score.get('normaltime')
        )
        goles_visitante_total = (
            away_score.get('current') or
            away_score.get('display') or
            away_score.get('normaltime')
        )

        # Detectar prórroga y penales
        if home_score.get('overtime') is not None:
            tiene_prorroga = True
        if home_score.get('penalties') is not None:
            tiene_penales = True

    # Jornada
    jornada = None
    round_info = evento_json.get('roundInfo', {})
    if round_info:
        jornada = round_info.get('round')

    # Slug para URL
    slug = evento_json.get('slug', '')

    return PartidoBasico(
        sofascore_id=sofascore_id,
        fecha_timestamp=fecha_timestamp,
        fecha_partido=fecha_partido,
        equipo_local_id=equipo_local_id,
        equipo_local_nombre=equipo_local_nombre,
        equipo_local_nombre_corto=equipo_local_nombre_corto,
        equipo_visitante_id=equipo_visitante_id,
        equipo_visitante_nombre=equipo_visitante_nombre,
        equipo_visitante_nombre_corto=equipo_visitante_nombre_corto,
        goles_local_1t=goles_local_1t,
        goles_local_2t=goles_local_2t,
        goles_local_total=goles_local_total,
        goles_visitante_1t=goles_visitante_1t,
        goles_visitante_2t=goles_visitante_2t,
        goles_visitante_total=goles_visitante_total,
        estado=estado,
        jornada=jornada,
        tiene_prorroga=tiene_prorroga,
        tiene_penales=tiene_penales,
        slug=slug,
    )


def obtener_partido_por_id(
    cliente: 'SofascoreClient',
    evento_id: int
) -> Optional[PartidoBasico]:
    """
    Obtiene un partido específico por su ID de Sofascore.

    Args:
        cliente: Instancia de SofascoreClient.
        evento_id: ID del evento en Sofascore.

    Returns:
        PartidoBasico con los datos del partido o None si no existe.

    Ejemplo:
        partido = obtener_partido_por_id(cliente, 12345678)
        if partido:
            print(f"Partido: {partido.equipo_local_nombre} vs {partido.equipo_visitante_nombre}")
    """
    endpoint = f"/event/{evento_id}"

    datos = cliente.get(endpoint)

    if datos is None:
        return None

    evento = datos.get('event', datos)

    try:
        return parsear_partido(evento)
    except Exception as e:
        logger.warning(f"Error parseando partido {evento_id}: {e}")
        return None


def obtener_partidos_por_fecha(
    cliente: 'SofascoreClient',
    fecha: datetime,
    liga_id: Optional[int] = None
) -> List[PartidoBasico]:
    """
    Obtiene todos los partidos de una fecha específica.

    Útil para sincronización diaria de resultados.

    Args:
        cliente: Instancia de SofascoreClient.
        fecha: Fecha de los partidos a obtener.
        liga_id: ID de liga opcional para filtrar (None = todas las ligas).

    Returns:
        Lista de partidos de esa fecha.
    """
    # Formatear fecha para Sofascore (YYYY-MM-DD)
    fecha_str = fecha.strftime('%Y-%m-%d')
    endpoint = f"/sport/football/scheduled-events/{fecha_str}"

    datos = cliente.get(endpoint)

    if datos is None:
        return []

    eventos = datos.get('events', [])
    partidos = []

    for evento in eventos:
        try:
            # Filtrar por liga si se especificó
            if liga_id:
                torneo = evento.get('tournament', {})
                unique_tournament = torneo.get('uniqueTournament', {})
                if unique_tournament.get('id') != liga_id:
                    continue

            partido = parsear_partido(evento)
            partidos.append(partido)

        except Exception as e:
            logger.warning(f"Error parseando partido de fecha {fecha_str}: {e}")

    logger.info(f"Obtenidos {len(partidos)} partidos para fecha {fecha_str}")

    return partidos


def filtrar_partidos_finalizados(
    partidos: List[PartidoBasico]
) -> List[PartidoBasico]:
    """
    Filtra una lista de partidos para obtener solo los finalizados.

    Args:
        partidos: Lista de partidos a filtrar.

    Returns:
        Lista con solo los partidos con estado 'finished'.
    """
    return [p for p in partidos if p.esta_finalizado()]


def filtrar_partidos_programados(
    partidos: List[PartidoBasico]
) -> List[PartidoBasico]:
    """
    Filtra una lista de partidos para obtener solo los programados.

    Args:
        partidos: Lista de partidos a filtrar.

    Returns:
        Lista con solo los partidos con estado 'notstarted'.
    """
    return [p for p in partidos if p.esta_programado()]
