# -*- coding: utf-8 -*-
"""
generador.py — Generador principal de features para partidos de fútbol.

Este módulo contiene la clase GeneradorFeaturesFutbol que genera todas las
características predictivas para un partido dado.

IMPORTANTE: Todas las funciones respetan fecha_corte para prevenir data leakage.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from ..tipos import FeaturesPartidoFutbol, normalizar_nombre_equipo
from ..constantes import (
    N_PARTIDOS_FORMA,
    MIN_PARTIDOS_ESTADISTICAS,
    DEFAULTS_CORNERS,
    DEFAULTS_GOLES,
    DEFAULTS_DISPAROS,
    DEFAULT_POSESION,
)
from ..excepciones import PartidoNoEncontrado, DatosInsuficientes
from .cache import CacheFeatures
from .calculadores import (
    calcular_estadisticas_temporada,
    calcular_estadisticas_ubicacion,
    calcular_forma_reciente,
    calcular_tendencia,
)

logger = logging.getLogger(__name__)


class GeneradorFeaturesFutbol:
    """
    Generador de features para partidos de fútbol.

    Esta clase extrae y calcula todas las características necesarias
    para predecir un partido, respetando siempre la fecha de corte
    para evitar data leakage.

    Atributos:
        pool: Pool de conexiones a PostgreSQL
        cache: Sistema de cache para estadísticas
        n_partidos_forma: Número de partidos para cálculo de forma
        min_partidos_estadisticas: Mínimo de partidos para estadísticas
    """

    def __init__(
        self,
        pool,
        n_partidos_forma: int = N_PARTIDOS_FORMA,
        usar_cache: bool = True,
    ):
        """
        Inicializa el generador con pool de conexiones.

        Args:
            pool: ConnectionPool de psycopg para la base de datos
            n_partidos_forma: Número de partidos para forma reciente
            usar_cache: Si True, usa cache para estadísticas
        """
        self._pool = pool
        self.n_partidos_forma = n_partidos_forma
        self.min_partidos_estadisticas = MIN_PARTIDOS_ESTADISTICAS
        self._cache = CacheFeatures() if usar_cache else None

    def generar(
        self,
        partido_id: UUID,
        fecha_corte: datetime,
    ) -> FeaturesPartidoFutbol:
        """
        Genera features para un partido.

        Args:
            partido_id: ID del partido a analizar
            fecha_corte: Fecha límite para datos históricos (CRÍTICO para prevenir leakage)

        Returns:
            FeaturesPartidoFutbol con todos los campos calculados

        Raises:
            PartidoNoEncontrado: Si el partido no existe
            DatosInsuficientes: Si no hay suficientes datos históricos
        """
        logger.debug(f"Generando features para partido {partido_id}, corte: {fecha_corte}")

        # 1. Obtener información básica del partido
        info_partido = self._obtener_info_partido(partido_id)

        # 2. Extraer IDs y nombres
        equipo_local_id = info_partido["equipo_local_id"]
        equipo_visitante_id = info_partido["equipo_visitante_id"]
        equipo_local_nombre = info_partido["equipo_local_nombre"]
        equipo_visitante_nombre = info_partido["equipo_visitante_nombre"]
        competicion_id = info_partido["competicion_id"]
        temporada_id = info_partido["temporada_id"]

        # 3. Calcular estadísticas para equipo LOCAL
        stats_local_temp = self._calcular_estadisticas_equipo(
            equipo_id=equipo_local_id,
            competicion_id=competicion_id,
            temporada_id=temporada_id,
            fecha_corte=fecha_corte,
            como_local=None,  # Todos los partidos
        )

        stats_local_ubicacion = self._calcular_estadisticas_equipo(
            equipo_id=equipo_local_id,
            competicion_id=competicion_id,
            temporada_id=temporada_id,
            fecha_corte=fecha_corte,
            como_local=True,  # Solo como local
        )

        forma_local = self._calcular_forma_equipo(
            equipo_id=equipo_local_id,
            fecha_corte=fecha_corte,
        )

        # 4. Calcular estadísticas para equipo VISITANTE
        stats_visitante_temp = self._calcular_estadisticas_equipo(
            equipo_id=equipo_visitante_id,
            competicion_id=competicion_id,
            temporada_id=temporada_id,
            fecha_corte=fecha_corte,
            como_local=None,  # Todos los partidos
        )

        stats_visitante_ubicacion = self._calcular_estadisticas_equipo(
            equipo_id=equipo_visitante_id,
            competicion_id=competicion_id,
            temporada_id=temporada_id,
            fecha_corte=fecha_corte,
            como_local=False,  # Solo como visitante
        )

        forma_visitante = self._calcular_forma_equipo(
            equipo_id=equipo_visitante_id,
            fecha_corte=fecha_corte,
        )

        # 5. Construir el objeto de features
        features = FeaturesPartidoFutbol(
            partido_id=partido_id,
            fecha_partido=info_partido["fecha_partido"],
            competicion_id=competicion_id,
            temporada_id=temporada_id,
            es_copa=info_partido.get("es_copa", False),
            equipo_local_nombre=equipo_local_nombre,
            equipo_visitante_nombre=equipo_visitante_nombre,

            # LOCAL - Temporada
            local_goles_favor_temp=stats_local_temp.get("goles_favor", DEFAULTS_GOLES["goles_favor"]),
            local_goles_contra_temp=stats_local_temp.get("goles_contra", DEFAULTS_GOLES["goles_contra"]),
            local_corners_favor_temp=stats_local_temp.get("corners_favor", DEFAULTS_CORNERS["corners_favor"]),
            local_corners_contra_temp=stats_local_temp.get("corners_contra", DEFAULTS_CORNERS["corners_contra"]),
            local_corners_1t_temp=stats_local_temp.get("corners_1t", DEFAULTS_CORNERS["corners_1t"]),
            local_corners_2t_temp=stats_local_temp.get("corners_2t", DEFAULTS_CORNERS["corners_2t"]),
            local_disparos_temp=stats_local_temp.get("disparos_total", DEFAULTS_DISPAROS["disparos_total"]),
            local_disparos_arco_temp=stats_local_temp.get("disparos_arco", DEFAULTS_DISPAROS["disparos_arco"]),
            local_posesion_temp=stats_local_temp.get("posesion", DEFAULT_POSESION),
            local_xg_temp=stats_local_temp.get("xg", 0.0),
            local_partidos_jugados=stats_local_temp.get("partidos_jugados", 0),

            # LOCAL - Como local
            local_goles_como_local=stats_local_ubicacion.get("goles_favor", DEFAULTS_GOLES["goles_favor"]),
            local_goles_contra_como_local=stats_local_ubicacion.get("goles_contra", DEFAULTS_GOLES["goles_contra"]),
            local_corners_como_local=stats_local_ubicacion.get("corners_favor", DEFAULTS_CORNERS["corners_favor"]),
            local_corners_contra_como_local=stats_local_ubicacion.get("corners_contra", DEFAULTS_CORNERS["corners_contra"]),
            local_partidos_local=stats_local_ubicacion.get("partidos_jugados", 0),

            # LOCAL - Forma
            local_goles_ultimos_5=forma_local.get("goles_promedio", DEFAULTS_GOLES["goles_favor"]),
            local_corners_ultimos_5=forma_local.get("corners_promedio", DEFAULTS_CORNERS["corners_favor"]),
            local_disparos_ultimos_5=forma_local.get("disparos_promedio", DEFAULTS_DISPAROS["disparos_total"]),
            local_tendencia_corners=forma_local.get("tendencia_corners", 0.0),

            # VISITANTE - Temporada
            visitante_goles_favor_temp=stats_visitante_temp.get("goles_favor", DEFAULTS_GOLES["goles_favor"]),
            visitante_goles_contra_temp=stats_visitante_temp.get("goles_contra", DEFAULTS_GOLES["goles_contra"]),
            visitante_corners_favor_temp=stats_visitante_temp.get("corners_favor", DEFAULTS_CORNERS["corners_favor"]),
            visitante_corners_contra_temp=stats_visitante_temp.get("corners_contra", DEFAULTS_CORNERS["corners_contra"]),
            visitante_corners_1t_temp=stats_visitante_temp.get("corners_1t", DEFAULTS_CORNERS["corners_1t"]),
            visitante_corners_2t_temp=stats_visitante_temp.get("corners_2t", DEFAULTS_CORNERS["corners_2t"]),
            visitante_disparos_temp=stats_visitante_temp.get("disparos_total", DEFAULTS_DISPAROS["disparos_total"]),
            visitante_disparos_arco_temp=stats_visitante_temp.get("disparos_arco", DEFAULTS_DISPAROS["disparos_arco"]),
            visitante_posesion_temp=stats_visitante_temp.get("posesion", DEFAULT_POSESION),
            visitante_xg_temp=stats_visitante_temp.get("xg", 0.0),
            visitante_partidos_jugados=stats_visitante_temp.get("partidos_jugados", 0),

            # VISITANTE - Como visitante
            visitante_goles_como_visitante=stats_visitante_ubicacion.get("goles_favor", DEFAULTS_GOLES["goles_favor"]),
            visitante_goles_contra_como_visitante=stats_visitante_ubicacion.get("goles_contra", DEFAULTS_GOLES["goles_contra"]),
            visitante_corners_como_visitante=stats_visitante_ubicacion.get("corners_favor", DEFAULTS_CORNERS["corners_favor"]),
            visitante_corners_contra_como_visitante=stats_visitante_ubicacion.get("corners_contra", DEFAULTS_CORNERS["corners_contra"]),
            visitante_partidos_visitante=stats_visitante_ubicacion.get("partidos_jugados", 0),

            # VISITANTE - Forma
            visitante_goles_ultimos_5=forma_visitante.get("goles_promedio", DEFAULTS_GOLES["goles_favor"]),
            visitante_corners_ultimos_5=forma_visitante.get("corners_promedio", DEFAULTS_CORNERS["corners_favor"]),
            visitante_disparos_ultimos_5=forma_visitante.get("disparos_promedio", DEFAULTS_DISPAROS["disparos_total"]),
            visitante_tendencia_corners=forma_visitante.get("tendencia_corners", 0.0),
        )

        # 6. Calcular features derivados
        features.diff_goles_favor = features.local_goles_favor_temp - features.visitante_goles_favor_temp
        features.diff_corners_favor = features.local_corners_favor_temp - features.visitante_corners_favor_temp
        features.suma_corners_promedio = features.local_corners_favor_temp + features.visitante_corners_favor_temp

        total_posesion = features.local_posesion_temp + features.visitante_posesion_temp
        if total_posesion > 0:
            features.ratio_posesion = features.local_posesion_temp / total_posesion
        else:
            features.ratio_posesion = 0.5

        return features

    def generar_lote(
        self,
        partidos: List[Tuple[UUID, datetime]],
    ) -> List[FeaturesPartidoFutbol]:
        """
        Genera features para múltiples partidos eficientemente.

        Args:
            partidos: Lista de tuplas (partido_id, fecha_corte)

        Returns:
            Lista de FeaturesPartidoFutbol
        """
        resultados = []
        for partido_id, fecha_corte in partidos:
            try:
                features = self.generar(partido_id, fecha_corte)
                resultados.append(features)
            except (PartidoNoEncontrado, DatosInsuficientes) as e:
                logger.warning(f"Error generando features para {partido_id}: {e}")
                continue
        return resultados

    def limpiar_cache(self):
        """Limpia el cache interno."""
        if self._cache:
            self._cache.limpiar()
            logger.info("Cache de features limpiado")

    def _obtener_info_partido(self, partido_id: UUID) -> Dict[str, Any]:
        """Obtiene información básica del partido desde la BD."""
        query = """
            SELECT
                p.id,
                p.fecha_partido,
                p.competicion_id,
                p.temporada_id,
                p.equipo_local_id,
                p.equipo_visitante_id,
                el.nombre as equipo_local_nombre,
                ev.nombre as equipo_visitante_nombre,
                c.codigo as competicion_codigo
            FROM partidos_futbol p
            JOIN equipos_futbol el ON p.equipo_local_id = el.id
            JOIN equipos_futbol ev ON p.equipo_visitante_id = ev.id
            JOIN competiciones_futbol c ON p.competicion_id = c.id
            WHERE p.id = %s
        """

        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, [str(partido_id)])
                fila = cursor.fetchone()

                if not fila:
                    raise PartidoNoEncontrado(str(partido_id))

                columnas = [desc[0] for desc in cursor.description]
                resultado = dict(zip(columnas, fila))

                # Determinar si es copa
                codigo_competicion = resultado.get("competicion_codigo", "")
                resultado["es_copa"] = "CHAMPIONS" in codigo_competicion.upper() or \
                                       "EUROPA" in codigo_competicion.upper() or \
                                       "COPA" in codigo_competicion.upper()

                return resultado

    def _calcular_estadisticas_equipo(
        self,
        equipo_id: UUID,
        competicion_id: UUID,
        temporada_id: UUID,
        fecha_corte: datetime,
        como_local: Optional[bool] = None,
    ) -> Dict[str, float]:
        """
        Calcula estadísticas de temporada para un equipo.

        Args:
            equipo_id: ID del equipo
            competicion_id: ID de la competición
            temporada_id: ID de la temporada
            fecha_corte: Solo partidos antes de esta fecha (CRÍTICO)
            como_local: None=todos, True=solo local, False=solo visitante
        """
        # Verificar cache
        if self._cache:
            cache_key = f"stats_{equipo_id}_{temporada_id}_{como_local}_{fecha_corte.date()}"
            cached = self._cache.obtener(cache_key)
            if cached is not None:
                return cached

        # Construir query base
        query = """
            SELECT
                COUNT(*) as partidos_jugados,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_goles_total
                    ELSE visitante_goles_total
                END) as goles_favor,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN visitante_goles_total
                    ELSE local_goles_total
                END) as goles_contra,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_corners_total
                    ELSE visitante_corners_total
                END) as corners_favor,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN visitante_corners_total
                    ELSE local_corners_total
                END) as corners_contra,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_corners_1t
                    ELSE visitante_corners_1t
                END) as corners_1t,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_corners_2t
                    ELSE visitante_corners_2t
                END) as corners_2t,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_disparos_total
                    ELSE visitante_disparos_total
                END) as disparos_total,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_disparos_arco
                    ELSE visitante_disparos_arco
                END) as disparos_arco,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_posesion
                    ELSE visitante_posesion
                END) as posesion,
                AVG(CASE
                    WHEN equipo_local_id = %s THEN local_xg
                    ELSE visitante_xg
                END) as xg
            FROM partidos_futbol
            WHERE (equipo_local_id = %s OR equipo_visitante_id = %s)
              AND temporada_id = %s
              AND estado = 'FINALIZADO'
              AND fecha_partido < %s
        """

        parametros = [str(equipo_id)] * 12 + [str(temporada_id), fecha_corte]

        # Filtrar por ubicación si se especifica
        if como_local is True:
            query += " AND equipo_local_id = %s"
            parametros.append(str(equipo_id))
        elif como_local is False:
            query += " AND equipo_visitante_id = %s"
            parametros.append(str(equipo_id))

        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parametros)
                fila = cursor.fetchone()

                if not fila or fila[0] == 0:
                    return {}

                columnas = [desc[0] for desc in cursor.description]
                resultado = {}
                for i, col in enumerate(columnas):
                    valor = fila[i]
                    if valor is not None:
                        resultado[col] = float(valor) if col != "partidos_jugados" else int(valor)

        # Guardar en cache
        if self._cache:
            self._cache.guardar(cache_key, resultado)

        return resultado

    def _calcular_forma_equipo(
        self,
        equipo_id: UUID,
        fecha_corte: datetime,
    ) -> Dict[str, float]:
        """
        Calcula estadísticas de forma reciente (últimos N partidos).

        Args:
            equipo_id: ID del equipo
            fecha_corte: Solo partidos antes de esta fecha
        """
        query = """
            SELECT
                CASE
                    WHEN equipo_local_id = %s THEN local_goles_total
                    ELSE visitante_goles_total
                END as goles,
                CASE
                    WHEN equipo_local_id = %s THEN local_corners_total
                    ELSE visitante_corners_total
                END as corners,
                CASE
                    WHEN equipo_local_id = %s THEN local_disparos_total
                    ELSE visitante_disparos_total
                END as disparos,
                fecha_partido
            FROM partidos_futbol
            WHERE (equipo_local_id = %s OR equipo_visitante_id = %s)
              AND estado = 'FINALIZADO'
              AND fecha_partido < %s
            ORDER BY fecha_partido DESC
            LIMIT %s
        """

        parametros = [str(equipo_id)] * 5 + [fecha_corte, self.n_partidos_forma]

        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parametros)
                filas = cursor.fetchall()

                if not filas:
                    return {}

                goles = []
                corners = []
                disparos = []

                for fila in filas:
                    if fila[0] is not None:
                        goles.append(float(fila[0]))
                    if fila[1] is not None:
                        corners.append(float(fila[1]))
                    if fila[2] is not None:
                        disparos.append(float(fila[2]))

                resultado = {}

                if goles:
                    resultado["goles_promedio"] = sum(goles) / len(goles)
                if corners:
                    resultado["corners_promedio"] = sum(corners) / len(corners)
                    resultado["tendencia_corners"] = calcular_tendencia(corners)
                if disparos:
                    resultado["disparos_promedio"] = sum(disparos) / len(disparos)

                return resultado
