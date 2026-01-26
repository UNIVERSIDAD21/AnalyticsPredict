# -*- coding: utf-8 -*-
"""
Extractor de estadísticas detalladas de partidos desde Sofascore.

Este módulo proporciona funciones para obtener estadísticas avanzadas
de partidos de fútbol, incluyendo corners, disparos, posesión y xG
(goles esperados) desglosados por tiempo.

Funciones principales:
- obtener_estadisticas_partido: Obtiene estadísticas de un partido
- parsear_estadisticas: Convierte JSON de Sofascore a EstadisticasPartido
- validar_consistencia_estadisticas: Valida integridad de los datos

Ejemplo de uso:
    from scrapers.sofascore.cliente import SofascoreClient
    from scrapers.sofascore.estadisticas import obtener_estadisticas_partido

    cliente = SofascoreClient()
    stats = obtener_estadisticas_partido(cliente, evento_id=12345678)
    if stats:
        print(f"Corners: {stats.corners_local_total} - {stats.corners_visitante_total}")
        print(f"xG: {stats.xg_local:.2f} - {stats.xg_visitante:.2f}")
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .excepciones import DatosIncompletos

if TYPE_CHECKING:
    from .cliente import SofascoreClient

# Configuración del logger
logger = logging.getLogger(__name__)

# Nombres de estadísticas en Sofascore (pueden variar por idioma/versión)
NOMBRES_CORNERS = ['Corner kicks', 'Corners', 'Tiros de esquina']
NOMBRES_DISPAROS_TOTAL = ['Total shots', 'Shots', 'Tiros totales', 'Total Shots']
NOMBRES_DISPAROS_ARCO = ['Shots on target', 'Shots on goal', 'Tiros a puerta', 'Shots On Target']
NOMBRES_POSESION = ['Ball possession', 'Possession', 'Posesión', 'Ball Possession']
NOMBRES_XG = ['Expected goals', 'xG', 'Goles esperados', 'Expected Goals']
NOMBRES_DISPAROS_FUERA = ['Shots off target', 'Shots off goal', 'Tiros fuera']
NOMBRES_TARJETAS_AMARILLAS = ['Yellow cards', 'Tarjetas amarillas']
NOMBRES_TARJETAS_ROJAS = ['Red cards', 'Tarjetas rojas']
NOMBRES_FALTAS = ['Fouls', 'Faltas']
NOMBRES_FUERA_JUEGO = ['Offsides', 'Fueras de juego']


@dataclass
class EstadisticasPartido:
    """
    Estadísticas detalladas de un partido de fútbol.

    Esta clase contiene todas las estadísticas avanzadas de un partido
    que se pueden obtener de Sofascore, desglosadas por tiempo cuando
    están disponibles.

    Atributos de Corners:
        corners_local_1t: Corners del equipo local en el primer tiempo.
        corners_local_2t: Corners del equipo local en el segundo tiempo.
        corners_local_total: Total de corners del equipo local.
        corners_visitante_1t: Corners del equipo visitante en el primer tiempo.
        corners_visitante_2t: Corners del equipo visitante en el segundo tiempo.
        corners_visitante_total: Total de corners del equipo visitante.

    Atributos de Disparos:
        disparos_local_total: Total de disparos del equipo local.
        disparos_local_arco: Disparos al arco del equipo local.
        disparos_visitante_total: Total de disparos del equipo visitante.
        disparos_visitante_arco: Disparos al arco del equipo visitante.

    Atributos de Posesión:
        posesion_local: Porcentaje de posesión del equipo local.
        posesion_visitante: Porcentaje de posesión del equipo visitante.

    Atributos de xG (Goles Esperados):
        xg_local: xG del equipo local.
        xg_visitante: xG del equipo visitante.

    Flags de Completitud:
        datos_completos: True si todas las estadísticas están disponibles.
        datos_corners_completos: True si corners por tiempo están disponibles.
        datos_disparos_completos: True si estadísticas de disparos disponibles.
        datos_xg_disponible: True si xG está disponible.
    """
    # Corners
    corners_local_1t: Optional[int] = None
    corners_local_2t: Optional[int] = None
    corners_local_total: Optional[int] = None
    corners_visitante_1t: Optional[int] = None
    corners_visitante_2t: Optional[int] = None
    corners_visitante_total: Optional[int] = None

    # Disparos
    disparos_local_total: Optional[int] = None
    disparos_local_arco: Optional[int] = None
    disparos_visitante_total: Optional[int] = None
    disparos_visitante_arco: Optional[int] = None
    disparos_local_fuera: Optional[int] = None
    disparos_visitante_fuera: Optional[int] = None

    # Posesión
    posesion_local: Optional[float] = None
    posesion_visitante: Optional[float] = None

    # xG
    xg_local: Optional[float] = None
    xg_visitante: Optional[float] = None

    # Estadísticas adicionales
    tarjetas_amarillas_local: Optional[int] = None
    tarjetas_amarillas_visitante: Optional[int] = None
    tarjetas_rojas_local: Optional[int] = None
    tarjetas_rojas_visitante: Optional[int] = None
    faltas_local: Optional[int] = None
    faltas_visitante: Optional[int] = None
    fuera_juego_local: Optional[int] = None
    fuera_juego_visitante: Optional[int] = None

    # Flags de completitud
    datos_completos: bool = False
    datos_corners_completos: bool = False
    datos_disparos_completos: bool = False
    datos_xg_disponible: bool = False

    def tiene_corners(self) -> bool:
        """Retorna True si tiene datos de corners totales."""
        return (
            self.corners_local_total is not None and
            self.corners_visitante_total is not None
        )

    def tiene_corners_por_tiempo(self) -> bool:
        """Retorna True si tiene corners desglosados por tiempo."""
        return (
            self.corners_local_1t is not None and
            self.corners_local_2t is not None and
            self.corners_visitante_1t is not None and
            self.corners_visitante_2t is not None
        )

    def tiene_disparos(self) -> bool:
        """Retorna True si tiene datos de disparos."""
        return (
            self.disparos_local_total is not None and
            self.disparos_visitante_total is not None
        )

    def tiene_xg(self) -> bool:
        """Retorna True si tiene datos de xG."""
        return (
            self.xg_local is not None and
            self.xg_visitante is not None
        )

    def tiene_posesion(self) -> bool:
        """Retorna True si tiene datos de posesión."""
        return (
            self.posesion_local is not None and
            self.posesion_visitante is not None
        )

    def total_corners(self) -> Optional[int]:
        """Retorna el total de corners del partido."""
        if self.corners_local_total is not None and self.corners_visitante_total is not None:
            return self.corners_local_total + self.corners_visitante_total
        return None

    def total_disparos(self) -> Optional[int]:
        """Retorna el total de disparos del partido."""
        if self.disparos_local_total is not None and self.disparos_visitante_total is not None:
            return self.disparos_local_total + self.disparos_visitante_total
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte las estadísticas a diccionario."""
        return {
            'corners_local_1t': self.corners_local_1t,
            'corners_local_2t': self.corners_local_2t,
            'corners_local_total': self.corners_local_total,
            'corners_visitante_1t': self.corners_visitante_1t,
            'corners_visitante_2t': self.corners_visitante_2t,
            'corners_visitante_total': self.corners_visitante_total,
            'disparos_local_total': self.disparos_local_total,
            'disparos_local_arco': self.disparos_local_arco,
            'disparos_visitante_total': self.disparos_visitante_total,
            'disparos_visitante_arco': self.disparos_visitante_arco,
            'posesion_local': self.posesion_local,
            'posesion_visitante': self.posesion_visitante,
            'xg_local': self.xg_local,
            'xg_visitante': self.xg_visitante,
            'datos_completos': self.datos_completos,
            'datos_corners_completos': self.datos_corners_completos,
            'datos_disparos_completos': self.datos_disparos_completos,
            'datos_xg_disponible': self.datos_xg_disponible,
        }


