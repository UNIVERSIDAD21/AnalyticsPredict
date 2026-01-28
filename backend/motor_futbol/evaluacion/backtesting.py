# -*- coding: utf-8 -*-
"""
backtesting.py — Framework de backtesting para modelos de fútbol.

Este módulo permite validar los modelos con datos históricos,
simulando predicciones en tiempo real.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import numpy as np

from ..tipos import (
    TipoMercadoFutbol,
    PrediccionPartido,
    NivelConfianza,
)
from ..entrenamiento.entrenador import EntrenadorFutbol
from ..prediccion.predictor import PredictorFutbol
from .metricas import CalculadorMetricas

logger = logging.getLogger(__name__)


@dataclass
class ResultadoBacktest:
    """Resultado de un backtest completo."""
    fecha_inicio: date
    fecha_fin: date
    n_partidos: int
    n_predicciones: int

    # Métricas por mercado
    metricas_corners: Dict[str, Dict[str, float]] = field(default_factory=dict)
    metricas_goles: Dict[str, Dict[str, float]] = field(default_factory=dict)
    metricas_disparos: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Métricas globales
    mae_global: float = 0.0
    brier_global: float = 0.0
    ece_global: float = 0.0

    # Rentabilidad simulada
    roi_simulado: float = 0.0
    win_rate: float = 0.0
    n_apuestas_simuladas: int = 0

    # Metadata
    duracion_segundos: float = 0.0
    errores: List[str] = field(default_factory=list)
    config_usada: Dict[str, Any] = field(default_factory=dict)

    def resumen(self) -> str:
        """Genera resumen legible del backtest."""
        return f"""
=== RESUMEN BACKTEST ===
Período: {self.fecha_inicio} a {self.fecha_fin}
Partidos evaluados: {self.n_partidos}
Predicciones generadas: {self.n_predicciones}

MÉTRICAS GLOBALES:
- MAE promedio: {self.mae_global:.3f}
- Brier Score: {self.brier_global:.4f}
- ECE: {self.ece_global:.4f}

RENTABILIDAD SIMULADA:
- ROI: {self.roi_simulado:.2f}%
- Win Rate: {self.win_rate:.2f}%
- Apuestas simuladas: {self.n_apuestas_simuladas}

