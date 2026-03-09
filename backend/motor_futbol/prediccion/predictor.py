# -*- coding: utf-8 -*-
"""
predictor.py — Predictor principal de fútbol.

Este módulo implementa la clase PredictorFutbol que integra todos los
componentes del motor de predicción.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from ..tipos import (
    PrediccionPartido,
    PrediccionMercado,
    TipoMercadoFutbol,
    NivelConfianza,
    FeaturesPartidoFutbol,
)
from ..constantes import (
    UMBRAL_PARTIDOS_CONFIANZA_ALTA,
    UMBRAL_PARTIDOS_CONFIANZA_MEDIA,
    UMBRAL_EDGE_RECOMENDACION,
    LINEAS_CORNERS,
    LINEAS_GOLES,
    LINEAS_DISPAROS,
)
from ..excepciones import (
    PartidoNoEncontrado,
    EquipoNoEncontrado,
    ModeloNoEntrenado,
    ErrorPrediccion,
)
from ..features.generador import GeneradorFeaturesFutbol
from ..modelos.corners import ModeloCorners
from ..modelos.goles import ModeloGoles
from ..modelos.disparos import ModeloDisparos
from .calculadora_probabilidad import CalculadoraProbabilidad

logger = logging.getLogger(__name__)


class PredictorFutbol:
    """
    Predictor principal de fútbol.

    Orquesta el flujo completo de predicción:
    1. Obtiene información del partido
    2. Genera features
    3. Predice corners, goles y disparos
    4. Calcula probabilidades
    5. Determina nivel de confianza
    6. Genera recomendaciones

    Atributos:
        pool: Pool de conexiones PostgreSQL
        generador: Generador de features
        modelo_corners: Modelo de predicción de corners
        modelo_goles: Modelo de predicción de goles
        modelo_disparos: Modelo de predicción de disparos
    """

    def __init__(
        self,
        pool,
        generador: Optional[GeneradorFeaturesFutbol] = None,
        modelo_corners: Optional[ModeloCorners] = None,
        modelo_goles: Optional[ModeloGoles] = None,
        modelo_disparos: Optional[ModeloDisparos] = None,
        cargar_modelos: bool = True,
        ruta_modelos: Optional[str] = None,
    ):
        """
        Inicializa el predictor.

        Args:
            pool: Pool de conexiones
            cargar_modelos: Si True, carga modelos desde BD/archivo
            ruta_modelos: Ruta opcional para cargar modelos desde archivo
        """
        self._pool = pool

        custom_contract = any(
            x is not None for x in [generador, modelo_corners, modelo_goles, modelo_disparos]
        )
        if custom_contract:
            if not all(x is not None for x in [generador, modelo_corners, modelo_goles, modelo_disparos]):
                raise TypeError(
                    "Si se inyecta contrato custom, debe incluir generador y los tres modelos"
                )
            self.generador = generador
            self.modelo_corners = modelo_corners
            self.modelo_goles = modelo_goles
            self.modelo_disparos = modelo_disparos
            self._modelos_cargados = True
        else:
            self.generador = GeneradorFeaturesFutbol(pool)
            self.modelo_corners = None
            self.modelo_goles = None
            self.modelo_disparos = None
            self._modelos_cargados = False

        self.version_activa: str = ""

        if custom_contract:
            self._actualizar_version()
        elif cargar_modelos:
            try:
                self.cargar_modelos(ruta_modelos)
            except Exception as e:
                logger.warning(f"No se pudieron cargar modelos: {e}")

    def cargar_modelos(
        self,
        ruta: Optional[str] = None,
        version_id: Optional[int] = None,
    ) -> None:
        """
        Carga modelos desde archivo o BD.

        Args:
            ruta: Ruta base de archivos (opcional)
            version_id: ID de versión específica (opcional)
        """
        if ruta:
            # Cargar desde archivos
            from ..modelos.base import ModeloPrediccionBase

            try:
                self.modelo_corners = ModeloCorners()
                self.modelo_corners = ModeloPrediccionBase.cargar(f"{ruta}/corners.npz")
            except FileNotFoundError:
                logger.warning("No se encontró modelo de corners")

            try:
                self.modelo_goles = ModeloGoles()
                self.modelo_goles = ModeloPrediccionBase.cargar(f"{ruta}/goles.npz")
            except FileNotFoundError:
                logger.warning("No se encontró modelo de goles")

            try:
                self.modelo_disparos = ModeloDisparos()
                self.modelo_disparos = ModeloPrediccionBase.cargar(f"{ruta}/disparos.npz")
            except FileNotFoundError:
                logger.warning("No se encontró modelo de disparos")
        else:
            # Inicializar modelos vacíos (se entrenarán después)
            self.modelo_corners = ModeloCorners()
            self.modelo_goles = ModeloGoles()
            self.modelo_disparos = ModeloDisparos()

        self._modelos_cargados = True
        logger.info("Modelos inicializados")

    def establecer_modelos(
        self,
        modelo_corners: Optional[ModeloCorners] = None,
        modelo_goles: Optional[ModeloGoles] = None,
        modelo_disparos: Optional[ModeloDisparos] = None,
    ) -> None:
        """
        Establece modelos ya entrenados.

        Args:
            modelo_corners: Modelo de corners entrenado
            modelo_goles: Modelo de goles entrenado
            modelo_disparos: Modelo de disparos entrenado
        """
        if modelo_corners:
            self.modelo_corners = modelo_corners
        if modelo_goles:
            self.modelo_goles = modelo_goles
        if modelo_disparos:
            self.modelo_disparos = modelo_disparos

        self._modelos_cargados = True
        self._actualizar_version()

    def _actualizar_version(self) -> None:
        """Actualiza string de versión activa."""
        partes = []

        if self.modelo_corners and self.modelo_corners.entrenado:
            v = self.modelo_corners.version_id or 0
            partes.append(f"corners_v{v}")

        if self.modelo_goles and self.modelo_goles.entrenado:
            v = self.modelo_goles.version_id or 0
            partes.append(f"goles_v{v}")

        if self.modelo_disparos and self.modelo_disparos.entrenado:
            v = self.modelo_disparos.version_id or 0
            partes.append(f"disparos_v{v}")

        self.version_activa = "_".join(partes) if partes else "sin_entrenar"

    def predecir_partido(
        self,
        partido_id: UUID,
        fecha_corte: Optional[datetime] = None,
    ) -> PrediccionPartido:
        """
        Genera predicción completa para un partido.

        Flujo:
        1. Obtener info del partido
        2. Verificar que equipos están en modelos
        3. Generar features (respetando fecha_corte)
        4. Predecir corners
        5. Predecir goles
        6. Predecir disparos
        7. Determinar confianza
        8. Generar recomendaciones

        Args:
            partido_id: ID del partido
            fecha_corte: Fecha límite para features (default: día antes del partido)

        Returns:
            PrediccionPartido completa

        Raises:
            PartidoNoEncontrado: Si el partido no existe
            EquipoNoEncontrado: Si algún equipo no está en el modelo
            ModeloNoEntrenado: Si los modelos no están entrenados
        """
        logger.info(f"Generando predicción para partido {partido_id}")

        # 1. Obtener información del partido
        info_partido = self._obtener_info_partido(partido_id)

        equipo_local = info_partido["equipo_local_nombre"]
        equipo_visitante = info_partido["equipo_visitante_nombre"]
        competicion = info_partido.get("competicion_nombre", "")
        fecha_partido = info_partido["fecha_partido"]

        # 2. Determinar fecha de corte
        if fecha_corte is None:
            fecha_corte = fecha_partido - timedelta(days=1)

        # 3. Generar features
        try:
            features = self.generador.generar(partido_id, fecha_corte)
        except Exception as e:
            logger.error(f"Error generando features: {e}")
            raise ErrorPrediccion(f"Error generando features: {e}", str(partido_id))

        # 4. Verificar que equipos están en modelos
        self._verificar_equipos(equipo_local, equipo_visitante)

        # 5. Generar predicciones por tipo
        mercados_corners = {}
        mercados_goles = {}
        mercados_disparos = {}
        metricas = {}

        if self.modelo_corners and self.modelo_corners.entrenado:
            try:
                mercados_corners = self.modelo_corners.predecir_completo(
                    equipo_local, equipo_visitante, es_local=True
                )
                metricas["mae_corners"] = self.modelo_corners.metricas.get("mae_promedio", 0)
            except Exception as e:
                logger.warning(f"Error prediciendo corners: {e}")

        if self.modelo_goles and self.modelo_goles.entrenado:
            try:
                mercados_goles = self.modelo_goles.predecir_completo(
                    equipo_local, equipo_visitante, es_local=True
                )
                metricas["mae_goles"] = self.modelo_goles.metricas.get("mae_promedio", 0)
            except Exception as e:
                logger.warning(f"Error prediciendo goles: {e}")

        if self.modelo_disparos and self.modelo_disparos.entrenado:
            try:
                mercados_disparos = self.modelo_disparos.predecir_completo(
                    equipo_local, equipo_visitante, es_local=True
                )
                metricas["mae_disparos"] = self.modelo_disparos.metricas.get("mae_promedio", 0)
            except Exception as e:
                logger.warning(f"Error prediciendo disparos: {e}")

        # 6. Determinar confianza
        nivel_confianza = self._determinar_confianza(features)

        # 7. Generar recomendaciones
        recomendaciones = self._generar_recomendaciones(
            mercados_corners, mercados_goles, mercados_disparos
        )

        # 8. Construir resultado
        prediccion = PrediccionPartido(
            partido_id=partido_id,
            fecha_analisis=datetime.now(),
            equipo_local=equipo_local,
            equipo_visitante=equipo_visitante,
            competicion=competicion,
            mercados_corners=mercados_corners,
            mercados_goles=mercados_goles,
            mercados_disparos=mercados_disparos,
            nivel_confianza=nivel_confianza,
            version_modelo=self.version_activa,
            metricas_modelo=metricas,
            recomendaciones=recomendaciones,
        )

        logger.info(f"Predicción generada para {equipo_local} vs {equipo_visitante}")
        return prediccion

    def predecir_partidos_proximos(
        self,
        dias: int = 7,
        competiciones: Optional[List[str]] = None,
        limite: int = 50,
    ) -> List[PrediccionPartido]:
        """
        Genera predicciones para partidos de próximos N días.

        Args:
            dias: Número de días a futuro
            competiciones: Lista de códigos de competiciones (opcional)
            limite: Número máximo de partidos

        Returns:
            Lista de PrediccionPartido
        """
        # Obtener partidos programados
        fecha_inicio = datetime.now()
        fecha_fin = fecha_inicio + timedelta(days=dias)

        query = """
            SELECT p.id
            FROM partidos_futbol p
            JOIN competiciones_futbol c ON p.competicion_id = c.id
            WHERE p.estado = 'PROGRAMADO'
              AND p.fecha_partido >= %s
              AND p.fecha_partido <= %s
        """
        parametros = [fecha_inicio, fecha_fin]

        if competiciones:
            query += " AND c.codigo = ANY(%s)"
            parametros.append(competiciones)

        query += " ORDER BY p.fecha_partido LIMIT %s"
        parametros.append(limite)

        predicciones = []

        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parametros)
                filas = cursor.fetchall()

                for fila in filas:
                    partido_id = fila[0]
                    try:
                        pred = self.predecir_partido(UUID(str(partido_id)))
                        predicciones.append(pred)
                    except Exception as e:
                        logger.warning(f"Error prediciendo partido {partido_id}: {e}")
                        continue

        return predicciones

    def _obtener_info_partido(self, partido_id: UUID) -> Dict[str, Any]:
        """Obtiene información del partido desde BD."""
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
                c.nombre as competicion_nombre
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
                return dict(zip(columnas, fila))

    def _verificar_equipos(self, equipo_local: str, equipo_visitante: str) -> None:
        """Verifica que los equipos estén en los modelos."""
        # Verificar en modelo de corners (es el principal)
        if self.modelo_corners and self.modelo_corners.entrenado:
            if not self.modelo_corners.contiene_equipo(equipo_local):
                raise EquipoNoEncontrado(
                    equipo_local,
                    self.modelo_corners.cantidad_equipos
                )
            if not self.modelo_corners.contiene_equipo(equipo_visitante):
                raise EquipoNoEncontrado(
                    equipo_visitante,
                    self.modelo_corners.cantidad_equipos
                )

    def _determinar_confianza(
        self,
        features: FeaturesPartidoFutbol,
    ) -> NivelConfianza:
        """
        Determina el nivel de confianza de la predicción.

        Criterios:
        - ALTA: ≥5 partidos cada equipo, datos completos
        - MEDIA: 3-4 partidos o datos parciales
        - BAJA: <3 partidos o muchos datos faltantes
        """
        partidos_local = features.local_partidos_jugados
        partidos_visitante = features.visitante_partidos_jugados
        min_partidos = min(partidos_local, partidos_visitante)

        if min_partidos >= UMBRAL_PARTIDOS_CONFIANZA_ALTA:
            return NivelConfianza.ALTA
        elif min_partidos >= UMBRAL_PARTIDOS_CONFIANZA_MEDIA:
            return NivelConfianza.MEDIA
        else:
            return NivelConfianza.BAJA

    def _generar_recomendaciones(
        self,
        mercados_corners: Dict[str, PrediccionMercado],
        mercados_goles: Dict[str, PrediccionMercado],
        mercados_disparos: Dict[str, PrediccionMercado],
        umbral_edge: float = UMBRAL_EDGE_RECOMENDACION,
    ) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones de apuesta basadas en las predicciones.

        Solo recomienda cuando hay edge positivo significativo.
        """
        recomendaciones = []

        # Función auxiliar para evaluar mercado
        def evaluar_mercado(
            mercado: PrediccionMercado,
            tipo: str,
        ) -> Optional[Dict[str, Any]]:
            # Buscar la línea con mayor probabilidad over
            mejor_over = None
            mejor_prob_over = 0.0

            for clave, prob in mercado.probabilidades.items():
                if clave.startswith("over_") and prob > mejor_prob_over:
                    mejor_prob_over = prob
                    linea = float(clave.replace("over_", ""))
                    mejor_over = (linea, prob)

            if mejor_over and mejor_prob_over > 0.55:  # Umbral mínimo
                linea, prob = mejor_over
                cuota_justa = CalculadoraProbabilidad.cuota_justa(prob)

                return {
                    "mercado": mercado.mercado.value,
                    "tipo": "OVER",
                    "linea": linea,
                    "probabilidad_modelo": round(prob, 4),
                    "cuota_minima_valor": round(cuota_justa, 2),
                    "media_predicha": mercado.media,
                    "confianza": tipo,
                }

            return None

        # Evaluar mercados de corners (prioridad)
        for mercado in mercados_corners.values():
            rec = evaluar_mercado(mercado, "CORNERS")
            if rec:
                recomendaciones.append(rec)

        # Evaluar mercados de goles
        for mercado in mercados_goles.values():
            rec = evaluar_mercado(mercado, "GOLES")
            if rec:
                recomendaciones.append(rec)

        # Evaluar mercados de disparos
        for mercado in mercados_disparos.values():
            rec = evaluar_mercado(mercado, "DISPAROS")
            if rec:
                recomendaciones.append(rec)

        # Ordenar por probabilidad descendente
        recomendaciones.sort(key=lambda x: x["probabilidad_modelo"], reverse=True)

        # Limitar a top 10
        return recomendaciones[:10]

    @property
    def modelos_entrenados(self) -> bool:
        """Indica si hay al menos un modelo entrenado."""
        return (
            (self.modelo_corners and self.modelo_corners.entrenado) or
            (self.modelo_goles and self.modelo_goles.entrenado) or
            (self.modelo_disparos and self.modelo_disparos.entrenado)
        )