def obtener_estadisticas_partido(
    cliente: 'SofascoreClient',
    evento_id: int
) -> Optional[EstadisticasPartido]:
    """
    Obtiene las estadísticas detalladas de un partido.

    Consulta el endpoint de estadísticas de Sofascore y parsea la
    respuesta para extraer corners, disparos, posesión y xG.

    Args:
        cliente: Instancia de SofascoreClient.
        evento_id: ID del evento/partido en Sofascore.

    Returns:
        EstadisticasPartido con todos los datos disponibles, o None
        si el partido no tiene estadísticas (404 o sin datos).

    Ejemplo:
        stats = obtener_estadisticas_partido(cliente, 12345678)
        if stats:
            print(f"Corners totales: {stats.total_corners()}")
            if stats.tiene_xg():
                print(f"xG: {stats.xg_local:.2f} vs {stats.xg_visitante:.2f}")
    """
    endpoint = f"/event/{evento_id}/statistics"

    logger.debug(f"Obteniendo estadísticas del partido {evento_id}")

    datos = cliente.get(endpoint)

    if datos is None:
        logger.debug(f"No hay estadísticas para el partido {evento_id}")
        return None

    statistics = datos.get('statistics', [])

    if not statistics:
        logger.debug(f"Respuesta vacía de estadísticas para partido {evento_id}")
        return None

    try:
        return parsear_estadisticas(statistics)
    except Exception as e:
        logger.warning(f"Error parseando estadísticas del partido {evento_id}: {e}")
        return None


