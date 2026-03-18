from __future__ import annotations

from collections import deque
from datetime import datetime
from threading import Lock
from typing import Deque


class ObservabilidadHTTP:
    """Acumulador en memoria para métricas HTTP operativas mínimas (A5).

    - p95 de latencia (ventana reciente)
    - tasa de error (5xx)
    - uptime del proceso
    """

    def __init__(self, max_muestras: int = 5000) -> None:
        self._inicio = datetime.now()
        self._latencias_ms: Deque[float] = deque(maxlen=max_muestras)
        self._total = 0
        self._errores_5xx = 0
        self._lock = Lock()

    def registrar(self, latencia_ms: float, status_code: int) -> None:
        latencia_sana = max(0.0, float(latencia_ms))
        with self._lock:
            self._latencias_ms.append(latencia_sana)
            self._total += 1
            if status_code >= 500:
                self._errores_5xx += 1

    def resumen(self, umbral_p95_ms: float = 800.0, umbral_error_rate: float = 0.05) -> dict:
        with self._lock:
            latencias = list(self._latencias_ms)
            total = self._total
            errores = self._errores_5xx

        p95 = self._percentil(latencias, 95)
        error_rate = (errores / total) if total > 0 else 0.0

        alertas = []
        if p95 is not None and p95 > umbral_p95_ms:
            alertas.append(
                f"LATENCIA_P95_ALTA: {p95:.2f}ms > {umbral_p95_ms:.2f}ms"
            )
        if error_rate > umbral_error_rate:
            alertas.append(
                f"ERROR_RATE_ALTO: {error_rate:.4f} > {umbral_error_rate:.4f}"
            )

        ahora = datetime.now()
        uptime_s = max(0.0, (ahora - self._inicio).total_seconds())

        return {
            "exito": True,
            "http": {
                "requests_total": total,
                "errors_5xx": errores,
                "error_rate": round(error_rate, 6),
                "latency_p95_ms": None if p95 is None else round(p95, 2),
                "samples": len(latencias),
            },
            "uptime": {
                "inicio": self._inicio.isoformat(),
                "segundos": round(uptime_s, 2),
            },
            "umbrales": {
                "latency_p95_ms": umbral_p95_ms,
                "error_rate": umbral_error_rate,
            },
            "alertas": alertas,
            "timestamp": ahora.isoformat(),
        }

    @staticmethod
    def _percentil(valores: list[float], percentil: float) -> float | None:
        if not valores:
            return None
        if len(valores) == 1:
            return valores[0]

        ordenados = sorted(valores)
        k = (len(ordenados) - 1) * (percentil / 100)
        f = int(k)
        c = min(f + 1, len(ordenados) - 1)
        if f == c:
            return ordenados[f]
        d0 = ordenados[f] * (c - k)
        d1 = ordenados[c] * (k - f)
        return d0 + d1
