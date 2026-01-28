# -*- coding: utf-8 -*-
"""
base.py — Clase base para modelos de predicción Ridge.

Este módulo implementa la clase base ModeloPrediccionBase que define
la interfaz común para todos los modelos de predicción (corners, goles, disparos).
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

from ..tipos import (
    TipoModelo,
    ResultadoEntrenamiento,
    ModeloRidgeFutbol,
    normalizar_nombre_equipo,
)
from ..constantes import ALPHA_RIDGE_DEFAULT, ALPHAS_BUSQUEDA
from ..excepciones import ModeloNoEntrenado, ErrorEntrenamiento

logger = logging.getLogger(__name__)


def construir_matriz_diseno(
    nombres_equipo: List[str],
    nombres_rival: List[str],
    es_local: List[int],
    entidad_a_indice: Dict[str, int],
) -> np.ndarray:
    """
    Construye la matriz de diseño para regresión Ridge.

    La matriz tiene la estructura:
    [1, one-hot-equipo, one-hot-rival, es_local]

    Args:
        nombres_equipo: Lista de nombres de equipos
        nombres_rival: Lista de nombres de rivales
        es_local: Lista de 1/0 indicando si es local
        entidad_a_indice: Mapeo nombre -> índice

    Returns:
        Matriz de diseño (n, 1 + 2*k + 1)
    """
    n = len(nombres_equipo)
    k = len(entidad_a_indice)
    X = np.zeros((n, 1 + k + k + 1), dtype=float)
    X[:, 0] = 1.0  # Intercepto

    for i, (equipo, rival, local) in enumerate(zip(nombres_equipo, nombres_rival, es_local)):
        equipo_norm = normalizar_nombre_equipo(equipo)
        rival_norm = normalizar_nombre_equipo(rival)

        if equipo_norm in entidad_a_indice:
            idx_equipo = entidad_a_indice[equipo_norm]
            X[i, 1 + idx_equipo] = 1.0

        if rival_norm in entidad_a_indice:
            idx_rival = entidad_a_indice[rival_norm]
            X[i, 1 + k + idx_rival] = 1.0

        X[i, -1] = float(local)

    return X


def ajustar_ridge(
    X: np.ndarray,
    Y: np.ndarray,
    alpha: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ajusta regresión Ridge y retorna pesos y desviación estándar.

    Fórmula matemática:
    W = (X'X + αI)^(-1) X'Y

    Args:
        X: Matriz de diseño (n, p)
        Y: Matriz de targets (n, m)
        alpha: Parámetro de regularización

    Returns:
        Tuple de (pesos, std_residuales)
    """
    p = X.shape[1]
    I = np.eye(p, dtype=float)
    I[0, 0] = 0.0  # No regularizar el intercepto

    A = X.T @ X + alpha * I
    B = X.T @ Y

    # Resolver sistema lineal
    W = np.linalg.solve(A, B)

    # Calcular residuales y desviación estándar
    residuos = Y - X @ W
    std = np.sqrt(np.mean(residuos**2, axis=0) + 1e-9)

    return W, std


