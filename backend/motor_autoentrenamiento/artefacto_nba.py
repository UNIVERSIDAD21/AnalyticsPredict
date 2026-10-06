"""Artefacto NBA de serving: lectura en startup y escritura solo por entrenamiento explícito."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


FORMATO = 1
FEATURE_SET_VERSION = "nba_ridge_cuartos_v1"


def ruta_artefacto() -> Path:
    configurada = os.getenv("ANALYTICSPREDICT_MODELO_NBA_ACTIVO")
    return Path(configurada).expanduser() if configurada else (
        Path.home() / ".local/share/analyticspredict/modelo_nba_activo.npz"
    )


def guardar_artefacto(datos: dict[str, Any], ruta: Path | None = None) -> Path:
    """Publica un snapshot atómico; nunca deja un archivo parcial como activo."""
    destino = ruta or ruta_artefacto()
    metricas = datos.get("metricas") or {}
    modelo_id = datos.get("modelo_version_id")
    if not isinstance(modelo_id, int) or modelo_id <= 0:
        raise ValueError("El artefacto requiere modelo_version_id persistido")
    if not metricas.get("hash_datos"):
        raise ValueError("El artefacto requiere hash del dataset")
    if not metricas.get("modelo_version") or not metricas.get("fecha_entrenamiento"):
        raise ValueError("El artefacto requiere versión y timestamp registrados en BD")
    metadatos = {
        "formato": FORMATO,
        "modelo_version_id": modelo_id,
        "modelo_version": metricas["modelo_version"],
        "feature_set_version": FEATURE_SET_VERSION,
        "dataset_hash": metricas["hash_datos"],
        "fit_start_date": metricas.get("fecha_min_entrenamiento"),
        "fit_end_date": metricas.get("fecha_max_entrenamiento"),
        "fit_started_at": metricas.get("fit_started_at"),
        "fit_completed_at": metricas.get("fit_completed_at"),
        "training_data_latest_game_date": metricas.get("training_data_latest_game_date"),
        "training_outcomes_available_at": None,  # Fecha de juego no prueba disponibilidad.
        "hiperparametros": {"alpha": float(datos["alpha"])},
        "metricas_entrenamiento": metricas,
        "metricas_validacion": None,
        "fecha_entrenamiento": metricas.get("fecha_entrenamiento"),
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(prefix=".modelo_nba_", suffix=".npz", dir=destino.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as archivo:
            np.savez_compressed(
                archivo,
                metadata=np.array(json.dumps(metadatos, sort_keys=True, default=str)),
                entity_json=np.array(json.dumps(datos["entidad_a_indice"], sort_keys=True)),
                w_team=np.asarray(datos["pesos_equipo"]),
                w_opp=np.asarray(datos["pesos_rival"]),
                std_team=np.asarray(datos["desviacion_equipo"]),
                std_opp=np.asarray(datos["desviacion_rival"]),
            )
        os.replace(temporal, destino)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)
    return destino


def cargar_artefacto(ruta: Path | None = None) -> dict[str, Any] | None:
    """Carga un artefacto versionado sin pickle ni acceso a base de datos."""
    origen = ruta or ruta_artefacto()
    if not origen.is_file():
        return None
    with np.load(origen, allow_pickle=False) as archivo:
        metadatos = json.loads(str(archivo["metadata"].item()))
        entidades = json.loads(str(archivo["entity_json"].item()))
        pesos_equipo = archivo["w_team"].copy()
        pesos_rival = archivo["w_opp"].copy()
        desviacion_equipo = archivo["std_team"].copy()
        desviacion_rival = archivo["std_opp"].copy()
    if metadatos.get("formato") != FORMATO or metadatos.get("feature_set_version") != FEATURE_SET_VERSION:
        raise ValueError("Artefacto NBA con formato o feature set incompatible")
    modelo_id = metadatos.get("modelo_version_id")
    if (not isinstance(modelo_id, int) or modelo_id <= 0
            or not metadatos.get("modelo_version") or not metadatos.get("dataset_hash")
            or not metadatos.get("fecha_entrenamiento")):
        raise ValueError("Artefacto NBA sin identidad o snapshot de datos")
    cantidad = len(entidades)
    forma_esperada = (1 + 2 * cantidad + 1, 4)
    if pesos_equipo.shape != forma_esperada or pesos_rival.shape != forma_esperada:
        raise ValueError("Artefacto NBA con matriz de pesos incompatible")
    if desviacion_equipo.shape != (4,) or desviacion_rival.shape != (4,):
        raise ValueError("Artefacto NBA con desviaciones incompatibles")
    if any(not np.isfinite(matriz).all() for matriz in (
        pesos_equipo, pesos_rival, desviacion_equipo, desviacion_rival
    )):
        raise ValueError("Artefacto NBA con coeficientes no finitos")
    return {
        "alpha": float(metadatos["hiperparametros"]["alpha"]),
        "entidad_a_indice": entidades,
        "pesos_equipo": pesos_equipo,
        "pesos_rival": pesos_rival,
        "desviacion_equipo": desviacion_equipo,
        "desviacion_rival": desviacion_rival,
        "metricas": metadatos["metricas_entrenamiento"],
        "modelo_version_id": modelo_id,
        "fecha_entrenamiento": metadatos["fecha_entrenamiento"],
    }
