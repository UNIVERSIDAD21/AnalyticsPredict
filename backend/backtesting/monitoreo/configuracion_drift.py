# -*- coding: utf-8 -*-
"""
configuracion_drift.py — Configuración de umbrales de drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class UmbralesMetrica:
    """Umbrales para una métrica específica."""

    absoluto_critical: Optional[float] = None
    absoluto_warning: Optional[float] = None
    relativo_critical: Optional[float] = None
    relativo_warning: Optional[float] = None


@dataclass
class ConfiguracionDrift:
    """Configuración completa de detección de drift."""

    ventana_actual_dias: int = 30
    ventana_baseline_dias: int = 90
    ventanas_tendencia: int = 3

    umbrales: Dict[str, UmbralesMetrica] = field(
        default_factory=lambda: {
            "ece": UmbralesMetrica(
                absoluto_critical=0.05,
                absoluto_warning=0.03,
                relativo_critical=0.50,
                relativo_warning=0.25,
            ),
            "brier": UmbralesMetrica(
                absoluto_critical=0.25,
                absoluto_warning=0.22,
                relativo_critical=0.20,
                relativo_warning=0.10,
            ),
            "sesgo": UmbralesMetrica(
                absoluto_critical=3.0,
                absoluto_warning=1.5,
            ),
            "mce": UmbralesMetrica(
                absoluto_critical=0.10,
                absoluto_warning=0.07,
            ),
        }
    )

    min_predicciones_evaluar: int = 100
    min_predicciones_baseline: int = 200

    evaluar_tendencia: bool = True
    evaluar_calibrador: bool = True
    auto_marcar_resueltas: bool = False

    @classmethod
    def desde_dict(cls, config: dict) -> "ConfiguracionDrift":
        """Crea configuración desde diccionario (ej: de BD o YAML)."""
        return cls(**config)

    def umbral_para(self, metrica: str, tipo: str) -> Optional[float]:
        """Obtiene umbral específico."""
        umbral = self.umbrales.get(metrica)
        if not umbral:
            return None
        return getattr(umbral, tipo, None)


CONFIG_DRIFT_DEFAULT = ConfiguracionDrift()
