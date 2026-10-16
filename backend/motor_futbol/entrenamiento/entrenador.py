# -*- coding: utf-8 -*-
"""
entrenador.py — Entrenador de modelos de fútbol desde PostgreSQL.

Este módulo entrena los modelos Ridge directamente desde la base de datos,
siguiendo la arquitectura del módulo NBA.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, date, time, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

import numpy as np

from ..tipos import (
    TipoModelo,
    ConfiguracionEntrenamiento,
    ResultadoEntrenamiento,
    normalizar_nombre_equipo,
)
from ..constantes import (
    ALPHA_RIDGE_DEFAULT,
    TARGETS_CORNERS,
    TARGETS_GOLES,
    TARGETS_DISPAROS,
    MIN_PARTIDOS_EQUIPO_ENTRENAMIENTO,
)
from ..excepciones import DatosInsuficientes, ErrorEntrenamiento
from ..modelos.corners import ModeloCorners
from ..modelos.goles import ModeloGoles
from ..modelos.disparos import ModeloDisparos
from ..modelos.base import construir_matriz_diseno, ajustar_ridge
from .dataset import seleccionar, describir

logger = logging.getLogger(__name__)

MIN_PARTIDOS_ENTRENAMIENTO = 100
MIN_PARTIDOS_DEFAULT = MIN_PARTIDOS_ENTRENAMIENTO



class EntrenadorFutbol:
    """
    Entrenador de modelos Ridge desde PostgreSQL.

    Características:
    - Lee partidos válidos de la BD
    - Entrena modelos para corners, goles y disparos
    - Registra versiones en modelo_versiones_futbol
    - Soporta validación cruzada temporal

    Ejemplo:
        entrenador = EntrenadorFutbol(pool)
        resultados = entrenador.entrenar_completo()
    """

    def __init__(
        self,
        pool,
        config: Optional[ConfiguracionEntrenamiento] = None,
        alpha: Optional[float] = None,
        min_partidos: Optional[int] = None,
        **kwargs,
    ):
        """
        Inicializa el entrenador.

        Args:
            pool: ConnectionPool de psycopg
            config: Configuración de entrenamiento (opcional)
        """
        self._pool = pool
        self.config = config or ConfiguracionEntrenamiento()
        self.alpha = float(alpha if alpha is not None else ALPHA_RIDGE_DEFAULT)
        self.min_partidos = int(min_partidos if min_partidos is not None else MIN_PARTIDOS_DEFAULT)
        # Compatibilidad retroactiva: si no viene alpha en config, usar el parámetro histórico.
        if getattr(self.config, "alpha_ridge", None) is None:
            self.config.alpha_ridge = self.alpha
        self._ultimo_hash_datos: Optional[str] = None
        self._metricas: Dict[str, Any] = {}

    def entrenar_completo(
        self,
        config: Optional[ConfiguracionEntrenamiento] = None,
    ) -> Dict[str, ResultadoEntrenamiento]:
        """
        Entrena todos los modelos (corners, goles, disparos).

        Args:
            config: Configuración opcional (sobreescribe la del constructor)

        Returns:
            Dict con resultados por tipo de modelo
        """
        if config:
            self.config = config

        logger.info("Iniciando entrenamiento completo de modelos de fútbol...")
        inicio = datetime.now()
        for tipo in TipoModelo:
            setattr(self, '_modelo_' + tipo.value, None)

        # Obtener partidos
        partidos = self._normalizar_partidos(self._obtener_partidos_entrenamiento())

        if not partidos:
            raise DatosInsuficientes(
                "No hay partidos válidos para entrenamiento",
                partidos_disponibles=0,
                partidos_requeridos=self.min_partidos
            )

        logger.info(f"Partidos obtenidos: {len(partidos)}")

        self._ultimo_hash_datos = None

        resultados = {}

        # Entrenar modelo de corners
        try:
            resultado_corners = self._entrenar_modelo_corners(partidos)
            self._aplicar_compatibilidad_resultado(resultado_corners)
            resultados["corners"] = resultado_corners
            logger.info(f"Corners: MAE promedio = {resultado_corners.mae_promedio():.3f}")
        except Exception as e:
            logger.error(f"Error entrenando modelo de corners: {e}")

        # Entrenar modelo de goles
        try:
            resultado_goles = self._entrenar_modelo_goles(partidos)
            self._aplicar_compatibilidad_resultado(resultado_goles)
            resultados["goles"] = resultado_goles
            logger.info(f"Goles: MAE promedio = {resultado_goles.mae_promedio():.3f}")
        except Exception as e:
            logger.error(f"Error entrenando modelo de goles: {e}")

        # Entrenar modelo de disparos
        try:
            resultado_disparos = self._entrenar_modelo_disparos(partidos)
            self._aplicar_compatibilidad_resultado(resultado_disparos)
            resultados["disparos"] = resultado_disparos
            logger.info(f"Disparos: MAE promedio = {resultado_disparos.mae_promedio():.3f}")
        except Exception as e:
            logger.error(f"Error entrenando modelo de disparos: {e}")

        if not resultados:
            raise DatosInsuficientes(
                "No se pudieron entrenar modelos con los datos disponibles",
                partidos_disponibles=len(partidos),
                partidos_requeridos=self.min_partidos,
            )

        duracion = (datetime.now() - inicio).total_seconds()
        logger.info(f"Entrenamiento completo en {duracion:.2f}s")

        return resultados

    def entrenar_modelo(
        self,
        tipo: TipoModelo,
        config: Optional[ConfiguracionEntrenamiento] = None,
    ) -> ResultadoEntrenamiento:
        """
        Entrena un modelo específico.

        Args:
            tipo: Tipo de modelo a entrenar
            config: Configuración opcional

        Returns:
            ResultadoEntrenamiento
        """
        if config:
            self.config = config

        partidos = self._normalizar_partidos(self._obtener_partidos_entrenamiento())

        if tipo == TipoModelo.CORNERS:
            return self._entrenar_modelo_corners(partidos)
        elif tipo == TipoModelo.GOLES:
            return self._entrenar_modelo_goles(partidos)
        else:
            return self._entrenar_modelo_disparos(partidos)

    def entrenar_para_backtest(
        self,
        cutoff_fecha: date,
        config: Optional[ConfiguracionEntrenamiento] = None,
    ) -> Dict[str, Any]:
        """
        Entrena modelos con datos hasta cutoff_fecha.

        Usado por backtesting para simular entrenamiento en el pasado.

        Args:
            cutoff_fecha: Fecha límite para datos de entrenamiento
            config: Configuración opcional

        Returns:
            Dict con modelos entrenados y metadata
        """
        if config:
            self.config = config

        # Modificar config para usar fecha de corte
        self.config.fecha_corte = cutoff_fecha

        logger.info(f"Entrenamiento backtest con cutoff: {cutoff_fecha}")

        partidos = self._normalizar_partidos(self._obtener_partidos_entrenamiento())

        if len(partidos) < self.min_partidos:
            logger.warning(f"Pocos partidos para entrenamiento: {len(partidos)}")
            return {
                "estado": "skip",
                "razon": "datos insuficientes",
                "partidos": len(partidos),
            }

        # Entrenar modelos
        modelo_corners = self._entrenar_modelo_corners(partidos)
        modelo_goles = self._entrenar_modelo_goles(partidos)
        modelo_disparos = self._entrenar_modelo_disparos(partidos)

        return {
            "estado": "ok",
            "modelo_corners": self.obtener_modelo_corners(),
            "modelo_goles": self.obtener_modelo_goles(),
            "modelo_disparos": self.obtener_modelo_disparos(),
            "partidos": len(partidos),
            "cutoff": cutoff_fecha,
        }

    def _obtener_partidos_entrenamiento(self) -> List[Dict]:
        """Obtiene partidos válidos para entrenamiento."""
        query = """
            SELECT
                p.id,
                p.fecha_partido,
                p.competicion_id,
                p.temporada_id,
                el.nombre as equipo_local,
                ev.nombre as equipo_visitante,

                -- Corners
                p.local_corners_1t,
                p.local_corners_2t,
                p.local_corners_total,
                p.visitante_corners_1t,
                p.visitante_corners_2t,
                p.visitante_corners_total,

                -- Goles
                p.local_goles_1t,
                p.local_goles_2t,
                p.local_goles_total,
                p.visitante_goles_1t,
                p.visitante_goles_2t,
                p.visitante_goles_total,

                -- Disparos
                p.local_disparos_total,
                p.local_disparos_arco,
                p.visitante_disparos_total,
                p.visitante_disparos_arco,

                c.codigo as competicion_codigo
            FROM partidos_futbol p
            JOIN equipos_futbol el ON p.equipo_local_id = el.id
            JOIN equipos_futbol ev ON p.equipo_visitante_id = ev.id
            JOIN competiciones_futbol c ON p.competicion_id = c.id
            WHERE p.estado = 'FINALIZADO' AND p.valido IS TRUE
        """

        parametros: List[Any] = []

        if self.config.fecha_minima:
            desde = self.config.fecha_minima
            if isinstance(desde, datetime):
                if desde.tzinfo is None:
                    raise ValueError('El inicio datetime requiere zona horaria')
            else:
                desde = datetime.combine(desde, time.min, tzinfo=timezone.utc)
            query += " AND p.fecha_partido >= %s"
            parametros.append(desde)

        if self.config.temporadas:
            query += " AND p.temporada_id::text = ANY(%s)"
            parametros.append(self.config.temporadas)

        # Filtrar por competiciones
        if self.config.competiciones:
            query += " AND c.codigo = ANY(%s)"
            parametros.append(self.config.competiciones)

        # Filtrar por fecha de corte
        if self.config.fecha_corte:
            query += " AND p.fecha_partido < %s"
            # Una fecha SQL depende del TimeZone de la conexión. El contrato es UTC.
            corte = self.config.fecha_corte
            if isinstance(corte, datetime):
                if corte.tzinfo is None:
                    raise ValueError('El cutoff datetime requiere zona horaria')
            else:
                corte = datetime.combine(corte, time.min, tzinfo=timezone.utc)
            parametros.append(corte)

        # Excluir copas si se indica
        if not self.config.incluir_copas:
                codigos_excluir = ['EUR_CHAMPIONS', 'EUR_EUROPA', 'EUR_CONFERENCE']
                query += " AND c.codigo NOT IN (%s, %s, %s)"
                parametros.extend(codigos_excluir)

        query += " ORDER BY p.fecha_partido"

        partidos = []

        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parametros)
                columnas = [desc[0] for desc in cursor.description]

                for fila in cursor.fetchall():
                    if isinstance(fila, dict):
                        partidos.append(fila)
                    else:
                        partidos.append(dict(zip(columnas, fila)))

        return partidos

    def _entrenar_modelo_corners(
        self,
        partidos: List[Dict],
    ) -> ResultadoEntrenamiento:
        """Entrena el modelo de corners."""
        # Filtrar partidos con datos de corners completos
        partidos_validos, excluidos = seleccionar(partidos, TipoModelo.CORNERS, self.config.min_partidos_equipo)

        if len(partidos_validos) < self.min_partidos:
            raise DatosInsuficientes(
                "Pocos partidos con corners completos",
                partidos_disponibles=len(partidos_validos),
                partidos_requeridos=self.min_partidos
            )

        # Preparar datos
        X, y_dict, nombres_equipos, fechas = self._preparar_datos_corners(partidos_validos)

        # Crear y entrenar modelo
        modelo = ModeloCorners()
        resultado = modelo.entrenar(
            X=X,
            y_dict=y_dict,
            nombres_equipos=nombres_equipos,
            alpha=self.config.alpha_ridge,
            fechas=fechas,
        )

        # Guardar modelo entrenado para uso posterior
        self._modelo_corners = modelo
        self._completar_modelo(modelo, resultado, partidos_validos, excluidos)
        return resultado

    def _entrenar_modelo_goles(
        self,
        partidos: List[Dict],
    ) -> ResultadoEntrenamiento:
        """Entrena el modelo de goles."""
        partidos_validos, excluidos = seleccionar(partidos, TipoModelo.GOLES, self.config.min_partidos_equipo)

        if len(partidos_validos) < self.min_partidos:
            raise DatosInsuficientes(
                "Pocos partidos con goles completos",
                partidos_disponibles=len(partidos_validos),
                partidos_requeridos=self.min_partidos
            )

        X, y_dict, nombres_equipos, fechas = self._preparar_datos_goles(partidos_validos)

        modelo = ModeloGoles()
        resultado = modelo.entrenar(
            X=X,
            y_dict=y_dict,
            nombres_equipos=nombres_equipos,
            alpha=self.config.alpha_ridge,
            fechas=fechas,
        )

        self._modelo_goles = modelo
        self._completar_modelo(modelo, resultado, partidos_validos, excluidos)
        return resultado

    def _entrenar_modelo_disparos(
        self,
        partidos: List[Dict],
    ) -> ResultadoEntrenamiento:
        """Entrena el modelo de disparos."""
        partidos_validos, excluidos = seleccionar(partidos, TipoModelo.DISPAROS, self.config.min_partidos_equipo)

        if len(partidos_validos) < self.min_partidos:
            raise DatosInsuficientes(
                "Pocos partidos con disparos",
                partidos_disponibles=len(partidos_validos),
                partidos_requeridos=self.min_partidos
            )

        X, y_dict, nombres_equipos, fechas = self._preparar_datos_disparos(partidos_validos)

        modelo = ModeloDisparos()
        resultado = modelo.entrenar(
            X=X,
            y_dict=y_dict,
            nombres_equipos=nombres_equipos,
            alpha=self.config.alpha_ridge,
            fechas=fechas,
        )

        self._modelo_disparos = modelo
        self._completar_modelo(modelo, resultado, partidos_validos, excluidos)
        return resultado

    def diagnosticar_dataset(self) -> Dict[str, Any]:
        """Solo lectura: mismos filtros de calidad y mínimos que el entrenamiento."""
        partidos = self._normalizar_partidos(self._obtener_partidos_entrenamiento())
        informe = {}
        for tipo in TipoModelo:
            efectivos, excluidos = seleccionar(partidos, tipo, self.config.min_partidos_equipo)
            informe[tipo.value] = describir(efectivos, tipo, excluidos)
            informe[tipo.value]['min_partidos'] = self.min_partidos
            informe[tipo.value]['entrenable_tecnicamente'] = len(efectivos) >= self.min_partidos
        return informe

    def _completar_modelo(self, modelo, resultado, partidos, excluidos):
        modelo.dataset = describir(partidos, modelo.tipo, excluidos)
        modelo.dataset['config'] = self.config.to_dict()
        resultado.hash_datos = modelo.dataset['hash_sha256']
        modelo.metricas = {
            'ambito': 'AJUSTE_IN_SAMPLE_NO_VALIDACION',
            'mae_promedio': resultado.mae_promedio(),
            'mae_por_target': resultado.mae_por_target,
            'rmse_por_target': resultado.rmse_por_target,
            'r2_por_target': resultado.r2_por_target,
        }
        # El diseño tiene dos perspectivas por partido; no son dos eventos.
        resultado.n_partidos = len(partidos)
        hashes = {tipo.value: getattr(self, '_modelo_' + tipo.value).dataset['hash_sha256']
                  for tipo in TipoModelo if getattr(self, '_modelo_' + tipo.value, None) is not None}
        self._ultimo_hash_datos = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()

    def _preparar_datos_corners(
        self,
        partidos: List[Dict],
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray], List[str], np.ndarray]:
        """Prepara matrices para entrenamiento de corners."""
        equipos_set = set()
        filas_equipo = []
        filas_rival = []
        filas_es_local = []
        fechas = []

        y_local_1t = []
        y_local_2t = []
        y_visitante_1t = []
        y_visitante_2t = []

        for p in partidos:
            local = p["equipo_local"]
            visitante = p["equipo_visitante"]

            equipos_set.add(normalizar_nombre_equipo(local))
            equipos_set.add(normalizar_nombre_equipo(visitante))

            fecha = p["fecha_partido"]

            # Perspectiva local
            filas_equipo.append(local)
            filas_rival.append(visitante)
            filas_es_local.append(1)
            fechas.append(fecha)

            y_local_1t.append(p["local_corners_1t"])
            y_local_2t.append(p["local_corners_2t"])
            y_visitante_1t.append(p["visitante_corners_1t"])
            y_visitante_2t.append(p["visitante_corners_2t"])

            # Perspectiva visitante
            filas_equipo.append(visitante)
            filas_rival.append(local)
            filas_es_local.append(0)
            fechas.append(fecha)

            y_local_1t.append(p["visitante_corners_1t"])
            y_local_2t.append(p["visitante_corners_2t"])
            y_visitante_1t.append(p["local_corners_1t"])
            y_visitante_2t.append(p["local_corners_2t"])

        # Crear mapeo de equipos
        equipos_ordenados = sorted(equipos_set)
        entidad_a_indice = {nombre: i for i, nombre in enumerate(equipos_ordenados)}

        # Construir matriz de diseño
        X = construir_matriz_diseno(filas_equipo, filas_rival, filas_es_local, entidad_a_indice)

        # Construir dict de targets
        y_dict = {
            "corners_local_1t": np.array(y_local_1t, dtype=float),
            "corners_local_2t": np.array(y_local_2t, dtype=float),
            "corners_visitante_1t": np.array(y_visitante_1t, dtype=float),
            "corners_visitante_2t": np.array(y_visitante_2t, dtype=float),
        }

        return X, y_dict, filas_equipo, np.array(fechas)

    def _preparar_datos_goles(
        self,
        partidos: List[Dict],
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray], List[str], np.ndarray]:
        """Prepara matrices para entrenamiento de goles."""
        equipos_set = set()
        filas_equipo = []
        filas_rival = []
        filas_es_local = []
        fechas = []

        y_local_1t = []
        y_local_2t = []
        y_visitante_1t = []
        y_visitante_2t = []

        for p in partidos:
            local = p["equipo_local"]
            visitante = p["equipo_visitante"]

            equipos_set.add(normalizar_nombre_equipo(local))
            equipos_set.add(normalizar_nombre_equipo(visitante))

            fecha = p["fecha_partido"]

            # Perspectiva local
            filas_equipo.append(local)
            filas_rival.append(visitante)
            filas_es_local.append(1)
            fechas.append(fecha)

            y_local_1t.append(p["local_goles_1t"])
            y_local_2t.append(p["local_goles_2t"])
            y_visitante_1t.append(p["visitante_goles_1t"])
            y_visitante_2t.append(p["visitante_goles_2t"])

            # Perspectiva visitante
            filas_equipo.append(visitante)
            filas_rival.append(local)
            filas_es_local.append(0)
            fechas.append(fecha)

            y_local_1t.append(p["visitante_goles_1t"])
            y_local_2t.append(p["visitante_goles_2t"])
            y_visitante_1t.append(p["local_goles_1t"])
            y_visitante_2t.append(p["local_goles_2t"])

        equipos_ordenados = sorted(equipos_set)
        entidad_a_indice = {nombre: i for i, nombre in enumerate(equipos_ordenados)}

        X = construir_matriz_diseno(filas_equipo, filas_rival, filas_es_local, entidad_a_indice)

        y_dict = {
            "goles_local_1t": np.array(y_local_1t, dtype=float),
            "goles_local_2t": np.array(y_local_2t, dtype=float),
            "goles_visitante_1t": np.array(y_visitante_1t, dtype=float),
            "goles_visitante_2t": np.array(y_visitante_2t, dtype=float),
        }

        return X, y_dict, filas_equipo, np.array(fechas)

    def _preparar_datos_disparos(
        self,
        partidos: List[Dict],
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray], List[str], np.ndarray]:
        """Prepara matrices para entrenamiento de disparos."""
        equipos_set = set()
        filas_equipo = []
        filas_rival = []
        filas_es_local = []
        fechas = []

        y_local_total = []
        y_local_arco = []
        y_visitante_total = []
        y_visitante_arco = []

        for p in partidos:
            local = p["equipo_local"]
            visitante = p["equipo_visitante"]

            equipos_set.add(normalizar_nombre_equipo(local))
            equipos_set.add(normalizar_nombre_equipo(visitante))

            fecha = p["fecha_partido"]

            # Perspectiva local
            filas_equipo.append(local)
            filas_rival.append(visitante)
            filas_es_local.append(1)
            fechas.append(fecha)

            y_local_total.append(p["local_disparos_total"])
            y_local_arco.append(p["local_disparos_arco"])
            y_visitante_total.append(p["visitante_disparos_total"])
            y_visitante_arco.append(p["visitante_disparos_arco"])

            # Perspectiva visitante
            filas_equipo.append(visitante)
            filas_rival.append(local)
            filas_es_local.append(0)
            fechas.append(fecha)

            y_local_total.append(p["visitante_disparos_total"])
            y_local_arco.append(p["visitante_disparos_arco"])
            y_visitante_total.append(p["local_disparos_total"])
            y_visitante_arco.append(p["local_disparos_arco"])

        equipos_ordenados = sorted(equipos_set)
        entidad_a_indice = {nombre: i for i, nombre in enumerate(equipos_ordenados)}

        X = construir_matriz_diseno(filas_equipo, filas_rival, filas_es_local, entidad_a_indice)

        y_dict = {
            "disparos_local_total": np.array(y_local_total, dtype=float),
            "disparos_local_arco": np.array(y_local_arco, dtype=float),
            "disparos_visitante_total": np.array(y_visitante_total, dtype=float),
            "disparos_visitante_arco": np.array(y_visitante_arco, dtype=float),
        }

        return X, y_dict, filas_equipo, np.array(fechas)

    def _aplicar_compatibilidad_resultado(self, resultado: ResultadoEntrenamiento) -> None:
        """Expone atributos legacy esperados por tests históricos."""
        if not hasattr(resultado, "modelo"):
            resultado.modelo = resultado.tipo_modelo.value  # type: ignore[attr-defined]
        if not hasattr(resultado, "metricas"):
            resultado.metricas = resultado.mae_por_target  # type: ignore[attr-defined]
        if not hasattr(resultado, "fecha_entrenamiento"):
            resultado.fecha_entrenamiento = datetime.now()  # type: ignore[attr-defined]

    def _normalizar_partidos(self, partidos: List[Dict]) -> List[Dict]:
        """Normaliza claves legacy de tests para compatibilidad de contrato."""
        normalizados = []
        for p in partidos:
            item = dict(p)
            item.setdefault("id", item.get("partido_id"))
            item.setdefault("equipo_local", item.get("equipo_local_nombre"))
            item.setdefault("equipo_visitante", item.get("equipo_visitante_nombre"))
            item.setdefault("local_corners_1t", item.get("corners_local_1t"))
            item.setdefault("local_corners_2t", item.get("corners_local_2t"))
            item.setdefault("visitante_corners_1t", item.get("corners_visitante_1t"))
            item.setdefault("visitante_corners_2t", item.get("corners_visitante_2t"))
            item.setdefault("local_goles_1t", item.get("goles_local_1t"))
            item.setdefault("local_goles_2t", item.get("goles_local_2t"))
            item.setdefault("visitante_goles_1t", item.get("goles_visitante_1t"))
            item.setdefault("visitante_goles_2t", item.get("goles_visitante_2t"))
            item.setdefault("local_disparos_total", item.get("disparos_local"))
            item.setdefault("visitante_disparos_total", item.get("disparos_visitante"))
            item.setdefault("local_disparos_arco", item.get("disparos_arco_local"))
            item.setdefault("visitante_disparos_arco", item.get("disparos_arco_visitante"))
            normalizados.append(item)
        return normalizados

    def _calcular_hash_datos(self, partidos: List[Dict]) -> str:
        """Calcula hash MD5 de los datos para detectar cambios."""
        datos_ordenados = sorted(
            partidos,
            key=lambda p: (p.get("fecha_partido"), str(p.get("id"))),
        )

        datos_str = json.dumps(
            [(
                str(p.get("id", p.get("partido_id", str(p)))),
                p["fecha_partido"].isoformat() if p.get("fecha_partido") else None,
            ) for p in datos_ordenados],
            sort_keys=True,
        )

        return hashlib.sha256(datos_str.encode()).hexdigest()[:16]

    def obtener_modelo_corners(self) -> Optional[ModeloCorners]:
        """Retorna el modelo de corners entrenado."""
        return getattr(self, "_modelo_corners", None)

    def obtener_modelo_goles(self) -> Optional[ModeloGoles]:
        """Retorna el modelo de goles entrenado."""
        return getattr(self, "_modelo_goles", None)

    def obtener_modelo_disparos(self) -> Optional[ModeloDisparos]:
        """Retorna el modelo de disparos entrenado."""
        return getattr(self, "_modelo_disparos", None)

    @property
    def hash_datos(self) -> Optional[str]:
        """Retorna el hash de los últimos datos usados."""
        return self._ultimo_hash_datos
