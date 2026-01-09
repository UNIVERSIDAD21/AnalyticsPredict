"""API pública liviana para backtesting."""

from .configuracion import ConfiguracionBacktest, Mercado, ModoCutoff, ModoVentana

__all__ = [
    "ConfiguracionBacktest",
    "Mercado",
    "ModoCutoff",
    "ModoVentana",
]