class ModeloPrediccionBase(ABC):
    """
    Clase base abstracta para modelos de predicción Ridge.

    Esta clase define la interfaz común que deben implementar
    todos los modelos de predicción (corners, goles, disparos).

    Atributos:
        tipo: Tipo de modelo (corners, goles, disparos)
        targets: Lista de targets que predice el modelo
        alfa: Parámetro de regularización Ridge
        entidad_a_indice: Mapeo equipo -> índice
        pesos: Dict de pesos por target
        std_residuales: Dict de desviaciones por target
    """

    def __init__(self, tipo: TipoModelo, targets: List[str]):
        """
        Inicializa modelo vacío.

        Args:
            tipo: Tipo de modelo
            targets: Lista de targets que predice
        """
        self.tipo = tipo
        self.targets = targets
        self.alfa: float = ALPHA_RIDGE_DEFAULT
        self.entidad_a_indice: Dict[str, int] = {}
        self.pesos: Dict[str, np.ndarray] = {}
        self.std_residuales: Dict[str, float] = {}
        self.metricas: Dict[str, float] = {}
        self.fecha_entrenamiento: Optional[datetime] = None
        self.version_id: Optional[int] = None
        self._entrenado = False

    @property
    def entrenado(self) -> bool:
        """Indica si el modelo ha sido entrenado."""
        return self._entrenado and len(self.pesos) > 0

    @property
    def cantidad_equipos(self) -> int:
        """Retorna la cantidad de equipos en el modelo."""
        return len(self.entidad_a_indice)

    def contiene_equipo(self, nombre: str) -> bool:
        """Verifica si un equipo está en el modelo."""
        nombre_norm = normalizar_nombre_equipo(nombre)
        return nombre_norm in self.entidad_a_indice

    def obtener_equipos(self) -> List[str]:
        """Retorna lista de nombres de equipos en el modelo."""
        return list(self.entidad_a_indice.keys())

    def entrenar(
        self,
        X: np.ndarray,
        y_dict: Dict[str, np.ndarray],
        nombres_equipos: List[str],
        alpha: Optional[float] = None,
        fechas: Optional[np.ndarray] = None,
    ) -> ResultadoEntrenamiento:
        """
        Entrena el modelo con validación cruzada.

        Args:
            X: Matriz de features (n_partidos, n_features)
            y_dict: Dict {target: array de valores}
            nombres_equipos: Lista de nombres para mapeo
            alpha: Parámetro de regularización. Si None, busca óptimo
            fechas: Array de fechas para validación cruzada temporal

        Returns:
            ResultadoEntrenamiento con métricas
        """
        inicio = datetime.now()
        logger.info(f"Iniciando entrenamiento de modelo {self.tipo.value}...")

        # Verificar datos
        if X.shape[0] == 0:
            raise ErrorEntrenamiento("No hay datos de entrenamiento")

        if not y_dict:
            raise ErrorEntrenamiento("No hay targets especificados")

        # Crear mapeo de equipos
        equipos_unicos = sorted(set(normalizar_nombre_equipo(n) for n in nombres_equipos))
        self.entidad_a_indice = {nombre: i for i, nombre in enumerate(equipos_unicos)}

        logger.info(f"Equipos en modelo: {len(equipos_unicos)}")
        logger.info(f"Partidos de entrenamiento: {X.shape[0]}")

        # Buscar alpha óptimo si no se especifica
        if alpha is None and fechas is not None:
            alpha = self._buscar_alpha_optimo(X, y_dict, fechas)
            logger.info(f"Alpha óptimo encontrado: {alpha}")
        elif alpha is None:
            alpha = ALPHA_RIDGE_DEFAULT
            logger.info(f"Usando alpha por defecto: {alpha}")

        self.alfa = alpha

        # Entrenar para cada target
        mae_por_target = {}
        rmse_por_target = {}
        r2_por_target = {}

        for target in self.targets:
            if target not in y_dict:
                logger.warning(f"Target {target} no encontrado en datos")
                continue

            Y = y_dict[target].reshape(-1, 1) if y_dict[target].ndim == 1 else y_dict[target]

            # Ajustar modelo Ridge
            pesos, std = ajustar_ridge(X, Y, self.alfa)

            self.pesos[target] = pesos.flatten()
            self.std_residuales[target] = float(std[0]) if std.size > 0 else 1.0

            # Calcular métricas
            predicciones = (X @ pesos).flatten()
            y_real = Y.flatten()

            mae = float(np.mean(np.abs(y_real - predicciones)))
            rmse = float(np.sqrt(np.mean((y_real - predicciones) ** 2)))

            # R²
            ss_res = np.sum((y_real - predicciones) ** 2)
            ss_tot = np.sum((y_real - np.mean(y_real)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

            mae_por_target[target] = mae
            rmse_por_target[target] = rmse
            r2_por_target[target] = float(r2)

            logger.info(f"  {target}: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}")

        self._entrenado = True
        self.fecha_entrenamiento = datetime.now()

        duracion = (datetime.now() - inicio).total_seconds()
        logger.info(f"Entrenamiento completado en {duracion:.2f}s")

        return ResultadoEntrenamiento(
            tipo_modelo=self.tipo,
            targets=self.targets,
            fecha_entrenamiento=self.fecha_entrenamiento,
            n_partidos=X.shape[0],
            n_equipos=len(equipos_unicos),
            mae_por_target=mae_por_target,
            rmse_por_target=rmse_por_target,
            r2_por_target=r2_por_target,
            std_residuales=self.std_residuales.copy(),
            alpha_usado=self.alfa,
            duracion_segundos=duracion,
        )

    def predecir(
        self,
        X: np.ndarray,
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Genera predicciones para cada target.

        Args:
            X: Matriz de features (n_partidos, n_features)

        Returns:
            Dict con {target: (medias, stds)}
        """
        if not self.entrenado:
            raise ModeloNoEntrenado(self.tipo.value)

        resultados = {}

        for target in self.targets:
            if target not in self.pesos:
                continue

            pesos = self.pesos[target]
            medias = X @ pesos
            std = self.std_residuales.get(target, 1.0)
            stds = np.full_like(medias, std)

            resultados[target] = (medias, stds)

        return resultados

    def predecir_partido(
        self,
        equipo: str,
        rival: str,
        es_local: bool = True,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Genera predicción para un partido individual.

        Args:
            equipo: Nombre del equipo
            rival: Nombre del rival
            es_local: True si el equipo juega de local

        Returns:
            Dict con {target: (media, std)}
        """
        if not self.entrenado:
            raise ModeloNoEntrenado(self.tipo.value)

        # Construir matriz de diseño para 1 partido
        X = construir_matriz_diseno(
            nombres_equipo=[equipo],
            nombres_rival=[rival],
            es_local=[1 if es_local else 0],
            entidad_a_indice=self.entidad_a_indice,
        )

        # Predecir
        predicciones = self.predecir(X)

        # Extraer valores escalares
        resultado = {}
        for target, (medias, stds) in predicciones.items():
            resultado[target] = (float(medias[0]), float(stds[0]))

        return resultado

    def _buscar_alpha_optimo(
        self,
        X: np.ndarray,
        y_dict: Dict[str, np.ndarray],
        fechas: np.ndarray,
        n_folds: int = 4,
    ) -> float:
        """
        Busca alpha óptimo con validación cruzada temporal.

        Args:
            X: Matriz de features
            y_dict: Dict de targets
            fechas: Array de fechas para ordenar
            n_folds: Número de folds

        Returns:
            Alpha óptimo
        """
        logger.info("Buscando alpha óptimo...")

        # Usar el primer target para búsqueda
        target = self.targets[0]
        if target not in y_dict:
            return ALPHA_RIDGE_DEFAULT

        Y = y_dict[target].reshape(-1, 1) if y_dict[target].ndim == 1 else y_dict[target]

        mejor_alpha = ALPHA_RIDGE_DEFAULT
        mejor_mae = float("inf")

        for alpha in ALPHAS_BUSQUEDA:
            mae = self._validacion_cruzada_temporal(X, Y, fechas, alpha, n_folds)
            logger.debug(f"  alpha={alpha}: MAE={mae:.4f}")

            if mae < mejor_mae:
                mejor_mae = mae
                mejor_alpha = alpha

        return mejor_alpha

    def _validacion_cruzada_temporal(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        fechas: np.ndarray,
        alpha: float,
        n_folds: int,
    ) -> float:
        """
        Ejecuta validación cruzada temporal.

        Args:
            X: Matriz de features
            Y: Matriz de targets
            fechas: Array de fechas
            alpha: Parámetro de regularización
            n_folds: Número de folds

        Returns:
            MAE promedio
        """
        n = len(fechas)
        if n < n_folds * 10:  # Mínimo 10 muestras por fold
            # Dataset muy pequeño, retornar MAE de entrenamiento
            pesos, _ = ajustar_ridge(X, Y, alpha)
            predicciones = X @ pesos
            return float(np.mean(np.abs(Y - predicciones)))

        # Ordenar por fecha
        orden = np.argsort(fechas)
        X_ordenado = X[orden]
        Y_ordenado = Y[orden]

        # Dividir en folds temporales
        fold_size = n // (n_folds + 1)
        maes = []

        for fold in range(n_folds):
            # Training: todo hasta cierto punto
            # Validation: siguiente porción
            train_end = (fold + 1) * fold_size
            val_end = (fold + 2) * fold_size

            if val_end > n:
                break

            X_train = X_ordenado[:train_end]
            Y_train = Y_ordenado[:train_end]
            X_val = X_ordenado[train_end:val_end]
            Y_val = Y_ordenado[train_end:val_end]

            if len(X_train) < 10 or len(X_val) < 5:
                continue

            pesos, _ = ajustar_ridge(X_train, Y_train, alpha)
            predicciones = X_val @ pesos
            mae = float(np.mean(np.abs(Y_val - predicciones)))
            maes.append(mae)

        return np.mean(maes) if maes else float("inf")

    def guardar(self, ruta: str) -> None:
        """
        Guarda modelo en formato .npz.

        Args:
            ruta: Ruta del archivo
        """
        import os
        os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)

        datos = {
            "tipo": np.array([self.tipo.value]),
            "alfa": np.array([self.alfa]),
            "entidad_json": np.array([json.dumps(self.entidad_a_indice)]),
            "targets": np.array(self.targets),
            "std_residuales": np.array([json.dumps(self.std_residuales)]),
        }

        # Agregar pesos por target
        for target, pesos in self.pesos.items():
            datos[f"pesos_{target}"] = pesos

        np.savez_compressed(ruta, **datos)
        logger.info(f"Modelo guardado en: {ruta}")

    @classmethod
    def cargar(cls, ruta: str) -> "ModeloPrediccionBase":
        """
        Carga modelo desde archivo .npz.

        Args:
            ruta: Ruta del archivo

        Returns:
            Instancia del modelo
        """
        with np.load(ruta, allow_pickle=True) as datos:
            tipo = TipoModelo(str(datos["tipo"][0]))
            targets = list(datos["targets"])

            # Crear instancia del tipo correcto
            from .corners import ModeloCorners
            from .goles import ModeloGoles
            from .disparos import ModeloDisparos

            if tipo == TipoModelo.CORNERS:
                modelo = ModeloCorners()
            elif tipo == TipoModelo.GOLES:
                modelo = ModeloGoles()
            else:
                modelo = ModeloDisparos()

            modelo.alfa = float(datos["alfa"][0])
            modelo.entidad_a_indice = json.loads(str(datos["entidad_json"][0]))
            modelo.std_residuales = json.loads(str(datos["std_residuales"][0]))

            # Cargar pesos
            for target in targets:
                clave = f"pesos_{target}"
                if clave in datos:
                    modelo.pesos[target] = datos[clave]

            modelo._entrenado = True

        logger.info(f"Modelo cargado desde: {ruta}")
        return modelo

    def a_modelo_ridge_futbol(self) -> ModeloRidgeFutbol:
        """Convierte a ModeloRidgeFutbol."""
        return ModeloRidgeFutbol(
            tipo=self.tipo,
            alfa=self.alfa,
            entidad_a_indice=self.entidad_a_indice,
            pesos=self.pesos,
            std_residuales=self.std_residuales,
            fecha_entrenamiento=self.fecha_entrenamiento,
            version_id=self.version_id,
            metricas=self.metricas,
        )

    @abstractmethod
    def predecir_completo(
        self,
        equipo: str,
        rival: str,
        es_local: bool,
    ) -> Dict[str, Any]:
        """
        Genera predicción completa para todos los mercados.

        Debe ser implementado por cada modelo específico.
        """
        pass
