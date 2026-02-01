# -*- coding: utf-8 -*-
"""
gestor_calibradores.py — Gestión de calibradores activos y persistencia.

Este módulo administra los calibradores activos por mercado, su
carga/guardado desde la base de datos, y proporciona una interfaz
simple para calibrar probabilidades.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Union
from uuid import UUID, uuid4

import numpy as np
from psycopg_pool import ConnectionPool

from ..tipos import TipoMercadoFutbol, ResultadoCalibracion
from .calibrador_base import CalibradorBase
from .platt_scaling import CalibradorPlatt
from .isotonic import CalibradorIsotonic


logger = logging.getLogger(__name__)


# Mapa de métodos a clases de calibradores
CALIBRADORES_DISPONIBLES: Dict[str, type] = {
    "platt": CalibradorPlatt,
    "isotonic": CalibradorIsotonic,
}


class GestorCalibradores:
    """
    Gestor de calibradores de probabilidad.

    Administra los calibradores activos para cada mercado, su persistencia
    en base de datos, y proporciona métodos para calibrar probabilidades.

    Atributos:
        pool: Pool de conexiones a la base de datos
        calibradores_cache: Cache de calibradores cargados
    """

    def __init__(self, pool: ConnectionPool):
        """
        Inicializa el gestor.

        Args:
            pool: Pool de conexiones PostgreSQL
        """
        self.pool = pool
        self.calibradores_cache: Dict[TipoMercadoFutbol, CalibradorBase] = {}

    def cargar_calibrador_activo(
        self,
        mercado: TipoMercadoFutbol,
        usar_cache: bool = True,
    ) -> Optional[CalibradorBase]:
        """
        Carga el calibrador activo para un mercado.

        Args:
            mercado: Tipo de mercado de fútbol
            usar_cache: Si usar el cache o forzar recarga

        Returns:
            Calibrador activo o None si no existe
        """
        # Verificar cache
        if usar_cache and mercado in self.calibradores_cache:
            return self.calibradores_cache[mercado]

        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, metodo, parametros_json, fecha_entrenamiento
                        FROM calibradores_futbol
                        WHERE mercado = %s AND activo = TRUE
                        ORDER BY creado_en DESC
                        LIMIT 1
                        """,
                        (mercado.value,),
                    )
                    row = cur.fetchone()

                    if not row:
                        logger.debug(f"No hay calibrador activo para {mercado.value}")
                        return None

                    calibrador_id, metodo, parametros_json, fecha_entrenamiento = row

                    # Reconstruir calibrador
                    clase = CALIBRADORES_DISPONIBLES.get(metodo)
                    if not clase:
                        logger.warning(f"Método de calibración desconocido: {metodo}")
                        return None

                    # Preparar datos para reconstrucción
                    data = parametros_json if parametros_json else {}
                    data["mercado"] = mercado.value
                    data["metodo"] = metodo
                    data["entrenado"] = True
                    if fecha_entrenamiento:
                        data["fecha_entrenamiento"] = fecha_entrenamiento.isoformat()

                    calibrador = clase.from_dict(data)

                    # Guardar en cache
                    self.calibradores_cache[mercado] = calibrador

                    logger.debug(
                        f"Calibrador cargado para {mercado.value}: {metodo}"
                    )
                    return calibrador

        except Exception as e:
            logger.error(f"Error cargando calibrador para {mercado.value}: {e}")
            return None

    def guardar_calibrador(
        self,
        calibrador: CalibradorBase,
        metricas: ResultadoCalibracion,
        cutoff_datos: Optional[date] = None,
        notas: Optional[str] = None,
    ) -> UUID:
        """
        Guarda un calibrador en la base de datos.

        Args:
            calibrador: Calibrador entrenado
            metricas: Métricas del entrenamiento
            cutoff_datos: Fecha de corte de los datos usados
            notas: Notas adicionales

        Returns:
            UUID del calibrador guardado

        Raises:
            ValueError: Si el calibrador no está entrenado
        """
        if not calibrador.entrenado:
            raise ValueError("El calibrador debe estar entrenado antes de guardar")

        calibrador_id = uuid4()
        parametros_json = calibrador.to_dict()

        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO calibradores_futbol (
                            id, mercado, metodo, fecha_entrenamiento,
                            cutoff_datos, n_muestras_entrenamiento,
                            parametros_json, brier_antes, brier_despues,
                            mejora_validacion, log_loss_antes, log_loss_despues,
                            activo, notas
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            calibrador_id,
                            calibrador.mercado.value,
                            calibrador.NOMBRE_METODO,
                            metricas.fecha_entrenamiento,
                            cutoff_datos,
                            metricas.n_muestras,
                            json.dumps(parametros_json),
                            metricas.brier_antes,
                            metricas.brier_despues,
                            metricas.mejora_brier_porcentual,
                            metricas.log_loss_antes,
                            metricas.log_loss_despues,
                            False,  # No activar automáticamente
                            notas,
                        ),
                    )
                    conn.commit()

            logger.info(
                f"Calibrador guardado: {calibrador_id} para {calibrador.mercado.value}"
            )
            return calibrador_id

        except Exception as e:
            logger.error(f"Error guardando calibrador: {e}")
            raise

    def activar_calibrador(
        self,
        calibrador_id: UUID,
        validar_mejora: bool = True,
    ) -> bool:
        """
        Activa un calibrador, desactivando el anterior.

        Args:
            calibrador_id: ID del calibrador a activar
            validar_mejora: Si verificar que mejora el Brier Score

        Returns:
            True si se activó correctamente

        Raises:
            ValueError: Si el calibrador no existe o no mejora
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    # Obtener info del nuevo calibrador
                    cur.execute(
                        """
                        SELECT mercado, brier_despues
                        FROM calibradores_futbol
                        WHERE id = %s
                        """,
                        (calibrador_id,),
                    )
                    row = cur.fetchone()

                    if not row:
                        raise ValueError(f"Calibrador no encontrado: {calibrador_id}")

                    mercado, nuevo_brier = row

                    if validar_mejora:
                        # Obtener Brier del calibrador activo actual
                        cur.execute(
                            """
                            SELECT brier_despues
                            FROM calibradores_futbol
                            WHERE mercado = %s AND activo = TRUE
                            """,
                            (mercado,),
                        )
                        actual = cur.fetchone()

                        if actual and actual[0] < nuevo_brier:
                            logger.warning(
                                f"El nuevo calibrador no mejora: "
                                f"actual={actual[0]:.4f}, nuevo={nuevo_brier:.4f}"
                            )
                            return False

                    # Desactivar calibrador anterior
                    cur.execute(
                        """
                        UPDATE calibradores_futbol
                        SET activo = FALSE
                        WHERE mercado = %s AND activo = TRUE
                        """,
                        (mercado,),
                    )

                    # Activar nuevo calibrador
                    cur.execute(
                        """
                        UPDATE calibradores_futbol
                        SET activo = TRUE
                        WHERE id = %s
                        """,
                        (calibrador_id,),
                    )

                    conn.commit()

                    # Invalidar cache
                    mercado_enum = TipoMercadoFutbol(mercado)
                    if mercado_enum in self.calibradores_cache:
                        del self.calibradores_cache[mercado_enum]

                    logger.info(f"Calibrador activado: {calibrador_id}")
                    return True

        except Exception as e:
            logger.error(f"Error activando calibrador: {e}")
            raise

    def desactivar_calibrador(self, mercado: TipoMercadoFutbol) -> bool:
        """
        Desactiva el calibrador activo de un mercado.

        Args:
            mercado: Tipo de mercado

        Returns:
            True si había un calibrador activo que se desactivó
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE calibradores_futbol
                        SET activo = FALSE
                        WHERE mercado = %s AND activo = TRUE
                        RETURNING id
                        """,
                        (mercado.value,),
                    )
                    resultado = cur.fetchone()
                    conn.commit()

                    # Invalidar cache
                    if mercado in self.calibradores_cache:
                        del self.calibradores_cache[mercado]

                    if resultado:
                        logger.info(f"Calibrador desactivado para {mercado.value}")
                        return True
                    return False

        except Exception as e:
            logger.error(f"Error desactivando calibrador: {e}")
            return False

    def obtener_todos_activos(self) -> Dict[TipoMercadoFutbol, CalibradorBase]:
        """
        Obtiene todos los calibradores activos.

        Returns:
            Diccionario de mercado → calibrador
        """
        calibradores = {}

        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT mercado, metodo, parametros_json, fecha_entrenamiento
                        FROM calibradores_futbol
                        WHERE activo = TRUE
                        """
                    )

                    for row in cur.fetchall():
                        mercado_str, metodo, parametros_json, fecha_ent = row

                        mercado = TipoMercadoFutbol(mercado_str)
                        clase = CALIBRADORES_DISPONIBLES.get(metodo)

                        if clase:
                            data = parametros_json if parametros_json else {}
                            data["mercado"] = mercado_str
                            data["metodo"] = metodo
                            data["entrenado"] = True
                            if fecha_ent:
                                data["fecha_entrenamiento"] = fecha_ent.isoformat()

                            calibrador = clase.from_dict(data)
                            calibradores[mercado] = calibrador
                            self.calibradores_cache[mercado] = calibrador

            logger.debug(f"Cargados {len(calibradores)} calibradores activos")
            return calibradores

        except Exception as e:
            logger.error(f"Error obteniendo calibradores activos: {e}")
            return {}

    def calibrar_probabilidad(
        self,
        mercado: TipoMercadoFutbol,
        prob_raw: Union[float, np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Calibra una probabilidad usando el calibrador activo del mercado.

        Si no hay calibrador activo, retorna la probabilidad sin modificar.

        Args:
            mercado: Tipo de mercado
            prob_raw: Probabilidad(es) sin calibrar

        Returns:
            Probabilidad(es) calibrada(s) o raw si no hay calibrador
        """
        calibrador = self.cargar_calibrador_activo(mercado)

        if calibrador is None:
            logger.debug(
                f"Sin calibrador para {mercado.value}, usando prob raw"
            )
            return prob_raw

        return calibrador.calibrar(prob_raw)

    def limpiar_cache(self) -> None:
        """Limpia el cache de calibradores."""
        self.calibradores_cache.clear()
        logger.debug("Cache de calibradores limpiado")

    def obtener_historial(
        self,
        mercado: TipoMercadoFutbol,
        limite: int = 10,
    ) -> list:
        """
        Obtiene el historial de calibradores para un mercado.

        Args:
            mercado: Tipo de mercado
            limite: Número máximo de registros

        Returns:
            Lista de diccionarios con info de calibradores
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, metodo, fecha_entrenamiento,
                               brier_antes, brier_despues, mejora_validacion,
                               n_muestras_entrenamiento, activo
                        FROM calibradores_futbol
                        WHERE mercado = %s
                        ORDER BY creado_en DESC
                        LIMIT %s
                        """,
                        (mercado.value, limite),
                    )

                    historial = []
                    for row in cur.fetchall():
                        historial.append({
                            "id": str(row[0]),
                            "metodo": row[1],
                            "fecha_entrenamiento": row[2].isoformat() if row[2] else None,
                            "brier_antes": float(row[3]) if row[3] else None,
                            "brier_despues": float(row[4]) if row[4] else None,
                            "mejora_porcentual": float(row[5]) if row[5] else None,
                            "n_muestras": row[6],
                            "activo": row[7],
                        })

                    return historial

        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