Duración: {self.duracion_segundos:.2f}s
Errores: {len(self.errores)}
"""


class BacktesterFutbol:
    """
    Framework de backtesting para modelos de fútbol.

    Permite evaluar modelos con datos históricos simulando
    el proceso de predicción en tiempo real.

    Características:
    - Reentrenamiento periódico (walk-forward)
    - Evaluación por mercado
    - Simulación de apuestas
    - Métricas de calibración
    """

    def __init__(self, pool):
        """
        Inicializa el backtester.

        Args:
            pool: ConnectionPool de psycopg
        """
        self._pool = pool
        self._resultados: List[Dict[str, Any]] = []

    def ejecutar_backtest(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        competiciones: Optional[List[str]] = None,
        mercados: Optional[List[TipoMercadoFutbol]] = None,
        reentrenar_cada_n_dias: int = 30,
        min_partidos_entrenamiento: int = 100,
    ) -> ResultadoBacktest:
        """
        Ejecuta backtest completo.

        Para cada día en el rango:
        1. Si toca reentrenar, entrena con datos hasta ese día
        2. Para cada partido del día:
           a. Genera predicción
           b. Compara con resultado real
        3. Calcula métricas

        Args:
            fecha_inicio: Inicio del período de backtest
            fecha_fin: Fin del período
            competiciones: Filtrar por competiciones
            mercados: Filtrar por mercados
            reentrenar_cada_n_dias: Frecuencia de reentrenamiento

        Returns:
            ResultadoBacktest con todas las métricas
        """
        logger.info(f"Iniciando backtest: {fecha_inicio} a {fecha_fin}")
        inicio = datetime.now()

        resultado = ResultadoBacktest(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            n_partidos=0,
            n_predicciones=0,
            config_usada={
                "competiciones": competiciones,
                "mercados": [m.value for m in mercados] if mercados else None,
                "reentrenar_cada_n_dias": reentrenar_cada_n_dias,
            },
        )

        # Obtener partidos en el rango
        partidos = self._obtener_partidos_backtest(fecha_inicio, fecha_fin, competiciones)

        if not partidos:
            logger.warning("No hay partidos para backtest")
            return resultado

        resultado.n_partidos = len(partidos)
        logger.info(f"Partidos a evaluar: {len(partidos)}")

        # Agrupar partidos por fecha para procesar secuencialmente
        partidos_por_fecha = self._agrupar_por_fecha(partidos)

        # Variables para tracking
        entrenador = EntrenadorFutbol(self._pool)
        predictor = PredictorFutbol(self._pool, cargar_modelos=False)

        ultimo_entrenamiento: Optional[date] = None
        predicciones_acumuladas: List[Dict[str, Any]] = []
        resultados_reales: List[Dict[str, Any]] = []

        # Procesar día por día
        for fecha_actual in sorted(partidos_por_fecha.keys()):
            # Verificar si toca reentrenar
            if self._debe_reentrenar(fecha_actual, ultimo_entrenamiento, reentrenar_cada_n_dias):
                try:
                    resultado_entrenamiento = entrenador.entrenar_para_backtest(
                        cutoff_fecha=fecha_actual,
                    )

                    if resultado_entrenamiento.get("estado") == "ok":
                        # Actualizar modelos en predictor
                        predictor.establecer_modelos(
                            modelo_corners=entrenador.obtener_modelo_corners(),
                            modelo_goles=entrenador.obtener_modelo_goles(),
                            modelo_disparos=entrenador.obtener_modelo_disparos(),
                        )
                        ultimo_entrenamiento = fecha_actual
                        logger.info(f"Modelo reentrenado para {fecha_actual}")
                    else:
                        logger.warning(f"Skip entrenamiento {fecha_actual}: {resultado_entrenamiento.get('razon')}")

                except Exception as e:
                    logger.error(f"Error entrenando para {fecha_actual}: {e}")
                    resultado.errores.append(f"Entrenamiento {fecha_actual}: {e}")
                    continue

            # Predecir partidos del día
            for partido in partidos_por_fecha[fecha_actual]:
                if not predictor.modelos_entrenados:
                    continue

                try:
                    prediccion = predictor.predecir_partido(
                        partido_id=UUID(str(partido["id"])),
                        fecha_corte=datetime.combine(fecha_actual, datetime.min.time()) - timedelta(days=1),
                    )

                    predicciones_acumuladas.append({
                        "partido_id": partido["id"],
                        "fecha": fecha_actual,
                        "prediccion": prediccion,
                    })

                    resultados_reales.append({
                        "partido_id": partido["id"],
                        "corners_ft": (partido.get("local_corners_total", 0) or 0) +
                                     (partido.get("visitante_corners_total", 0) or 0),
                        "goles_ft": (partido.get("local_goles_total", 0) or 0) +
                                   (partido.get("visitante_goles_total", 0) or 0),
                    })

                    resultado.n_predicciones += 1

                except Exception as e:
                    logger.warning(f"Error prediciendo partido {partido['id']}: {e}")
                    resultado.errores.append(f"Predicción {partido['id']}: {e}")

        # Calcular métricas finales
        if predicciones_acumuladas:
            metricas = self._calcular_metricas_backtest(
                predicciones_acumuladas,
                resultados_reales,
            )

            resultado.mae_global = metricas.get("mae_corners_ft", 0.0)
            resultado.brier_global = metricas.get("brier_corners_ft", 0.0)
            resultado.metricas_corners = metricas.get("corners", {})
            resultado.metricas_goles = metricas.get("goles", {})

            # Simular apuestas
            sim_apuestas = self._simular_apuestas_backtest(
                predicciones_acumuladas,
                resultados_reales,
            )
            resultado.roi_simulado = sim_apuestas.get("roi", 0.0)
            resultado.win_rate = sim_apuestas.get("win_rate", 0.0)
            resultado.n_apuestas_simuladas = sim_apuestas.get("n_apuestas", 0)

        resultado.duracion_segundos = (datetime.now() - inicio).total_seconds()

        logger.info(f"Backtest completado en {resultado.duracion_segundos:.2f}s")
        return resultado

    def _obtener_partidos_backtest(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        competiciones: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Obtiene partidos finalizados en el rango de fechas."""
        query = """
            SELECT
                p.id,
                p.fecha_partido,
                p.equipo_local_id,
                p.equipo_visitante_id,
                el.nombre as equipo_local,
                ev.nombre as equipo_visitante,
                p.local_corners_total,
                p.visitante_corners_total,
                p.local_goles_total,
                p.visitante_goles_total,
                c.codigo as competicion_codigo
            FROM partidos_futbol p
            JOIN equipos_futbol el ON p.equipo_local_id = el.id
            JOIN equipos_futbol ev ON p.equipo_visitante_id = ev.id
            JOIN competiciones_futbol c ON p.competicion_id = c.id
            WHERE p.estado = 'FINALIZADO'
              AND p.fecha_partido >= %s
              AND p.fecha_partido <= %s
        """

        parametros: List[Any] = [fecha_inicio, fecha_fin]

        if competiciones:
            query += " AND c.codigo = ANY(%s)"
            parametros.append(competiciones)

        query += " ORDER BY p.fecha_partido"

        partidos = []

        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parametros)
                columnas = [desc[0] for desc in cursor.description]

                for fila in cursor.fetchall():
                    partidos.append(dict(zip(columnas, fila)))

        return partidos

    def _agrupar_por_fecha(
        self,
        partidos: List[Dict[str, Any]],
    ) -> Dict[date, List[Dict[str, Any]]]:
        """Agrupa partidos por fecha."""
        agrupados: Dict[date, List[Dict[str, Any]]] = {}

        for partido in partidos:
            fecha = partido["fecha_partido"]
            if isinstance(fecha, datetime):
                fecha = fecha.date()

            if fecha not in agrupados:
                agrupados[fecha] = []
            agrupados[fecha].append(partido)

        return agrupados

    def _debe_reentrenar(
        self,
        fecha_actual: date,
        ultimo_entrenamiento: Optional[date],
        intervalo_dias: int,
    ) -> bool:
        """Determina si se debe reentrenar el modelo."""
        if ultimo_entrenamiento is None:
            return True

        dias_desde_ultimo = (fecha_actual - ultimo_entrenamiento).days
        return dias_desde_ultimo >= intervalo_dias

    def _calcular_metricas_backtest(
        self,
        predicciones: List[Dict[str, Any]],
        resultados: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calcula métricas de evaluación del backtest."""
        metricas: Dict[str, Any] = {}

        # Crear mapeo de resultados por partido_id
        resultados_map = {r["partido_id"]: r for r in resultados}

        # Evaluar corners FT
        corners_pred = []
        corners_real = []

        for pred_data in predicciones:
            partido_id = pred_data["partido_id"]
            prediccion = pred_data["prediccion"]

            if partido_id not in resultados_map:
                continue

            resultado = resultados_map[partido_id]

            # Obtener predicción de corners totales
            mercado_corners = prediccion.mercados_corners.get(TipoMercadoFutbol.CORNERS_FT.value)
            if mercado_corners:
                corners_pred.append(mercado_corners.media)
                corners_real.append(resultado["corners_ft"])

        if corners_pred:
            corners_pred_arr = np.array(corners_pred)
            corners_real_arr = np.array(corners_real)

            metricas["mae_corners_ft"] = CalculadorMetricas.mae(corners_real_arr, corners_pred_arr)
            metricas["rmse_corners_ft"] = CalculadorMetricas.rmse(corners_real_arr, corners_pred_arr)
            metricas["mejora_vs_baseline"] = CalculadorMetricas.mejora_vs_baseline(
                corners_real_arr, corners_pred_arr
            )

            metricas["corners"] = {
                "n_predicciones": len(corners_pred),
                "mae": metricas["mae_corners_ft"],
                "rmse": metricas["rmse_corners_ft"],
            }

        return metricas

    def _simular_apuestas_backtest(
        self,
        predicciones: List[Dict[str, Any]],
        resultados: List[Dict[str, Any]],
        linea_base: float = 9.5,
        umbral_prob: float = 0.55,
    ) -> Dict[str, Any]:
        """
        Simula apuestas durante el backtest.

        Args:
            predicciones: Lista de predicciones generadas
            resultados: Lista de resultados reales
            linea_base: Línea a usar para over/under
            umbral_prob: Probabilidad mínima para apostar

        Returns:
            Dict con métricas de apuestas
        """
        resultados_map = {r["partido_id"]: r for r in resultados}

        apuestas = 0
        ganadas = 0
        stake_total = 0.0
        ganancias = 0.0

        cuota_tipica = 1.90  # Cuota típica para over/under

        for pred_data in predicciones:
            partido_id = pred_data["partido_id"]
            prediccion = pred_data["prediccion"]

            if partido_id not in resultados_map:
                continue

            resultado = resultados_map[partido_id]
            corners_real = resultado["corners_ft"]

            # Evaluar mercado de corners totales
            mercado = prediccion.mercados_corners.get(TipoMercadoFutbol.CORNERS_FT.value)
            if not mercado:
                continue

            # Obtener probabilidad over 9.5
            prob_over = mercado.probabilidades.get(f"over_{linea_base}", 0.5)

            # Decidir si apostar
            if prob_over >= umbral_prob:
                # Apostar OVER
                apuestas += 1
                stake_total += 1.0

                if corners_real > linea_base:
                    ganadas += 1
                    ganancias += (cuota_tipica - 1)
                else:
                    ganancias -= 1.0

            elif prob_over <= (1 - umbral_prob):
                # Apostar UNDER
                apuestas += 1
                stake_total += 1.0

                if corners_real < linea_base:
                    ganadas += 1
                    ganancias += (cuota_tipica - 1)
                else:
                    ganancias -= 1.0

        return {
            "n_apuestas": apuestas,
            "ganadas": ganadas,
            "roi": CalculadorMetricas.roi(ganancias, stake_total),
            "win_rate": CalculadorMetricas.win_rate(ganadas, apuestas),
            "ganancias_netas": ganancias,
        }

    def generar_reporte(
        self,
        resultado: ResultadoBacktest,
    ) -> str:
        """Genera reporte en markdown."""
        return f"""# Reporte de Backtest - Motor de Fútbol

## Información General

- **Período:** {resultado.fecha_inicio} a {resultado.fecha_fin}
- **Partidos evaluados:** {resultado.n_partidos}
- **Predicciones generadas:** {resultado.n_predicciones}
- **Duración:** {resultado.duracion_segundos:.2f} segundos

## Métricas de Predicción

### Corners

| Métrica | Valor |
|---------|-------|
| MAE | {resultado.mae_global:.3f} |
| Brier Score | {resultado.brier_global:.4f} |
| ECE | {resultado.ece_global:.4f} |

## Rentabilidad Simulada

| Métrica | Valor |
|---------|-------|
| ROI | {resultado.roi_simulado:.2f}% |
| Win Rate | {resultado.win_rate:.2f}% |
| Apuestas | {resultado.n_apuestas_simuladas} |

## Errores

Total de errores: {len(resultado.errores)}

---
*Generado automáticamente por BacktesterFutbol*
"""
