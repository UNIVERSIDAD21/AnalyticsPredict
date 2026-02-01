# -*- coding: utf-8 -*-
"""
conftest.py — Configuración de pytest para los tests.

Este archivo es cargado automáticamente por pytest y configura
el path de Python para encontrar los módulos del proyecto.
"""

import sys
import os

# Agregar el directorio backend al path de Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