def parsear_estadisticas(estadisticas_json: List[Dict[str, Any]]) -> EstadisticasPartido:
    """
    Parsea el JSON de estadísticas de Sofascore.

    La estructura de Sofascore tiene períodos (ALL, 1ST, 2ND) y dentro
    de cada período hay grupos con estadísticas individuales.

    Args:
        estadisticas_json: Lista de períodos con estadísticas.

    Returns:
        EstadisticasPartido con todos los datos extraídos.

    Ejemplo de estructura esperada:
        [
            {
                "period": "ALL",
                "groups": [
                    {
                        "groupName": "Match overview",
                        "statisticsItems": [
                            {"name": "Ball possession", "home": "55%", "away": "45%"},
                            {"name": "Corner kicks", "home": "6", "away": "4"},
                            ...
                        ]
                    },
                    ...
                ]
            },
            {
                "period": "1ST",
                "groups": [...]
            },
            ...
        ]
    """
    stats = EstadisticasPartido()

    # Organizar datos por período
    periodos = {}
    for periodo_data in estadisticas_json:
        periodo = periodo_data.get('period', '').upper()
        if periodo:
            periodos[periodo] = periodo_data.get('groups', [])

    # Extraer estadísticas del período completo (ALL)
    if 'ALL' in periodos:
        grupos = periodos['ALL']

        # Corners totales
        corners = buscar_estadistica_en_grupos(grupos, NOMBRES_CORNERS)
        if corners[0] is not None:
            stats.corners_local_total = _parsear_entero(corners[0])
            stats.corners_visitante_total = _parsear_entero(corners[1])

        # Disparos totales
        disparos = buscar_estadistica_en_grupos(grupos, NOMBRES_DISPAROS_TOTAL)
        if disparos[0] is not None:
            stats.disparos_local_total = _parsear_entero(disparos[0])
            stats.disparos_visitante_total = _parsear_entero(disparos[1])

        # Disparos al arco
        disparos_arco = buscar_estadistica_en_grupos(grupos, NOMBRES_DISPAROS_ARCO)
        if disparos_arco[0] is not None:
            stats.disparos_local_arco = _parsear_entero(disparos_arco[0])
            stats.disparos_visitante_arco = _parsear_entero(disparos_arco[1])

        # Disparos fuera
        disparos_fuera = buscar_estadistica_en_grupos(grupos, NOMBRES_DISPAROS_FUERA)
        if disparos_fuera[0] is not None:
            stats.disparos_local_fuera = _parsear_entero(disparos_fuera[0])
            stats.disparos_visitante_fuera = _parsear_entero(disparos_fuera[1])

        # Posesión
        posesion = buscar_estadistica_en_grupos(grupos, NOMBRES_POSESION)
        if posesion[0] is not None:
            stats.posesion_local = _parsear_porcentaje(posesion[0])
            stats.posesion_visitante = _parsear_porcentaje(posesion[1])

        # xG
        xg = buscar_estadistica_en_grupos(grupos, NOMBRES_XG)
        if xg[0] is not None:
            stats.xg_local = _parsear_decimal(xg[0])
            stats.xg_visitante = _parsear_decimal(xg[1])
            stats.datos_xg_disponible = True

        # Tarjetas amarillas
        amarillas = buscar_estadistica_en_grupos(grupos, NOMBRES_TARJETAS_AMARILLAS)
        if amarillas[0] is not None:
            stats.tarjetas_amarillas_local = _parsear_entero(amarillas[0])
            stats.tarjetas_amarillas_visitante = _parsear_entero(amarillas[1])

        # Tarjetas rojas
        rojas = buscar_estadistica_en_grupos(grupos, NOMBRES_TARJETAS_ROJAS)
        if rojas[0] is not None:
            stats.tarjetas_rojas_local = _parsear_entero(rojas[0])
            stats.tarjetas_rojas_visitante = _parsear_entero(rojas[1])

        # Faltas
        faltas = buscar_estadistica_en_grupos(grupos, NOMBRES_FALTAS)
        if faltas[0] is not None:
            stats.faltas_local = _parsear_entero(faltas[0])
            stats.faltas_visitante = _parsear_entero(faltas[1])

        # Fuera de juego
        offsides = buscar_estadistica_en_grupos(grupos, NOMBRES_FUERA_JUEGO)
        if offsides[0] is not None:
            stats.fuera_juego_local = _parsear_entero(offsides[0])
            stats.fuera_juego_visitante = _parsear_entero(offsides[1])

    # Extraer corners por tiempo
    if '1ST' in periodos:
        grupos_1t = periodos['1ST']
        corners_1t = buscar_estadistica_en_grupos(grupos_1t, NOMBRES_CORNERS)
        if corners_1t[0] is not None:
            stats.corners_local_1t = _parsear_entero(corners_1t[0])
            stats.corners_visitante_1t = _parsear_entero(corners_1t[1])

    if '2ND' in periodos:
        grupos_2t = periodos['2ND']
        corners_2t = buscar_estadistica_en_grupos(grupos_2t, NOMBRES_CORNERS)
        if corners_2t[0] is not None:
            stats.corners_local_2t = _parsear_entero(corners_2t[0])
            stats.corners_visitante_2t = _parsear_entero(corners_2t[1])

    # Calcular corners totales si solo tenemos por tiempo
    if stats.corners_local_total is None and stats.corners_local_1t is not None:
        if stats.corners_local_2t is not None:
            stats.corners_local_total = stats.corners_local_1t + stats.corners_local_2t
            stats.corners_visitante_total = stats.corners_visitante_1t + stats.corners_visitante_2t

    # Actualizar flags de completitud
    stats.datos_corners_completos = (
        stats.corners_local_1t is not None and
        stats.corners_local_2t is not None and
        stats.corners_visitante_1t is not None and
        stats.corners_visitante_2t is not None
    )

    stats.datos_disparos_completos = (
        stats.disparos_local_total is not None and
        stats.disparos_local_arco is not None and
        stats.disparos_visitante_total is not None and
        stats.disparos_visitante_arco is not None
    )

    stats.datos_completos = (
        stats.tiene_corners() and
        stats.tiene_disparos() and
        stats.tiene_posesion()
    )

    return stats


