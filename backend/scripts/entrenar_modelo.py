#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entrenar_modelo.py — Entrena el modelo Ridge para puntos por cuarto.

Uso:
    python entrenar_modelo.py --csv-dir ./ --out ../backend/datos/modelo_entrenado.npz
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

Q_KEYS = ("Q1", "Q2", "Q3", "Q4")


def normalize_name(nombre: str) -> str:
    return " ".join((nombre or "").strip().lower().replace("_", " ").split())


def parse_location_value(valor: str | None) -> int:
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
    p = X.shape[1]
    I = np.eye(p, dtype=float)
    I[0, 0] = 0.0
    A = X.T @ X + alpha * I
    B = X.T @ Y
    W = np.linalg.solve(A, B)
    resid = Y - X @ W
    std = np.sqrt(np.mean(resid**2, axis=0) + 1e-9)
    return W, std


def save_model(path: Path, alpha: float, entity_to_idx: Dict[str, int], w_team: np.ndarray, w_opp: np.ndarray,
               std_team: np.ndarray, std_opp: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        alpha=np.array([float(alpha)], dtype=float),
        entity_json=np.array([json.dumps(entity_to_idx, ensure_ascii=False)], dtype=object),
        w_team=w_team,
        w_opp=w_opp,
        std_team=std_team,
        std_opp=std_opp,
    )


def cargar_datos(csv_paths: Sequence[Path], incluir_post: bool) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for path in csv_paths:
        df = pd.read_csv(path)
        if "season_type" in df.columns:
            df = df[df["season_type"].fillna("").str.upper() != "PRE"].copy()
            if not incluir_post:
                df = df[df["season_type"].fillna("").str.upper() != "POST"].copy()
        if "valid_linescore" in df.columns:
            df = df[df["valid_linescore"] == True].copy()  # noqa: E712

        df = df.dropna(subset=["team_q1", "team_q2", "team_q3", "team_q4", "opp_q1", "opp_q2", "opp_q3", "opp_q4"])
        df = df[df["opponent"].notna() & (df["opponent"].astype(str) != "")]

        frames.append(
            pd.DataFrame(
                {
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
                }
            )
        )

    data = pd.concat(frames, ignore_index=True)
    return data.dropna()


def dividir_indices(n: int, test_size: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(n)
    corte = int(n * (1 - test_size))
    return indices[:corte], indices[corte:]


def evaluar_mae(y_real: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    return np.mean(np.abs(y_real - y_pred), axis=0)


def evaluar_calibracion(total_real: np.ndarray, total_pred: np.ndarray, std_total: np.ndarray) -> float:
    z = 0.8416
    lower = total_pred - z * std_total
    upper = total_pred + z * std_total
    return float(np.mean((total_real >= lower) & (total_real <= upper)))


def imprimir_resumen(mae_team: np.ndarray, mae_opp: np.ndarray, mae_total: np.ndarray,
                     mae_game_total: float, calibracion_q: List[float], calibracion_total: float) -> None:
    print("📊 Métricas MAE por cuarto (equipo):", ", ".join(f"{q}: {m:.2f}" for q, m in zip(Q_KEYS, mae_team)))
    print("📊 Métricas MAE por cuarto (rival):", ", ".join(f"{q}: {m:.2f}" for q, m in zip(Q_KEYS, mae_opp)))
    print("📊 Métricas MAE por cuarto (total):", ", ".join(f"{q}: {m:.2f}" for q, m in zip(Q_KEYS, mae_total)))
    print(f"📊 MAE juego completo (total): {mae_game_total:.2f}")
    print("🎯 Calibración (60% esperado) por cuarto:",
          ", ".join(f"{q}: {c*100:.1f}%" for q, c in zip(Q_KEYS, calibracion_q)))
    print(f"🎯 Calibración total (60% esperado): {calibracion_total*100:.1f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el modelo Ridge por cuartos.")
    parser.add_argument("--csv-dir", default=".", help="Directorio con CSVs (por defecto: .)")
    parser.add_argument("--out", default="../backend/datos/modelo_entrenado.npz", help="Ruta de salida .npz")
    parser.add_argument("--alpha", type=float, default=5.0, help="Parámetro alpha de Ridge")
    parser.add_argument("--test-size", type=float, default=0.2, help="Proporción para test")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para división")
    parser.add_argument("--include-post", action="store_true", help="Incluir partidos de postemporada")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    csv_paths = sorted(p for p in csv_dir.glob("*.csv") if p.is_file())
    if not csv_paths:
        raise SystemExit(f"No se encontraron CSVs en {csv_dir}")

    data = cargar_datos(csv_paths, incluir_post=args.include_post)
    entities = sorted(set(data["team"].map(normalize_name)) | set(data["opp"].map(normalize_name)))
    entity_to_idx = {name: i for i, name in enumerate(entities)}

    X = build_design_matrix(
        team_names=data["team"].tolist(),
        opp_names=data["opp"].tolist(),
        is_home=data["is_home"].astype(int).tolist(),
        entity_to_idx=entity_to_idx,
    )

    y_team = data[["team_q1", "team_q2", "team_q3", "team_q4"]].to_numpy(dtype=float)
    y_opp = data[["opp_q1", "opp_q2", "opp_q3", "opp_q4"]].to_numpy(dtype=float)

    train_idx, test_idx = dividir_indices(len(data), args.test_size, args.seed)
    X_train, X_test = X[train_idx], X[test_idx]
    y_team_train, y_team_test = y_team[train_idx], y_team[test_idx]
    y_opp_train, y_opp_test = y_opp[train_idx], y_opp[test_idx]

    w_team, std_team = fit_ridge(X_train, y_team_train, args.alpha)
    w_opp, std_opp = fit_ridge(X_train, y_opp_train, args.alpha)

    pred_team = X_test @ w_team
    pred_opp = X_test @ w_opp

    mae_team = evaluar_mae(y_team_test, pred_team)
    mae_opp = evaluar_mae(y_opp_test, pred_opp)
    total_real = y_team_test + y_opp_test
    total_pred = pred_team + pred_opp
    mae_total = evaluar_mae(total_real, total_pred)
    mae_game_total = float(np.mean(np.abs(total_real.sum(axis=1) - total_pred.sum(axis=1))))

    std_total = np.sqrt(std_team**2 + std_opp**2)
    calibracion_q = [
        evaluar_calibracion(total_real[:, i], total_pred[:, i], std_total[i]) for i in range(4)
    ]
    std_total_game = float(np.sqrt(np.sum(std_total**2)))
    calibracion_total = evaluar_calibracion(
        total_real.sum(axis=1),
        total_pred.sum(axis=1),
        std_total_game,
    )

    imprimir_resumen(mae_team, mae_opp, mae_total, mae_game_total, calibracion_q, calibracion_total)

    out_path = Path(args.out)
    save_model(out_path, args.alpha, entity_to_idx, w_team, w_opp, std_team, std_opp)
    print(f"✅ Modelo guardado en {out_path}")


if __name__ == "__main__":
    main()
