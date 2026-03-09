# -*- coding: utf-8 -*-
"""
validacion.py — Validación cruzada temporal para modelos de fútbol.

Este módulo implementa validación cruzada respetando el orden temporal
de los datos para evitar data leakage.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Any

import numpy as np

from ..constantes import ALPHA_RIDGE_DEFAULT, ALPHAS_BUSQUEDA

logger = logging.getLogger(__name__)


class ValidacionCruzadaTemporal:
    """
    Validación cruzada temporal (TimeSeriesSplit).

    A diferencia de la validación cruzada estándar, esta respeta
    el orden temporal de los datos, entrenando siempre con datos
    anteriores y validando con datos posteriores.

    Esquema de validación:
    ```
    Fold 1: Train [t0, t1]  → Test [t1, t2]
    Fold 2: Train [t0, t2]  → Test [t2, t3]
    Fold 3: Train [t0, t3]  → Test [t3, t4]
    ...
    ```
    """

    def __init__(
        self,
        n_folds: int = 4,
        min_train_size: int = 100,
        min_test_size: int = 20,
    ):
        """
        Inicializa el validador.

        Args:
            n_folds: Número de folds de validación
            min_train_size: Mínimo de muestras en training
            min_test_size: Mínimo de muestras en test
        """
        self.n_folds = n_folds
        self.min_train_size = min_train_size
        self.min_test_size = min_test_size

    def split(
        self,
        X: np.ndarray,
        fechas: np.ndarray,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Genera índices de train/test para cada fold.

        Args:
            X: Matriz de features
            fechas: Array de fechas correspondientes

        Returns:
            Lista de tuplas (train_indices, test_indices)
        """
        n = len(fechas)

        if n < self.min_train_size + self.min_test_size:
            logger.warning(f"Dataset muy pequeño ({n}), retornando split único")
            mid = int(n * 0.8)
            return [(np.arange(mid), np.arange(mid, n))]

        # Ordenar por fecha
        orden = np.argsort(fechas)

        # Calcular tamaño de cada porción
        total_test = n // (self.n_folds + 1)
        splits = []

        for fold in range(self.n_folds):
            # Training: todo hasta cierto punto
            train_end = (fold + 1) * total_test + self.min_train_size
            train_end = min(train_end, n - self.min_test_size)

            # Test: siguiente porción
            test_start = train_end
            test_end = min(test_start + total_test, n)

            if test_end <= test_start or train_end <= self.min_train_size:
                continue

            train_indices = orden[:train_end]
            test_indices = orden[test_start:test_end]

            if len(train_indices) >= self.min_train_size and len(test_indices) >= self.min_test_size:
                splits.append((train_indices, test_indices))

        return splits

    def evaluar_modelo(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        fechas: np.ndarray,
        alpha: float,
    ) -> Dict[str, float]:
        """
        Evalúa un modelo con validación cruzada temporal.

        Args:
            X: Matriz de features
            Y: Matriz de targets
            fechas: Array de fechas
            alpha: Parámetro de regularización

        Returns:
            Dict con métricas promediadas
        """
        from ..modelos.base import ajustar_ridge

        splits = self.split(X, fechas)

        if not splits:
            logger.warning("No se pudieron generar splits")
            return {"mae": float("inf"), "rmse": float("inf")}

        maes = []
        rmses = []

        for train_idx, test_idx in splits:
            X_train = X[train_idx]
            Y_train = Y[train_idx]
            X_test = X[test_idx]
            Y_test = Y[test_idx]

            # Entrenar
            pesos, _ = ajustar_ridge(X_train, Y_train, alpha)

            # Predecir
            predicciones = X_test @ pesos

            # Calcular métricas
            mae = float(np.mean(np.abs(Y_test - predicciones)))
            rmse = float(np.sqrt(np.mean((Y_test - predicciones) ** 2)))

            maes.append(mae)
            rmses.append(rmse)

        return {
            "mae": np.mean(maes),
            "mae_std": np.std(maes),
            "rmse": np.mean(rmses),
            "rmse_std": np.std(rmses),
            "n_folds": len(splits),
        }

    def buscar_alpha_optimo(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        fechas: np.ndarray,
        alphas: List[float] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Busca el alpha óptimo usando validación cruzada temporal.

        Args:
            X: Matriz de features
            Y: Matriz de targets
            fechas: Array de fechas
            alphas: Lista de alphas a probar

        Returns:
            Tupla (mejor_alpha, resultados_por_alpha)
        """
        if alphas is None:
            alphas = ALPHAS_BUSQUEDA

        resultados = {}
        mejor_alpha = ALPHA_RIDGE_DEFAULT
        mejor_mae = float("inf")

        for alpha in alphas:
            metricas = self.evaluar_modelo(X, Y, fechas, alpha)
            resultados[alpha] = metricas

            logger.debug(f"Alpha {alpha}: MAE = {metricas['mae']:.4f}")

            if metricas["mae"] < mejor_mae:
                mejor_mae = metricas["mae"]
                mejor_alpha = alpha

        logger.info(f"Mejor alpha: {mejor_alpha} (MAE = {mejor_mae:.4f})")

        return mejor_alpha, resultados


class TimeSeriesSplitFutbol:
    """Compatibilidad con tests legacy, wrapper simple temporal."""

    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits

    def split(self, fechas: np.ndarray):
        n = len(fechas)
        if n <= self.n_splits + 1:
            yield np.arange(max(1, n - 1)), np.arange(max(1, n - 1), n)
            return
        fold = n // (self.n_splits + 1)
        for i in range(self.n_splits):
            train_end = (i + 1) * fold
            test_end = min((i + 2) * fold, n)
            if train_end < 1 or test_end <= train_end:
                continue
            yield np.arange(train_end), np.arange(train_end, test_end)


class ValidacionTemporal:
    """Compatibilidad con API esperada por tests históricos."""

    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits
        self._splitter = TimeSeriesSplitFutbol(n_splits=n_splits)

    def _generar_splits(self, fechas: np.ndarray):
        return self._splitter.split(fechas)

    def validar(self, modelo, X: np.ndarray, y: np.ndarray, fechas: np.ndarray):
        metricas = []
        for train_idx, test_idx in self._generar_splits(fechas):
            X_train, y_train = X[train_idx], y[train_idx]
            X_test, y_test = X[test_idx], y[test_idx]
            modelo.entrenar(X_train, y_train)
            pred = modelo.predecir(X_test)
            if isinstance(pred, tuple):
                pred = pred[0]
            mae = float(np.mean(np.abs(y_test - pred))) if len(y_test) else 0.0
            metricas.append({"mae": mae, "n_test": len(test_idx)})
        return {"metricas_por_fold": metricas}


class ValidacionPorTemporada:
    """
    Validación leave-one-season-out.

    Entrena con todas las temporadas menos una, y valida con esa temporada.
    """

    def __init__(self):
        """Inicializa el validador."""
        pass

    def split_por_temporada(
        self,
        temporadas: np.ndarray,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Genera splits dejando una temporada fuera.

        Args:
            temporadas: Array con ID de temporada de cada muestra

        Returns:
            Lista de tuplas (train_indices, test_indices)
        """
        temporadas_unicas = np.unique(temporadas)
        splits = []

        for temp_test in temporadas_unicas:
            train_mask = temporadas != temp_test
            test_mask = temporadas == temp_test

            train_idx = np.where(train_mask)[0]
            test_idx = np.where(test_mask)[0]

            if len(train_idx) > 50 and len(test_idx) > 10:
                splits.append((train_idx, test_idx))

        return splits

    def evaluar_modelo(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        temporadas: np.ndarray,
        alpha: float,
    ) -> Dict[str, Any]:
        """
        Evalúa modelo con validación por temporada.

        Returns:
            Dict con métricas por temporada y promedio
        """
        from ..modelos.base import ajustar_ridge

        splits = self.split_por_temporada(temporadas)
        resultados_temporada = {}

        for train_idx, test_idx in splits:
            temp = temporadas[test_idx[0]]

            X_train = X[train_idx]
            Y_train = Y[train_idx]
            X_test = X[test_idx]
            Y_test = Y[test_idx]

            pesos, _ = ajustar_ridge(X_train, Y_train, alpha)
            predicciones = X_test @ pesos

            mae = float(np.mean(np.abs(Y_test - predicciones)))
            rmse = float(np.sqrt(np.mean((Y_test - predicciones) ** 2)))

            resultados_temporada[str(temp)] = {
                "mae": mae,
                "rmse": rmse,
                "n_test": len(test_idx),
            }

        if resultados_temporada:
            mae_promedio = np.mean([r["mae"] for r in resultados_temporada.values()])
            rmse_promedio = np.mean([r["rmse"] for r in resultados_temporada.values()])
        else:
            mae_promedio = float("inf")
            rmse_promedio = float("inf")

        return {
            "mae_promedio": mae_promedio,
            "rmse_promedio": rmse_promedio,
            "por_temporada": resultados_temporada,
        }
