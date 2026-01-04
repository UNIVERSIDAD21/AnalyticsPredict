# -*- coding: utf-8 -*-
"""
entrenador_bd.py — Entrenador de modelo Ridge desde PostgreSQL.

Este módulo entrena el modelo directamente desde la tabla `partidos` de la base de datos,
eliminando la dependencia de archivos CSV.

IMPORTANTE: El modelo se reentrena automáticamente cuando:
1. Se inicia el servidor y no hay modelo en memoria
2. Se detectan nuevos partidos en la BD
3. Se llama explícitamente a reentrenar()

Uso:
    from entrenador_bd import EntrenadorBD
    
    entrenador = EntrenadorBD()
    modelo = entrenador.entrenar()
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

CUARTOS = ("Q1", "Q2", "Q3", "Q4")
ALPHA_RIDGE = 5.0

# Mapeo de nombres para normalización
MAPEO_NOMBRES = {
    "la clippers": "los angeles clippers",
    "la lakers": "los angeles lakers",
    "lac": "los angeles clippers",
    "lal": "los angeles lakers",
}


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ══════════════════════════════════════════════════════════════════════════════

def normalizar_nombre(nombre: str) -> str:
    """
    Normaliza el nombre de un equipo a minúsculas sin espacios extra.
    Aplica mapeo de nombres alternativos.
    """
    nombre = " ".join((nombre or "").strip().lower().replace("_", " ").split())
    return MAPEO_NOMBRES.get(nombre, nombre)


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
    """
    n = len(nombres_equipo)
    k = len(entidad_a_indice)
    X = np.zeros((n, 1 + k + k + 1), dtype=float)
    X[:, 0] = 1.0  # Intercepto
    
    for i, (equipo, rival, local) in enumerate(zip(nombres_equipo, nombres_rival, es_local)):
        idx_equipo = entidad_a_indice[normalizar_nombre(equipo)]
        idx_rival = entidad_a_indice[normalizar_nombre(rival)]
        X[i, 1 + idx_equipo] = 1.0
        X[i, 1 + k + idx_rival] = 1.0
        X[i, -1] = float(local)
    
    return X