def buscar_estadistica_en_grupos(
    grupos: List[Dict[str, Any]],
    nombres_posibles: List[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Busca una estadística en los grupos por su nombre.

    La estructura de Sofascore tiene grupos con statisticsItems.
    Esta función busca recursivamente una estadística por su nombre,
    probando varios nombres posibles (para manejar variaciones de idioma).

    Args:
        grupos: Lista de grupos de estadísticas.
        nombres_posibles: Lista de nombres a buscar (ej: ['Corner kicks', 'Corners']).

    Returns:
        Tupla (valor_home, valor_away) o (None, None) si no se encontró.

    Ejemplo:
        corners = buscar_estadistica_en_grupos(grupos, ['Corner kicks', 'Corners'])
        if corners[0] is not None:
            print(f"Corners: {corners[0]} - {corners[1]}")
    """
    for grupo in grupos:
        items = grupo.get('statisticsItems', [])

        for item in items:
            nombre_stat = item.get('name', '')

            for nombre_buscar in nombres_posibles:
                if nombre_stat.lower() == nombre_buscar.lower():
                    home = item.get('home', item.get('homeValue'))
                    away = item.get('away', item.get('awayValue'))
                    return (home, away)

    return (None, None)


def _parsear_entero(valor: Any) -> Optional[int]:
    """
    Convierte un valor a entero de forma segura.

    Args:
        valor: Valor a convertir (puede ser string, int, o None).

    Returns:
        Entero o None si no se puede convertir.
    """
    if valor is None:
        return None

    if isinstance(valor, int):
        return valor

    try:
        # Eliminar caracteres no numéricos
        valor_str = str(valor).strip()
        valor_str = re.sub(r'[^\d\-]', '', valor_str)
        return int(valor_str) if valor_str else None
    except (ValueError, TypeError):
        return None


def _parsear_decimal(valor: Any) -> Optional[float]:
    """
    Convierte un valor a decimal de forma segura.

    Args:
        valor: Valor a convertir (puede ser string "1.39", float, o None).

    Returns:
        Float o None si no se puede convertir.
    """
    if valor is None:
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    try:
        valor_str = str(valor).strip()
        # Reemplazar coma por punto si es necesario
        valor_str = valor_str.replace(',', '.')
        # Eliminar caracteres no válidos
        valor_str = re.sub(r'[^\d.\-]', '', valor_str)
        return float(valor_str) if valor_str else None
    except (ValueError, TypeError):
        return None


def _parsear_porcentaje(valor: Any) -> Optional[float]:
    """
    Convierte un porcentaje a número (ej: "47%" → 47.0).

    Args:
        valor: Valor a convertir (puede ser "47%", "47", 47, etc.).

    Returns:
        Float representando el porcentaje (sin el símbolo %).
    """
    if valor is None:
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    try:
        valor_str = str(valor).strip()
        # Eliminar símbolo de porcentaje y espacios
        valor_str = valor_str.replace('%', '').strip()
        return float(valor_str) if valor_str else None
    except (ValueError, TypeError):
        return None


def validar_consistencia_estadisticas(
    estadisticas: EstadisticasPartido
) -> List[str]:
    """
    Valida la consistencia de las estadísticas de un partido.

    Verifica que los datos tengan sentido lógico:
    - corners_1t + corners_2t = corners_total (±1 tolerancia)
    - disparos_arco <= disparos_total
    - posesion_local + posesion_visitante ≈ 100

    Los warnings no causan que falle la importación, pero se registran
    para revisión posterior.

    Args:
        estadisticas: EstadisticasPartido a validar.

    Returns:
        Lista de strings describiendo las inconsistencias encontradas.
        Lista vacía si todo está correcto.

    Ejemplo:
        inconsistencias = validar_consistencia_estadisticas(stats)
        if inconsistencias:
            for msg in inconsistencias:
                logger.warning(msg)
    """
    problemas = []

    # Validar consistencia de corners
    if estadisticas.tiene_corners_por_tiempo() and estadisticas.tiene_corners():
        # Local
        suma_corners_local = estadisticas.corners_local_1t + estadisticas.corners_local_2t
        if abs(suma_corners_local - estadisticas.corners_local_total) > 1:
            problemas.append(
                f"Corners local inconsistentes: {estadisticas.corners_local_1t} + "
                f"{estadisticas.corners_local_2t} != {estadisticas.corners_local_total}"
            )

        # Visitante
        suma_corners_visitante = estadisticas.corners_visitante_1t + estadisticas.corners_visitante_2t
        if abs(suma_corners_visitante - estadisticas.corners_visitante_total) > 1:
            problemas.append(
                f"Corners visitante inconsistentes: {estadisticas.corners_visitante_1t} + "
                f"{estadisticas.corners_visitante_2t} != {estadisticas.corners_visitante_total}"
            )

    # Validar disparos al arco vs total
    if estadisticas.tiene_disparos() and estadisticas.disparos_local_arco is not None:
        if estadisticas.disparos_local_arco > estadisticas.disparos_local_total:
            problemas.append(
                f"Disparos local inconsistentes: arco ({estadisticas.disparos_local_arco}) > "
                f"total ({estadisticas.disparos_local_total})"
            )

        if estadisticas.disparos_visitante_arco > estadisticas.disparos_visitante_total:
            problemas.append(
                f"Disparos visitante inconsistentes: arco ({estadisticas.disparos_visitante_arco}) > "
                f"total ({estadisticas.disparos_visitante_total})"
            )

    # Validar posesión
    if estadisticas.tiene_posesion():
        suma_posesion = estadisticas.posesion_local + estadisticas.posesion_visitante
        if suma_posesion < 99 or suma_posesion > 101:
            problemas.append(
                f"Posesión inconsistente: {estadisticas.posesion_local} + "
                f"{estadisticas.posesion_visitante} = {suma_posesion} (esperado ~100)"
            )

    return problemas


def validar_rango_estadisticas(
    estadisticas: EstadisticasPartido
) -> List[str]:
    """
    Valida que las estadísticas estén dentro de rangos razonables.

    Esto ayuda a detectar datos incorrectos o atípicos que podrían
    indicar problemas con la fuente de datos.

    Args:
        estadisticas: EstadisticasPartido a validar.

    Returns:
        Lista de warnings sobre valores fuera de rango.
    """
    warnings = []

    # Rangos de corners (0-15 normal, >15 sospechoso)
    if estadisticas.tiene_corners():
        if estadisticas.corners_local_total > 15:
            warnings.append(
                f"Corners local alto: {estadisticas.corners_local_total}"
            )
        if estadisticas.corners_visitante_total > 15:
            warnings.append(
                f"Corners visitante alto: {estadisticas.corners_visitante_total}"
            )

    # Rangos de disparos (5-30 normal)
    if estadisticas.tiene_disparos():
        if estadisticas.disparos_local_total < 5 or estadisticas.disparos_local_total > 30:
            warnings.append(
                f"Disparos local fuera de rango: {estadisticas.disparos_local_total}"
            )
        if estadisticas.disparos_visitante_total < 5 or estadisticas.disparos_visitante_total > 30:
            warnings.append(
                f"Disparos visitante fuera de rango: {estadisticas.disparos_visitante_total}"
            )

    # Rangos de xG (0-5 normal)
    if estadisticas.tiene_xg():
        if estadisticas.xg_local > 5:
            warnings.append(f"xG local alto: {estadisticas.xg_local}")
        if estadisticas.xg_visitante > 5:
            warnings.append(f"xG visitante alto: {estadisticas.xg_visitante}")

    # Rangos de posesión (20-80 normal)
    if estadisticas.tiene_posesion():
        if estadisticas.posesion_local < 20 or estadisticas.posesion_local > 80:
            warnings.append(
                f"Posesión local extrema: {estadisticas.posesion_local}%"
            )
        if estadisticas.posesion_visitante < 20 or estadisticas.posesion_visitante > 80:
            warnings.append(
                f"Posesión visitante extrema: {estadisticas.posesion_visitante}%"
            )

    return warnings
