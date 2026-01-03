#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crea un modelo mínimo para pruebas."""

import json
import numpy as np

# Equipos de prueba
equipos = [
    "los angeles lakers",
    "golden state warriors",
    "boston celtics",
    "miami heat",
    "denver nuggets",
    "phoenix suns",
    "milwaukee bucks",
    "philadelphia 76ers",
]

# Crear mapeo
entidad_a_indice = {equipo: i for i, equipo in enumerate(equipos)}

# Cantidad de features: 1 (intercepto) + N (equipos) + N (rivales) + 1 (local)
cantidad_equipos = len(equipos)
caracteristicas = 1 + cantidad_equipos + cantidad_equipos + 1

# Pesos aleatorios pero razonables (media ~28 pts por cuarto)
np.random.seed(42)
pesos_equipo = np.zeros((caracteristicas, 4))
pesos_equipo[0, :] = 28.0
pesos_equipo[1:cantidad_equipos + 1, :] = np.random.randn(cantidad_equipos, 4) * 1.5
pesos_equipo[cantidad_equipos + 1:-1, :] = np.random.randn(cantidad_equipos, 4) * 1.0
pesos_equipo[-1, :] = 1.5

pesos_rival = np.zeros((caracteristicas, 4))
pesos_rival[0, :] = 27.0
pesos_rival[1:cantidad_equipos + 1, :] = np.random.randn(cantidad_equipos, 4) * 1.0
pesos_rival[cantidad_equipos + 1:-1, :] = np.random.randn(cantidad_equipos, 4) * 1.5
pesos_rival[-1, :] = -1.5

# Desviaciones estándar típicas
desviacion_equipo = np.array([5.5, 5.8, 6.0, 6.2])
desviacion_rival = np.array([5.6, 5.9, 6.1, 6.3])

# Guardar
np.savez_compressed(
    "../backend/datos/modelo_entrenado.npz",
    alpha=np.array([5.0]),
    entity_json=np.array([json.dumps(entidad_a_indice)]),
    w_team=pesos_equipo,
    w_opp=pesos_rival,
    std_team=desviacion_equipo,
    std_opp=desviacion_rival,
)

print("✅ Modelo de prueba creado en: backend/datos/modelo_entrenado.npz")
print(f"   Equipos incluidos: {len(equipos)}")
