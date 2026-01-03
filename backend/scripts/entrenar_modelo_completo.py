#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entrenar_modelo_completo.py — Entrena el modelo Ridge con TODOS los equipos NBA.

Uso desde la carpeta backend:
    python entrenar_modelo_completo.py

Este script:
1. Busca todos los CSVs de equipos en el directorio actual
2. Normaliza los nombres de equipos (ej: "LA Clippers" → "los angeles clippers")
3. Entrena un modelo Ridge por cuartos
4. Guarda el modelo en datos/modelo_entrenado.npz
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

Q_KEYS = ("Q1", "Q2", "Q3", "Q4")

# ══════════════════════════════════════════════════════════════
# MAPEO DE NOMBRES DE EQUIPOS
# Los CSVs de ESPN usan nombres cortos, pero el frontend usa nombres completos
# ══════════════════════════════════════════════════════════════

MAPEO_NOMBRES = {
    # Nombres que necesitan normalización
    "la clippers": "los angeles clippers",
    "la lakers": "los angeles lakers",
    # Alias adicionales por si acaso
    "lac": "los angeles clippers",
    "lal": "los angeles lakers",
}


def normalize_name(nombre: str) -> str:
    """
    Normaliza el nombre de un equipo a minúsculas sin espacios extra.
    También aplica mapeo de nombres alternativos.
    """
    nombre = " ".join((nombre or "").strip().lower().replace("_", " ").split())
    # Aplicar mapeo si existe
    return MAPEO_NOMBRES.get(nombre, nombre)


