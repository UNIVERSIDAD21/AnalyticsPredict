# -*- coding: utf-8 -*-
"""
cache.py — Sistema de cache para features.

Este módulo implementa un cache en memoria para estadísticas calculadas,
evitando consultas repetidas a la base de datos.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ..constantes import CACHE_TTL_ESTADISTICAS, CACHE_MAX_ELEMENTOS

logger = logging.getLogger(__name__)


class CacheFeatures:
    """
    Cache en memoria para estadísticas de features.

    Implementa un cache LRU (Least Recently Used) con TTL (Time To Live).

    Atributos:
        ttl_segundos: Tiempo de vida de cada entrada en segundos
        max_elementos: Número máximo de elementos en cache
    """

    def __init__(
        self,
        ttl_segundos: int = CACHE_TTL_ESTADISTICAS,
        max_elementos: int = CACHE_MAX_ELEMENTOS,
    ):
        """
        Inicializa el cache.

        Args:
            ttl_segundos: Tiempo de vida de cada entrada
            max_elementos: Número máximo de elementos
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_segundos = ttl_segundos
        self._max_elementos = max_elementos
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def obtener(self, clave: str) -> Optional[Any]:
        """
        Obtiene un valor del cache.

        Args:
            clave: Clave del elemento

        Returns:
            El valor si existe y no ha expirado, None en caso contrario
        """
        with self._lock:
            if clave not in self._cache:
                self._misses += 1
                return None

            entrada = self._cache[clave]
            expiracion = entrada.get("expiracion")

            if expiracion and datetime.now() > expiracion:
                # La entrada ha expirado
                del self._cache[clave]
                self._misses += 1
                return None

            # Actualizar timestamp de acceso para LRU
            entrada["ultimo_acceso"] = datetime.now()
            self._hits += 1
            return entrada.get("valor")

    def guardar(self, clave: str, valor: Any) -> None:
        """
        Guarda un valor en el cache.

        Args:
            clave: Clave del elemento
            valor: Valor a guardar
        """
        with self._lock:
            # Verificar si necesitamos hacer espacio
            if len(self._cache) >= self._max_elementos and clave not in self._cache:
                self._evictar_lru()

            ahora = datetime.now()
            self._cache[clave] = {
                "valor": valor,
                "creado": ahora,
                "ultimo_acceso": ahora,
                "expiracion": ahora + timedelta(seconds=self._ttl_segundos),
            }

    def eliminar(self, clave: str) -> bool:
        """
        Elimina una entrada del cache.

        Args:
            clave: Clave del elemento

        Returns:
            True si se eliminó, False si no existía
        """
        with self._lock:
            if clave in self._cache:
                del self._cache[clave]
                return True
            return False

    def limpiar(self) -> None:
        """Limpia todo el cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.debug("Cache limpiado completamente")

    def limpiar_expirados(self) -> int:
        """
        Limpia entradas expiradas.

        Returns:
            Número de entradas eliminadas
        """
        with self._lock:
            ahora = datetime.now()
            claves_expiradas = [
                clave for clave, entrada in self._cache.items()
                if entrada.get("expiracion") and entrada["expiracion"] < ahora
            ]

            for clave in claves_expiradas:
                del self._cache[clave]

            if claves_expiradas:
                logger.debug(f"Eliminadas {len(claves_expiradas)} entradas expiradas del cache")

            return len(claves_expiradas)

    def _evictar_lru(self) -> None:
        """Elimina la entrada menos recientemente usada."""
        if not self._cache:
            return

        # Encontrar la entrada con el ultimo_acceso más antiguo
        clave_lru = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].get("ultimo_acceso", datetime.min)
        )

        del self._cache[clave_lru]
        logger.debug(f"Evictada entrada LRU: {clave_lru[:50]}...")

    @property
    def tamano(self) -> int:
        """Retorna el número de elementos en cache."""
        with self._lock:
            return len(self._cache)

    @property
    def estadisticas(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache."""
        with self._lock:
            total = self._hits + self._misses
            tasa_aciertos = self._hits / total if total > 0 else 0.0

            return {
                "elementos": len(self._cache),
                "max_elementos": self._max_elementos,
                "hits": self._hits,
                "misses": self._misses,
                "tasa_aciertos": tasa_aciertos,
                "ttl_segundos": self._ttl_segundos,
            }

    def contiene(self, clave: str) -> bool:
        """
        Verifica si una clave está en el cache (sin contar como acceso).

        Args:
            clave: Clave a verificar

        Returns:
            True si existe y no ha expirado
        """
        with self._lock:
            if clave not in self._cache:
                return False

            entrada = self._cache[clave]
            expiracion = entrada.get("expiracion")

            if expiracion and datetime.now() > expiracion:
                del self._cache[clave]
                return False

            return True

    def obtener_multiples(self, claves: list) -> Dict[str, Any]:
        """
        Obtiene múltiples valores del cache.

        Args:
            claves: Lista de claves a obtener

        Returns:
            Dict con {clave: valor} para las claves encontradas
        """
        resultado = {}
        for clave in claves:
            valor = self.obtener(clave)
            if valor is not None:
                resultado[clave] = valor
        return resultado

    def guardar_multiples(self, items: Dict[str, Any]) -> None:
        """
        Guarda múltiples valores en el cache.

        Args:
            items: Dict con {clave: valor}
        """
        for clave, valor in items.items():
            self.guardar(clave, valor)
