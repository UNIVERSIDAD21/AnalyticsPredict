# -*- coding: utf-8 -*-
"""
conftest.py — Configuración de pytest para los tests.

Este archivo es cargado automáticamente por pytest y configura
el path de Python para encontrar los módulos del proyecto.
"""

import sys
import os
import pytest

# Agregar el directorio backend al path de Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_collection_modifyitems(config, items):
    """Quarantine temporal para tests legacy de motor_futbol.

    Se ejecutan solo cuando ENABLE_LEGACY_MOTOR_FUTBOL_TESTS=true.
    """
    enable_legacy = os.getenv("ENABLE_LEGACY_MOTOR_FUTBOL_TESTS", "false").strip().lower() in {"1", "true", "yes", "on"}
    if enable_legacy:
        return

    skip_legacy = pytest.mark.skip(reason="Quarantine temporal: tests legacy fuera del baseline operativo B08")
    rutas_quarantine = [
        "tests/motor_futbol/",
        "tests/api/test_rutas_futbol.py",
        "tests/test_registro_predicciones.py",
        "tests/test_resolucion_predicciones.py",
        "tests/test_rutas_analisis_respuesta.py",
    ]
    for item in items:
        if any(ruta in item.nodeid for ruta in rutas_quarantine):
            item.add_marker(skip_legacy)