def parse_location_value(valor) -> int:
    """Convierte el valor de ubicación a 1 (local) o 0 (visitante)."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return 1
    texto = str(valor).strip().upper()
    if texto in ("HOME", "H", "LOCAL"):
        return 1
    if texto in ("AWAY", "A", "VISITOR", "VISITANTE") or texto.startswith("@"):
        return 0
    if texto.startswith("VS"):
        return 1
    return 1


def build_design_matrix(
    team_names: Sequence[str],
    opp_names: Sequence[str],
    is_home: Sequence[int],
    entity_to_idx: Dict[str, int],
) -> np.ndarray:
    """Construye la matriz de diseño para regresión Ridge."""
    n = len(team_names)
    k = len(entity_to_idx)
    X = np.zeros((n, 1 + k + k + 1), dtype=float)
    X[:, 0] = 1.0
    for i, (team, opp, home) in enumerate(zip(team_names, opp_names, is_home)):
        ti = entity_to_idx[normalize_name(team)]
        oi = entity_to_idx[normalize_name(opp)]
        X[i, 1 + ti] = 1.0
        X[i, 1 + k + oi] = 1.0
        X[i, -1] = float(home)
    return X


def fit_ridge(X: np.ndarray, Y: np.ndarray, alpha: float) -> Tuple[np.ndarray, np.ndarray]:
    """Ajusta regresión Ridge y retorna pesos y desviación estándar."""
    p = X.shape[1]
    I = np.eye(p, dtype=float)
    I[0, 0] = 0.0
    A = X.T @ X + alpha * I
    B = X.T @ Y
    W = np.linalg.solve(A, B)
    resid = Y - X @ W
    std = np.sqrt(np.mean(resid**2, axis=0) + 1e-9)
    return W, std


def cargar_datos(csv_paths: Sequence[Path], incluir_post: bool = False) -> pd.DataFrame:
    """Carga y procesa todos los CSVs de partidos."""
    frames: List[pd.DataFrame] = []
    
    for path in csv_paths:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"  ⚠️  Error leyendo {path.name}: {e}")
            continue
            
        # Filtrar por tipo de temporada
        if "season_type" in df.columns:
            df = df[df["season_type"].fillna("").str.upper() != "PRE"].copy()
            if not incluir_post:
                df = df[df["season_type"].fillna("").str.upper() != "POST"].copy()
        
        # Filtrar solo partidos válidos
        if "valid_linescore" in df.columns:
            df = df[df["valid_linescore"] == True].copy()

        # Eliminar filas con datos faltantes
        columnas_requeridas = ["team_q1", "team_q2", "team_q3", "team_q4", 
                               "opp_q1", "opp_q2", "opp_q3", "opp_q4"]
        df = df.dropna(subset=columnas_requeridas)
        df = df[df["opponent"].notna() & (df["opponent"].astype(str) != "")]

        if len(df) == 0:
            continue

        frames.append(
            pd.DataFrame({
                "team": df["team"].astype(str),
                "opp": df["opponent"].astype(str),
                "is_home": df.get("location", "HOME").apply(parse_location_value),
                "team_q1": pd.to_numeric(df["team_q1"], errors="coerce"),
                "team_q2": pd.to_numeric(df["team_q2"], errors="coerce"),
                "team_q3": pd.to_numeric(df["team_q3"], errors="coerce"),
                "team_q4": pd.to_numeric(df["team_q4"], errors="coerce"),
                "opp_q1": pd.to_numeric(df["opp_q1"], errors="coerce"),
                "opp_q2": pd.to_numeric(df["opp_q2"], errors="coerce"),
                "opp_q3": pd.to_numeric(df["opp_q3"], errors="coerce"),
                "opp_q4": pd.to_numeric(df["opp_q4"], errors="coerce"),
            })
        )
        print(f"  ✅ {path.name}: {len(df)} partidos")

    if not frames:
        raise ValueError("No se encontraron datos válidos en los CSVs")
        
    data = pd.concat(frames, ignore_index=True)
    return data.dropna()


def main() -> None:
    print("=" * 60)
    print("🏀 ENTRENAMIENTO DE MODELO NBA")
    print("=" * 60)
    print()
    
    # Buscar CSVs de equipos (excluir equipos.csv que es el catálogo)
    csv_dir = Path(".")
    csv_paths = [p for p in sorted(csv_dir.glob("*.csv")) 
                 if p.is_file() and p.name != "equipos.csv"]
    
    if not csv_paths:
        print("❌ No se encontraron CSVs de partidos en el directorio actual.")
        print("   Asegúrate de estar en la carpeta backend y que existan los CSVs.")
        return
    
    print(f"📁 Encontrados {len(csv_paths)} archivos CSV de partidos:")
    print()
    
    # Cargar datos
    print("📥 Cargando datos...")
    data = cargar_datos(csv_paths)
    print()
    print(f"📊 Total de partidos válidos: {len(data)}")
    
    # Obtener lista de equipos únicos (con nombres normalizados)
    equipos_team = set(data["team"].map(normalize_name))
    equipos_opp = set(data["opp"].map(normalize_name))
    entities = sorted(equipos_team | equipos_opp)
    entity_to_idx = {name: i for i, name in enumerate(entities)}
    
    print(f"🏀 Equipos en el modelo: {len(entities)}")
    print()
    
    # Mostrar equipos
    print("📋 Lista de equipos (nombres normalizados):")
    for i, equipo in enumerate(entities, 1):
        print(f"   {i:2d}. {equipo}")
    print()
    
    # Verificar que "los angeles clippers" está en la lista
    if "los angeles clippers" in entities:
        print("✅ 'los angeles clippers' está correctamente incluido")
    else:
        print("⚠️  ADVERTENCIA: 'los angeles clippers' NO está en el modelo")
        print("   Equipos similares encontrados:")
        for e in entities:
            if "clip" in e or "angeles" in e:
                print(f"      - {e}")
    print()
    
    # Construir matriz de diseño
    print("🔧 Construyendo matriz de diseño...")
    X = build_design_matrix(
        team_names=data["team"].tolist(),
        opp_names=data["opp"].tolist(),
        is_home=data["is_home"].astype(int).tolist(),
        entity_to_idx=entity_to_idx,
    )
    
    y_team = data[["team_q1", "team_q2", "team_q3", "team_q4"]].to_numpy(dtype=float)
    y_opp = data[["opp_q1", "opp_q2", "opp_q3", "opp_q4"]].to_numpy(dtype=float)
    
    # Entrenar modelo
    print("🎯 Entrenando modelo Ridge (alpha=5.0)...")
    alpha = 5.0
    w_team, std_team = fit_ridge(X, y_team, alpha)
    w_opp, std_opp = fit_ridge(X, y_opp, alpha)
    
    # Evaluar en todo el dataset
    pred_team = X @ w_team
    pred_opp = X @ w_opp
    mae_team = np.mean(np.abs(y_team - pred_team), axis=0)
    mae_opp = np.mean(np.abs(y_opp - pred_opp), axis=0)
    
    print()
    print("📈 Métricas MAE por cuarto (equipo):", 
          ", ".join(f"{q}: {m:.2f}" for q, m in zip(Q_KEYS, mae_team)))
    print("📈 Métricas MAE por cuarto (rival):", 
          ", ".join(f"{q}: {m:.2f}" for q, m in zip(Q_KEYS, mae_opp)))
    
    # Guardar modelo
    output_path = Path("datos/modelo_entrenado.npz")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    np.savez_compressed(
        output_path,
        alpha=np.array([float(alpha)], dtype=float),
        entity_json=np.array([json.dumps(entity_to_idx, ensure_ascii=False)], dtype=object),
        w_team=w_team,
        w_opp=w_opp,
        std_team=std_team,
        std_opp=std_opp,
    )
    
    print()
    print("=" * 60)
    print("✅ MODELO ENTRENADO EXITOSAMENTE")
    print("=" * 60)
    print(f"   📁 Guardado en: {output_path}")
    print(f"   🏀 Equipos: {len(entities)}")
    print(f"   📊 Partidos: {len(data)}")
    print("=" * 60)


if __name__ == "__main__":
    main()