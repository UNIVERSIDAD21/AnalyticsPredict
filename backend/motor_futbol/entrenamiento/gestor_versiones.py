# -*- coding: utf-8 -*-
"""
gestor_versiones.py — Gestión de versiones de modelos en BD.

Este módulo maneja el registro y recuperación de versiones de modelos
en la tabla modelo_versiones_futbol.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from ..tipos import TipoModelo, ResultadoEntrenamiento

logger = logging.getLogger(__name__)


class GestorVersiones:
    """
    Gestor de versiones de modelos en base de datos.

    Funcionalidades:
    - Registrar nuevas versiones de modelos
    - Consultar versiones activas
    - Activar/desactivar versiones
    - Cargar parámetros de versiones anteriores
    """

    def __init__(self, pool):
        """
        Inicializa el gestor.

        Args:
            pool: ConnectionPool de psycopg
        """
        self._pool = pool

    def registrar_version(
        self,
        tipo_modelo: TipoModelo,
        resultado: ResultadoEntrenamiento,
        hash_datos: str,
        ruta_archivo: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Registra una nueva versión del modelo en la BD.

        Args:
            tipo_modelo: Tipo de modelo (corners, goles, disparos)
            resultado: Resultado del entrenamiento
            hash_datos: Hash de los datos usados
            ruta_archivo: Ruta del archivo .npz (opcional)
            metadata: Metadata adicional (opcional)

        Returns:
            ID de la versión creada
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                # Obtener siguiente número de versión para este tipo
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(version), 0) + 1
                    FROM modelo_versiones_futbol
                    WHERE tipo_modelo = %s
                    """,
                    [tipo_modelo.value]
                )
                nueva_version = cursor.fetchone()[0]

                # Calcular MAEs por tiempo si están disponibles
                mae_1t = None
                mae_2t = None
                mae_total = None

                if resultado.mae_por_target:
                    maes = list(resultado.mae_por_target.values())
                    if len(maes) >= 2:
                        mae_1t = maes[0]  # Primer target (1T)
                        mae_2t = maes[1]  # Segundo target (2T)
                    mae_total = resultado.mae_promedio()

                # Preparar metadata
                full_metadata = {
                    **(metadata or {}),
                    "targets": resultado.targets,
                    "mae_por_target": resultado.mae_por_target,
                    "rmse_por_target": resultado.rmse_por_target,
                    "r2_por_target": resultado.r2_por_target,
                }

                # Insertar registro
                cursor.execute(
                    """
                    INSERT INTO modelo_versiones_futbol (
                        tipo_modelo,
                        version,
                        fecha_entrenamiento,
                        partidos_entrenamiento,
                        equipos,
                        mae_1t,
                        mae_2t,
                        mae_total,
                        duracion_segundos,
                        hash_datos,
                        ruta_archivo,
                        metadata,
                        activo
                    ) VALUES (
                        %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE
                    )
                    RETURNING id
                    """,
                    [
                        tipo_modelo.value,
                        nueva_version,
                        resultado.n_partidos,
                        resultado.n_equipos,
                        mae_1t,
                        mae_2t,
                        mae_total,
                        resultado.duracion_segundos,
                        hash_datos,
                        ruta_archivo,
                        json.dumps(full_metadata),
                    ]
                )
                version_id = cursor.fetchone()[0]

        logger.info(
            f"Registrada versión {nueva_version} de modelo {tipo_modelo.value} "
            f"(id={version_id}, partidos={resultado.n_partidos})"
        )

        return version_id

    def activar_version(
        self,
        tipo_modelo: TipoModelo,
        version_id: int,
    ) -> None:
        """
        Activa una versión específica (desactiva las demás).

        Args:
            tipo_modelo: Tipo de modelo
            version_id: ID de la versión a activar
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                # Desactivar todas las versiones de este tipo
                cursor.execute(
                    """
                    UPDATE modelo_versiones_futbol
                    SET activo = FALSE
                    WHERE tipo_modelo = %s AND activo = TRUE
                    """,
                    [tipo_modelo.value]
                )

                # Activar la versión especificada
                cursor.execute(
                    """
                    UPDATE modelo_versiones_futbol
                    SET activo = TRUE
                    WHERE id = %s AND tipo_modelo = %s
                    """,
                    [version_id, tipo_modelo.value]
                )

        logger.info(f"Activada versión {version_id} para modelo {tipo_modelo.value}")

    def obtener_version_activa(
        self,
        tipo_modelo: TipoModelo,
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de la versión activa.

        Args:
            tipo_modelo: Tipo de modelo

        Returns:
            Dict con información de la versión o None
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        version,
                        fecha_entrenamiento,
                        partidos_entrenamiento,
                        equipos,
                        mae_1t,
                        mae_2t,
                        mae_total,
                        hash_datos,
                        ruta_archivo,
                        metadata
                    FROM modelo_versiones_futbol
                    WHERE tipo_modelo = %s AND activo = TRUE
                    LIMIT 1
                    """,
                    [tipo_modelo.value]
                )
                fila = cursor.fetchone()

                if not fila:
                    return None

                columnas = [desc[0] for desc in cursor.description]
                resultado = dict(zip(columnas, fila))

                if resultado.get("metadata"):
                    resultado["metadata"] = json.loads(resultado["metadata"])

                return resultado

    def obtener_historial(
        self,
        tipo_modelo: TipoModelo,
        limite: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historial de versiones de un modelo.

        Args:
            tipo_modelo: Tipo de modelo
            limite: Número máximo de versiones

        Returns:
            Lista de versiones ordenadas por fecha (más reciente primero)
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        version,
                        fecha_entrenamiento,
                        partidos_entrenamiento,
                        equipos,
                        mae_total,
                        activo
                    FROM modelo_versiones_futbol
                    WHERE tipo_modelo = %s
                    ORDER BY fecha_entrenamiento DESC
                    LIMIT %s
                    """,
                    [tipo_modelo.value, limite]
                )

                columnas = [desc[0] for desc in cursor.description]
                return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    def obtener_version_por_id(
        self,
        version_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una versión específica por ID.

        Args:
            version_id: ID de la versión

        Returns:
            Dict con información o None
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM modelo_versiones_futbol
                    WHERE id = %s
                    """,
                    [version_id]
                )
                fila = cursor.fetchone()

                if not fila:
                    return None

                columnas = [desc[0] for desc in cursor.description]
                resultado = dict(zip(columnas, fila))

                if resultado.get("metadata"):
                    resultado["metadata"] = json.loads(resultado["metadata"])

                return resultado

    def generar_version(self) -> str:
        """Alias de compatibilidad para tests históricos."""
        return f"v1.0.0_{datetime.now().strftime('%Y%m%d')}"

    def guardar_modelo(
        self,
        modelo: Any,
        tipo: TipoModelo,
        version: str,
        metricas: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Compatibilidad retroactiva con contrato anterior de persistencia."""
        metricas = metricas or {}
        payload = modelo.to_dict() if hasattr(modelo, "to_dict") else {}

        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO modelo_versiones_futbol (
                        tipo_modelo,
                        version,
                        fecha_entrenamiento,
                        metadata,
                        activo
                    ) VALUES (%s, %s, NOW(), %s, FALSE)
                    RETURNING id
                    """,
                    [
                        tipo.value if hasattr(tipo, "value") else str(tipo),
                        version,
                        json.dumps({"metricas": metricas, "payload": payload}),
                    ],
                )
                row = cursor.fetchone()
                return int(row[0]) if row else 0

    def comparar_versiones(
        self,
        tipo_modelo: TipoModelo,
    ) -> Dict[str, Any]:
        """
        Compara métricas entre versiones de un modelo.

        Returns:
            Dict con estadísticas comparativas
        """
        historial = self.obtener_historial(tipo_modelo, limite=20)

        if not historial:
            return {"versiones": 0}

        maes = [v["mae_total"] for v in historial if v.get("mae_total")]

        return {
            "versiones": len(historial),
            "version_activa": next((v for v in historial if v.get("activo")), None),
            "mejor_mae": min(maes) if maes else None,
            "peor_mae": max(maes) if maes else None,
            "mae_promedio": sum(maes) / len(maes) if maes else None,
            "ultima_version": historial[0] if historial else None,
        }