def ajustar_ridge(X: np.ndarray, Y: np.ndarray, alpha: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ajusta regresión Ridge y retorna pesos y desviación estándar.
    
    La regularización Ridge penaliza coeficientes grandes para evitar overfitting.
    """
    p = X.shape[1]
    I = np.eye(p, dtype=float)
    I[0, 0] = 0.0  # No regularizar el intercepto
    
    A = X.T @ X + alpha * I
    B = X.T @ Y
    W = np.linalg.solve(A, B)
    
    residuos = Y - X @ W
    std = np.sqrt(np.mean(residuos**2, axis=0) + 1e-9)
    
    return W, std


# ══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class EntrenadorBD:
    """
    Entrenador de modelo Ridge que lee directamente desde PostgreSQL.
    
    Características:
    - Lee todos los partidos válidos de la BD
    - Calcula automáticamente los equipos únicos
    - Genera hash de datos para detectar cambios
    - Almacena métricas de entrenamiento
    
    Ejemplo:
        entrenador = EntrenadorBD(obtener_pool())
        modelo = entrenador.entrenar()
        
        # Verificar si hay datos nuevos
        if entrenador.hay_datos_nuevos():
            modelo = entrenador.entrenar()
    """
    
    def __init__(self, pool):
        """
        Inicializa el entrenador.
        
        Args:
            pool: ConnectionPool de psycopg para la base de datos
        """
        self._pool = pool
        self._ultimo_hash_datos: Optional[str] = None
        self._ultima_fecha_entrenamiento: Optional[datetime] = None
        self._metricas: Dict[str, Any] = {}
    
    def _obtener_partidos(
        self,
        incluir_pretemporada: bool = False,
        temporadas: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Obtiene todos los partidos válidos de la base de datos.
        
        Args:
            incluir_pretemporada: Si True, incluye partidos de pretemporada
            temporadas: Lista opcional de IDs de temporada a filtrar
            
        Returns:
            Lista de diccionarios con los datos de cada partido
        """
        query = """
            SELECT 
                p.id,
                p.fecha_partido,
                p.tipo_partido,
                el.nombre as equipo_local,
                ev.nombre as equipo_visitante,
                p.local_q1, p.local_q2, p.local_q3, p.local_q4,
                p.visitante_q1, p.visitante_q2, p.visitante_q3, p.visitante_q4
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            WHERE 
                p.local_q1 IS NOT NULL 
                AND p.local_q2 IS NOT NULL 
                AND p.local_q3 IS NOT NULL 
                AND p.local_q4 IS NOT NULL
                AND p.visitante_q1 IS NOT NULL 
                AND p.visitante_q2 IS NOT NULL 
                AND p.visitante_q3 IS NOT NULL 
                AND p.visitante_q4 IS NOT NULL
        """
        parametros: List[object] = []

        if temporadas:
            query += " AND p.temporada_id = ANY(%s)"
            parametros.append(temporadas)

        if not incluir_pretemporada:
            query += " AND COALESCE(p.tipo_partido, 'REG') != 'PRE'"
        
        query += " ORDER BY p.fecha_partido"
        
        partidos = []
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parametros)
                columnas = [desc[0] for desc in cursor.description]
                for fila in cursor.fetchall():
                    partidos.append(dict(zip(columnas, fila)))
        
        return partidos
    
    def _calcular_hash_datos(self, partidos: List[Dict]) -> str:
        """
        Calcula un hash único de los datos para detectar cambios.

        Esto permite saber si necesitamos reentrenar sin comparar
        todos los registros uno por uno.
        """
        datos_str = json.dumps([
            (str(p['id']), p['local_q1'], p['local_q2'], p['local_q3'], p['local_q4'],
             p['visitante_q1'], p['visitante_q2'], p['visitante_q3'], p['visitante_q4'])
            for p in partidos
        ], sort_keys=True)

        return hashlib.sha256(datos_str.encode()).hexdigest()[:16]
    
    def _obtener_conteo_partidos(self) -> int:
        """Obtiene el conteo actual de partidos válidos en la BD."""
        query = """
            SELECT COUNT(*) FROM partidos 
            WHERE local_q1 IS NOT NULL 
            AND local_q2 IS NOT NULL 
            AND local_q3 IS NOT NULL 
            AND local_q4 IS NOT NULL
            AND visitante_q1 IS NOT NULL 
            AND visitante_q2 IS NOT NULL 
            AND visitante_q3 IS NOT NULL 
            AND visitante_q4 IS NOT NULL
            AND COALESCE(tipo_partido, 'REG') != 'PRE'
        """
        
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]
    
    def hay_datos_nuevos(self) -> bool:
        """
        Verifica si hay datos nuevos que requieran reentrenamiento.
        
        Compara el hash actual de los datos con el último hash conocido.
        Es más eficiente que comparar todos los registros.
        
        Returns:
            True si hay datos nuevos o si nunca se ha entrenado
        """
        if self._ultimo_hash_datos is None:
            return True
        
        partidos = self._obtener_partidos()
        hash_actual = self._calcular_hash_datos(partidos)
        
        return hash_actual != self._ultimo_hash_datos
    
    def entrenar(
        self,
        alpha: float = ALPHA_RIDGE,
        temporadas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Entrena el modelo Ridge desde la base de datos.
        
        Este método:
        1. Lee todos los partidos válidos de la BD
        2. Extrae equipos únicos y crea índices
        3. Construye matrices de diseño
        4. Entrena modelos Ridge para equipo y rival
        5. Calcula métricas de evaluación
        
        Args:
            alpha: Parámetro de regularización Ridge (default: 5.0)
            temporadas: Lista opcional de IDs de temporada a usar en el entrenamiento
            
        Returns:
            Diccionario con el modelo entrenado listo para usar
            
        Raises:
            ValueError: Si no hay partidos válidos en la BD
        """
        logger.info("🏀 Iniciando entrenamiento desde base de datos...")
        inicio = datetime.now()
        
        # 1. Obtener partidos
        partidos = self._obtener_partidos(temporadas=temporadas)
        
        if not partidos:
            raise ValueError(
                "No hay partidos válidos en la base de datos. "
                "Asegúrate de que la tabla 'partidos' tenga datos con puntos por cuarto."
            )
        
        logger.info(f"📊 Partidos cargados: {len(partidos)}")
        
        # 2. Preparar datos - Cada partido genera DOS filas de entrenamiento
        # Una desde la perspectiva del equipo local y otra del visitante
        equipos_set = set()
        
        filas_equipo = []
        filas_rival = []
        filas_es_local = []
        filas_y_equipo = []
        filas_y_rival = []
        
        for p in partidos:
            local = p['equipo_local']
            visitante = p['equipo_visitante']
            
            equipos_set.add(normalizar_nombre(local))
            equipos_set.add(normalizar_nombre(visitante))
            
            # Fila 1: Perspectiva del equipo local
            filas_equipo.append(local)
            filas_rival.append(visitante)
            filas_es_local.append(1)
            filas_y_equipo.append([p['local_q1'], p['local_q2'], p['local_q3'], p['local_q4']])
            filas_y_rival.append([p['visitante_q1'], p['visitante_q2'], p['visitante_q3'], p['visitante_q4']])
            
            # Fila 2: Perspectiva del equipo visitante
            filas_equipo.append(visitante)
            filas_rival.append(local)
            filas_es_local.append(0)
            filas_y_equipo.append([p['visitante_q1'], p['visitante_q2'], p['visitante_q3'], p['visitante_q4']])
            filas_y_rival.append([p['local_q1'], p['local_q2'], p['local_q3'], p['local_q4']])
        
        # 3. Crear índices de equipos
        equipos_ordenados = sorted(equipos_set)
        entidad_a_indice = {nombre: i for i, nombre in enumerate(equipos_ordenados)}
        
        logger.info(f"🏀 Equipos en el modelo: {len(equipos_ordenados)}")
        
        # 4. Construir matrices
        X = construir_matriz_diseno(filas_equipo, filas_rival, filas_es_local, entidad_a_indice)
        Y_equipo = np.array(filas_y_equipo, dtype=float)
        Y_rival = np.array(filas_y_rival, dtype=float)
        
        logger.info(f"📐 Matriz de diseño: {X.shape}")
        
        # 5. Entrenar modelos
        logger.info(f"🎯 Entrenando modelo Ridge (alpha={alpha})...")
        
        pesos_equipo, std_equipo = ajustar_ridge(X, Y_equipo, alpha)
        pesos_rival, std_rival = ajustar_ridge(X, Y_rival, alpha)
        
        # 6. Calcular métricas
        pred_equipo = X @ pesos_equipo
        pred_rival = X @ pesos_rival
        
        mae_equipo = np.mean(np.abs(Y_equipo - pred_equipo), axis=0)
        mae_rival = np.mean(np.abs(Y_rival - pred_rival), axis=0)
        
        # 7. Actualizar estado interno
        self._ultimo_hash_datos = self._calcular_hash_datos(partidos)
        self._ultima_fecha_entrenamiento = datetime.now()
        
        duracion = (datetime.now() - inicio).total_seconds()
        
        self._metricas = {
            "partidos_entrenamiento": len(partidos),
            "filas_entrenamiento": len(filas_equipo),
            "equipos": len(equipos_ordenados),
            "mae_equipo_por_cuarto": {q: float(m) for q, m in zip(CUARTOS, mae_equipo)},
            "mae_rival_por_cuarto": {q: float(m) for q, m in zip(CUARTOS, mae_rival)},
            "duracion_segundos": duracion,
            "fecha_entrenamiento": self._ultima_fecha_entrenamiento.isoformat(),
            "hash_datos": self._ultimo_hash_datos,
            "temporadas": list(temporadas) if temporadas else None,
        }
        
        logger.info(f"✅ Modelo entrenado en {duracion:.2f}s")
        logger.info(f"   MAE equipo: {', '.join(f'{q}: {m:.2f}' for q, m in zip(CUARTOS, mae_equipo))}")
        
        # 8. Retornar modelo en formato compatible
        return {
            "alpha": alpha,
            "entidad_a_indice": entidad_a_indice,
            "pesos_equipo": pesos_equipo,
            "pesos_rival": pesos_rival,
            "desviacion_equipo": std_equipo,
            "desviacion_rival": std_rival,
            "metricas": self._metricas,
        }
    
    def guardar_modelo(self, modelo: Dict[str, Any], ruta: str) -> None:
        """
        Guarda el modelo entrenado en un archivo .npz.
        
        Útil para backup o para pre-cargar al iniciar el servidor.
        
        Args:
            modelo: Diccionario del modelo entrenado
            ruta: Ruta donde guardar el archivo
        """
        import os
        os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)
        
        np.savez_compressed(
            ruta,
            alpha=np.array([float(modelo["alpha"])], dtype=float),
            entity_json=np.array([json.dumps(modelo["entidad_a_indice"], ensure_ascii=False)], dtype=object),
            w_team=modelo["pesos_equipo"],
            w_opp=modelo["pesos_rival"],
            std_team=modelo["desviacion_equipo"],
            std_opp=modelo["desviacion_rival"],
        )
        
        logger.info(f"💾 Modelo guardado en: {ruta}")
    
    @property
    def metricas(self) -> Dict[str, Any]:
        """Retorna las métricas del último entrenamiento."""
        return self._metricas.copy()
    
    @property
    def ultima_fecha_entrenamiento(self) -> Optional[datetime]:
        """Retorna la fecha del último entrenamiento."""
        return self._ultima_fecha_entrenamiento
