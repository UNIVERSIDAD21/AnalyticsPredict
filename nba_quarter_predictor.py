#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nba_quarter_predictor.py (PRO + LIVE)

✅ train: entrenar modelo (.npz)
✅ predict: predicción pre-partido por cuartos + O/U + ganador por cuarto
✅ predict-live: incorpora marcador REAL del Q1 (ajusta Q2–Q4)
✅ predict-live2: incorpora marcador REAL del Q1 y/o Q2 (ajusta Q3–Q4)
✅ predict-live3: incorpora marcador REAL del Q1 y/o Q2 y/o Q3 (ajusta el/los cuartos restantes, típicamente Q4)

Formato de parciales (siempre desde la perspectiva de --team):
  --q1-score "28-32"  => Team=28, Opp=32 en ese cuarto
  --q2-score "18-26"
  --q3-score "28-32"

Requiere: numpy, pandas
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

Q_KEYS = ("Q1", "Q2", "Q3", "Q4")
Q_IDX = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3}


def normalize_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def fmt_pct(p: float) -> str:
    return f"{p * 100:.1f}%"


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def parse_lines(s: Optional[str]) -> Dict[str, float]:
    """ "Q1:57.5,Q2:55.5" -> {"Q1":57.5, "Q2":55.5} """
    if not s:
        return {}
    out: Dict[str, float] = {}
    parts = [p.strip() for p in s.split(",") if p.strip()]
    for p in parts:
        if ":" not in p:
            raise ValueError(f'Línea inválida "{p}". Formato esperado: Q1:57.5')
        k, v = p.split(":", 1)
        k = k.strip().upper()
        v = v.strip()
        if k not in Q_KEYS:
            raise ValueError(f'Clave inválida "{k}". Usa Q1,Q2,Q3,Q4.')
        out[k] = float(v)
    return out


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def over_probability(mean: float, std: float, line: float) -> float:
    std = max(float(std), 1e-9)
    z = (line - mean) / std
    return 1.0 - normal_cdf(z)


def win_probability(mean_team: float, std_team: float, mean_opp: float, std_opp: float) -> float:
    mu_d = float(mean_team) - float(mean_opp)
    sd_d = math.sqrt(float(std_team) ** 2 + float(std_opp) ** 2)
    sd_d = max(sd_d, 1e-9)
    return normal_cdf(mu_d / sd_d)


def ci_approx(mean: float, std: float, z: float) -> Tuple[float, float]:
    return mean - z * std, mean + z * std


# -----------------------------
# Auto-detección columnas CSV
# -----------------------------

def _find_col(df: pd.DataFrame, patterns: Sequence[str]) -> Optional[str]:
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in df.columns:
            if rx.fullmatch(str(c).strip()):
                return c
        for c in df.columns:
            if rx.search(str(c)):
                return c
    return None


def autodetect_location_col(df: pd.DataFrame) -> Optional[str]:
    return _find_col(df, [r"location", r"home_away", r"homeaway", r"venue", r"ha"])


def autodetect_opp_col(df: pd.DataFrame) -> Optional[str]:
    return _find_col(df, [r"opponent", r"opp", r"vs", r"rival"])


def autodetect_team_name_from_path(path: str) -> str:
    base = os.path.basename(path)
    base = os.path.splitext(base)[0]
    base = re.sub(r"(_fixed|_games|_data|_stats)$", "", base, flags=re.IGNORECASE)
    return normalize_name(base)


def autodetect_quarter_cols(df: pd.DataFrame, role: str) -> Optional[List[str]]:
    role = role.lower()
    patterns_by_q = {
        "Q1": [rf"(?:{role}|tm|for|pts|points)_[ ]?q1", rf"q1_[ ]?(?:{role}|tm|for|pts|points)", r"^q1$" if role == "team" else r"^opp_q1$", r"^q1_pts$"],
        "Q2": [rf"(?:{role}|tm|for|pts|points)_[ ]?q2", rf"q2_[ ]?(?:{role}|tm|for|pts|points)", r"^q2$" if role == "team" else r"^opp_q2$", r"^q2_pts$"],
        "Q3": [rf"(?:{role}|tm|for|pts|points)_[ ]?q3", rf"q3_[ ]?(?:{role}|tm|for|pts|points)", r"^q3$" if role == "team" else r"^opp_q3$", r"^q3_pts$"],
        "Q4": [rf"(?:{role}|tm|for|pts|points)_[ ]?q4", rf"q4_[ ]?(?:{role}|tm|for|pts|points)", r"^q4$" if role == "team" else r"^opp_q4$", r"^q4_pts$"],
    }
    cols: List[str] = []
    for q in Q_KEYS:
        col = _find_col(df, patterns_by_q[q])
        cols.append(col if col else "")

    if all(cols):
        return cols
    if role == "team" and all(q in df.columns for q in Q_KEYS):
        return list(Q_KEYS)

    if role == "team":
        maybe = [f"TEAM_{q}" for q in Q_KEYS]
        if all(m in df.columns for m in maybe):
            return maybe
    if role == "opp":
        maybe = [f"OPP_{q}" for q in Q_KEYS]
        if all(m in df.columns for m in maybe):
            return maybe
        maybe = [f"OPPONENT_{q}" for q in Q_KEYS]
        if all(m in df.columns for m in maybe):
            return maybe
    return None


def parse_location_value(v) -> Optional[int]:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    s = str(v).strip().upper()
    if s in ("HOME", "H", "LOCAL"):
        return 1
    if s in ("AWAY", "A", "VISITOR", "VISITANTE"):
        return 0
    if s.startswith("@"):
        return 0
    if s.startswith("VS"):
        return 1
    return None


def ensure_columns(df: pd.DataFrame, cols: Sequence[str], label: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas para {label}: {missing}\nColumnas disponibles: {list(df.columns)}")


# -----------------------------
# Modelo Ridge
# -----------------------------

@dataclass
class RidgeModel:
    alpha: float
    entity_to_idx: Dict[str, int]
    w_team: np.ndarray
    w_opp: np.ndarray
    std_team: np.ndarray
    std_opp: np.ndarray


def build_design_matrix(team_names: Sequence[str], opp_names: Sequence[str], is_home: Sequence[int], entity_to_idx: Dict[str, int]) -> np.ndarray:
    n = len(team_names)
    k = len(entity_to_idx)
    X = np.zeros((n, 1 + k + k + 1), dtype=float)
    X[:, 0] = 1.0
    for i, (t, o, h) in enumerate(zip(team_names, opp_names, is_home)):
        ti = entity_to_idx[normalize_name(t)]
        oi = entity_to_idx[normalize_name(o)]
        X[i, 1 + ti] = 1.0
        X[i, 1 + k + oi] = 1.0
        X[i, -1] = float(h)
    return X


def fit_ridge(X: np.ndarray, Y: np.ndarray, alpha: float) -> Tuple[np.ndarray, np.ndarray]:
    p = X.shape[1]
    I = np.eye(p, dtype=float)
    I[0, 0] = 0.0
    A = X.T @ X + alpha * I
    B = X.T @ Y
    W = np.linalg.solve(A, B)
    resid = Y - X @ W
    std = np.sqrt(np.mean(resid ** 2, axis=0) + 1e-9)
    return W, std


def save_model(path: str, model: RidgeModel):
    np.savez_compressed(
        path,
        alpha=np.array([float(model.alpha)], dtype=float),
        entity_json=np.array([json.dumps(model.entity_to_idx, ensure_ascii=False)], dtype=object),
        w_team=model.w_team,
        w_opp=model.w_opp,
        std_team=model.std_team,
        std_opp=model.std_opp,
    )


def load_model(path: str) -> RidgeModel:
    with np.load(path, allow_pickle=True) as z:
        alpha = float(z["alpha"][0])
        entity_to_idx = json.loads(str(z["entity_json"][0]))
        w_team = z["w_team"]
        w_opp = z["w_opp"]
        std_team = z["std_team"]
        std_opp = z["std_opp"]
    return RidgeModel(alpha=alpha, entity_to_idx=entity_to_idx, w_team=w_team, w_opp=w_opp, std_team=std_team, std_opp=std_opp)


# -----------------------------
# Dataset
# -----------------------------

@dataclass
class DatasetConfig:
    opp_col: Optional[str]
    loc_col: Optional[str]
    team_q_cols: Optional[List[str]]
    opp_q_cols: Optional[List[str]]


def parse_cols_list(s: Optional[str]) -> Optional[List[str]]:
    if not s:
        return None
    cols = [c.strip() for c in s.split(",") if c.strip()]
    if len(cols) != 4:
        raise ValueError(f"Esperaba 4 columnas separadas por coma para Q1..Q4, pero llegaron {len(cols)}: {cols}")
    return cols


def load_one_csv(path: str, cfg: DatasetConfig) -> pd.DataFrame:
    df = pd.read_csv(path)
    team_name = autodetect_team_name_from_path(path)

    opp_col = cfg.opp_col or autodetect_opp_col(df)
    loc_col = cfg.loc_col or autodetect_location_col(df)
    team_q_cols = cfg.team_q_cols or autodetect_quarter_cols(df, "team")
    opp_q_cols = cfg.opp_q_cols or autodetect_quarter_cols(df, "opp")

    if not opp_col:
        raise ValueError(f"No pude detectar columna de rival en {path}. Usa --opp-col.\nColumnas: {list(df.columns)}")
    if not team_q_cols:
        raise ValueError(f"No pude detectar Q1..Q4 del EQUIPO en {path}. Usa --team-q-cols.\nColumnas: {list(df.columns)}")
    if not opp_q_cols:
        raise ValueError(f"No pude detectar Q1..Q4 del RIVAL en {path}. Usa --opp-q-cols.\nColumnas: {list(df.columns)}")

    ensure_columns(df, [opp_col] + team_q_cols + opp_q_cols, "dataset")

    if loc_col and loc_col in df.columns:
        home_vals = df[loc_col].apply(parse_location_value)
        if home_vals.isna().any():
            home_from_opp = df[opp_col].apply(parse_location_value)
            home_vals = home_vals.fillna(home_from_opp)
        home_vals = home_vals.fillna(1).astype(int)
    else:
        home_vals = pd.Series([1] * len(df), index=df.index, dtype=int)

    out = pd.DataFrame({
        "team": [team_name] * len(df),
        "opp": df[opp_col].astype(str).map(normalize_name),
        "is_home": home_vals.astype(int),
        "team_q1": pd.to_numeric(df[team_q_cols[0]], errors="coerce"),
        "team_q2": pd.to_numeric(df[team_q_cols[1]], errors="coerce"),
        "team_q3": pd.to_numeric(df[team_q_cols[2]], errors="coerce"),
        "team_q4": pd.to_numeric(df[team_q_cols[3]], errors="coerce"),
        "opp_q1": pd.to_numeric(df[opp_q_cols[0]], errors="coerce"),
        "opp_q2": pd.to_numeric(df[opp_q_cols[1]], errors="coerce"),
        "opp_q3": pd.to_numeric(df[opp_q_cols[2]], errors="coerce"),
        "opp_q4": pd.to_numeric(df[opp_q_cols[3]], errors="coerce"),
    })

    out = out.dropna(subset=["team_q1","team_q2","team_q3","team_q4","opp_q1","opp_q2","opp_q3","opp_q4"])
    return out


def load_dataset(csv_paths: Sequence[str], cfg: DatasetConfig) -> pd.DataFrame:
    frames = [load_one_csv(p, cfg) for p in csv_paths]
    data = pd.concat(frames, ignore_index=True)
    data = data[data["opp"].notna() & (data["opp"] != "") & (data["opp"] != "nan")].copy()
    return data


def train_model(csv_paths: Sequence[str], model_out: str, alpha: float, cfg: DatasetConfig) -> RidgeModel:
    data = load_dataset(csv_paths, cfg)
    entities = sorted(set(data["team"].map(normalize_name).tolist()) | set(data["opp"].map(normalize_name).tolist()))
    entity_to_idx = {name: i for i, name in enumerate(entities)}

    X = build_design_matrix(
        team_names=data["team"].tolist(),
        opp_names=data["opp"].tolist(),
        is_home=data["is_home"].astype(int).tolist(),
        entity_to_idx=entity_to_idx,
    )

    Y_team = data[["team_q1","team_q2","team_q3","team_q4"]].to_numpy(dtype=float)
    Y_opp  = data[["opp_q1","opp_q2","opp_q3","opp_q4"]].to_numpy(dtype=float)

    w_team, std_team = fit_ridge(X, Y_team, alpha=alpha)
    w_opp,  std_opp  = fit_ridge(X, Y_opp,  alpha=alpha)

    model = RidgeModel(alpha=alpha, entity_to_idx=entity_to_idx, w_team=w_team, w_opp=w_opp, std_team=std_team, std_opp=std_opp)
    save_model(model_out, model)
    return model


def predict_quarters(model: RidgeModel, team: str, opp: str, location: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    team_n = normalize_name(team)
    opp_n = normalize_name(opp)

    if team_n not in model.entity_to_idx:
        raise ValueError(f'Equipo "{team}" no está en el modelo.')
    if opp_n not in model.entity_to_idx:
        raise ValueError(f'Rival "{opp}" no está en el modelo.')

    loc = location.strip().upper()
    if loc not in ("HOME", "AWAY"):
        raise ValueError('--location debe ser HOME o AWAY (desde la perspectiva de --team).')
    is_home = 1 if loc == "HOME" else 0

    X = build_design_matrix([team_n], [opp_n], [is_home], model.entity_to_idx)
    mu_team = (X @ model.w_team).reshape(-1)
    mu_opp  = (X @ model.w_opp).reshape(-1)
    std_team = model.std_team.reshape(-1)
    std_opp  = model.std_opp.reshape(-1)
    return mu_team, std_team, mu_opp, std_opp


def parse_score(s: Optional[str]) -> Optional[Tuple[float, float]]:
    if not s:
        return None
    s = s.strip()
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[-:]\s*(\d+(?:\.\d+)?)\s*", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.fullmatch(r"\s*team\s*[:=]\s*(\d+(?:\.\d+)?)\s*,\s*opp\s*[:=]\s*(\d+(?:\.\d+)?)\s*", s, flags=re.IGNORECASE)
    if m:
        return float(m.group(1)), float(m.group(2))
    raise ValueError('Formato inválido. Usa "28-32" o "team=28,opp=32".')


def apply_live_adjustment(mu_team: np.ndarray, mu_opp: np.ndarray,
                          q1: Optional[Tuple[float, float]],
                          q2: Optional[Tuple[float, float]],
                          q3: Optional[Tuple[float, float]],
                          live_weight: float,
                          w_q1: float = 0.15,
                          w_q2: float = 0.35,
                          w_q3: float = 0.50) -> Tuple[np.ndarray, np.ndarray, Dict[str, float], Dict[str, Tuple[float, float]]]:
    w = clamp01(live_weight)

    mu_team_adj = mu_team.copy()
    mu_opp_adj = mu_opp.copy()

    actuals: Dict[str, Tuple[float, float]] = {}
    meta: Dict[str, float] = {"live_weight": w, "w_q1": float(w_q1), "w_q2": float(w_q2), "w_q3": float(w_q3)}

    provided: List[Tuple[str, Tuple[float, float], float]] = []
    if q1 is not None:
        provided.append(("Q1", (float(q1[0]), float(q1[1])), float(w_q1)))
    if q2 is not None:
        provided.append(("Q2", (float(q2[0]), float(q2[1])), float(w_q2)))
    if q3 is not None:
        provided.append(("Q3", (float(q3[0]), float(q3[1])), float(w_q3)))

    if not provided:
        raise ValueError("Debes pasar al menos uno: --q1-score, --q2-score o --q3-score")

    resid_team = {}
    resid_opp = {}

    for q, (t_real, o_real), _wq in provided:
        idx = Q_IDX[q]
        actuals[q] = (t_real, o_real)
        resid_team[q] = t_real - float(mu_team[idx])
        resid_opp[q] = o_real - float(mu_opp[idx])
        mu_team_adj[idx] = t_real
        mu_opp_adj[idx] = o_real
        meta[f"resid_team_{q.lower()}"] = resid_team[q]
        meta[f"resid_opp_{q.lower()}"] = resid_opp[q]

    total_w = sum(max(0.0, _wq) for _, _, _wq in provided)
    if total_w <= 0:
        total_w = 1.0

    resid_team_comb = 0.0
    resid_opp_comb = 0.0
    for q, _score, _wq in provided:
        wnorm = max(0.0, _wq) / total_w
        resid_team_comb += wnorm * resid_team[q]
        resid_opp_comb += wnorm * resid_opp[q]

    meta["resid_team_comb"] = resid_team_comb
    meta["resid_opp_comb"] = resid_opp_comb

    for q in Q_KEYS:
        if q in actuals:
            continue
        idx = Q_IDX[q]
        mu_team_adj[idx] = float(mu_team_adj[idx]) + w * resid_team_comb
        mu_opp_adj[idx] = float(mu_opp_adj[idx]) + w * resid_opp_comb

    return mu_team_adj, mu_opp_adj, meta, actuals


@dataclass
class BetCandidate:
    quarter: str
    market: str
    side: str
    line: float
    prob: float
    mean: float
    std: float
    zdist: float

    def label(self, team: str, opp: str) -> str:
        if self.market == "TOTAL":
            return f"{self.side} {self.line:.2f} (TOTAL)"
        if self.market == "TEAM":
            return f"{self.side} {self.line:.2f} ({team})"
        return f"{self.side} {self.line:.2f} ({opp})"


def candidates_for_quarter(q: str,
                          mean_total: float, std_total: float, total_line: Optional[float],
                          mean_team: float, std_team: float, team_line: Optional[float],
                          mean_opp: float, std_opp: float, opp_line: Optional[float]) -> List[BetCandidate]:
    cands: List[BetCandidate] = []

    def add(market: str, mean: float, std: float, line: float):
        p_over = over_probability(mean, std, line)
        p_under = 1.0 - p_over
        zdist = abs(mean - line) / max(std, 1e-9)
        cands.append(BetCandidate(q, market, "OVER", float(line), p_over, float(mean), float(std), float(zdist)))
        cands.append(BetCandidate(q, market, "UNDER", float(line), p_under, float(mean), float(std), float(zdist)))

    if total_line is not None:
        add("TOTAL", mean_total, std_total, total_line)
    if team_line is not None:
        add("TEAM", mean_team, std_team, team_line)
    if opp_line is not None:
        add("OPP", mean_opp, std_opp, opp_line)

    return cands


def pick_best_bet(cands: List[BetCandidate]) -> Optional[BetCandidate]:
    if not cands:
        return None
    market_pref = {"TOTAL": 2, "TEAM": 1, "OPP": 0}
    return sorted(cands, key=lambda c: (c.prob, c.zdist, market_pref.get(c.market, 0)), reverse=True)[0]


def print_intro():
    print("=== Predicción por cuartos (Q1–Q4) ===\n")
    print("Interpretación rápida:")
    print("- mean = 'media' o 'valor esperado' (promedio que espera el modelo).")
    print("- std  = 'desviación estándar' (incertidumbre / variación típica).")
    print("  Regla rápida: ~68% cae cerca de mean ± 1*std, y ~95% cerca de mean ± 1.96*std.\n")


def print_quarter_prediction(q: str, team: str, opp: str,
                            mean_team: float, std_team: float,
                            mean_opp: float, std_opp: float,
                            mean_total: float, std_total: float,
                            note: Optional[str] = None):
    lo68_t, hi68_t = ci_approx(mean_team, std_team, 1.0)
    lo95_t, hi95_t = ci_approx(mean_team, std_team, 1.96)
    lo68_o, hi68_o = ci_approx(mean_opp, std_opp, 1.0)
    lo95_o, hi95_o = ci_approx(mean_opp, std_opp, 1.96)
    lo68_tot, hi68_tot = ci_approx(mean_total, std_total, 1.0)
    lo95_tot, hi95_tot = ci_approx(mean_total, std_total, 1.96)

    p_team_win = win_probability(mean_team, std_team, mean_opp, std_opp)
    winner = team if p_team_win >= 0.5 else opp
    p_winner = p_team_win if p_team_win >= 0.5 else (1.0 - p_team_win)

    print(f"{q}:{' ' + note if note else ''}")
    print(f"  {team:>24} -> mean={mean_team:.2f}, std={std_team:.2f} | ~68% [{lo68_t:.2f}, {hi68_t:.2f}] | ~95% [{lo95_t:.2f}, {hi95_t:.2f}]")
    print(f"  {opp:>24} -> mean={mean_opp:.2f}, std={std_opp:.2f} | ~68% [{lo68_o:.2f}, {hi68_o:.2f}] | ~95% [{lo95_o:.2f}, {hi95_o:.2f}]")
    print(f"  {'TOTAL':>24} -> mean={mean_total:.2f}, std={std_total:.2f} | ~68% [{lo68_tot:.2f}, {hi68_tot:.2f}] | ~95% [{lo95_tot:.2f}, {hi95_tot:.2f}]")
    print(f"  🏁 Ganador probable del cuarto: {winner} = {fmt_pct(p_winner)}\n")


def print_lines_and_best_bet(q: str, team: str, opp: str,
                            mean_team: float, std_team: float,
                            mean_opp: float, std_opp: float,
                            mean_total: float, std_total: float,
                            total_lines: Dict[str, float], team_lines: Dict[str, float], opp_lines: Dict[str, float],
                            min_prob: float) -> Optional[BetCandidate]:

    tl = total_lines.get(q)
    tml = team_lines.get(q)
    ol = opp_lines.get(q)

    if tl is not None:
        p_over = over_probability(mean_total, std_total, tl)
        print(f"  Línea TOTAL {tl:.2f} -> Over={fmt_pct(p_over)} | Under={fmt_pct(1 - p_over)}")
    if tml is not None:
        p_over = over_probability(mean_team, std_team, tml)
        print(f"  Línea {team} {tml:.2f} -> Over={fmt_pct(p_over)} | Under={fmt_pct(1 - p_over)}")
    if ol is not None:
        p_over = over_probability(mean_opp, std_opp, ol)
        print(f"  Línea {opp} {ol:.2f} -> Over={fmt_pct(p_over)} | Under={fmt_pct(1 - p_over)}")

    cands = candidates_for_quarter(q, mean_total, std_total, tl, mean_team, std_team, tml, mean_opp, std_opp, ol)
    best = pick_best_bet(cands)
    if best is None:
        print("  (Sin líneas para recomendar apuesta en este cuarto.)\n")
        return None

    warn = ""
    if best.prob < min_prob:
        warn = f" ⚠️ (prob < {fmt_pct(min_prob)}; es la mejor ENTRE tus opciones, pero no es 'fuerte')."

    print(f"  ✅ Mejor apuesta {q}: {best.label(team, opp)} = {fmt_pct(best.prob)}{warn}")
    print(f"     Motivo: mean={best.mean:.2f} vs línea={best.line:.2f} | separación≈{best.zdist:.2f}σ\n")
    return best


def run_prediction(team: str, opp: str, location: str,
                   mu_team: np.ndarray, std_team: np.ndarray,
                   mu_opp: np.ndarray, std_opp: np.ndarray,
                   total_lines: Dict[str, float], team_lines: Dict[str, float], opp_lines: Dict[str, float],
                   min_prob: float,
                   actuals: Optional[Dict[str, Tuple[float, float]]] = None,
                   live_meta: Optional[Dict[str, float]] = None):

    mu_total = mu_team + mu_opp
    std_total = np.sqrt(std_team**2 + std_opp**2)

    print_intro()
    print("Partido / Contexto:")
    print(f"- Team (tu equipo): {team}")
    print(f"- Rival: {opp}")
    print(f"- Location (desde Team): {location.upper()}")
    if live_meta is not None:
        print(f"- LIVE: live_weight={live_meta.get('live_weight', 0.0):.2f}")
        if "resid_team_comb" in live_meta:
            print(f"        resid COMB={live_meta['resid_team_comb']:+.2f} (TEAM) | {live_meta['resid_opp_comb']:+.2f} (OPP)")
    print("")

    bests: List[BetCandidate] = []

    for i, q in enumerate(Q_KEYS):
        if actuals and q in actuals:
            t_real, o_real = actuals[q]
            tot_real = t_real + o_real
            print(f"{q}: (REAL)")
            print(f"  {team:>24} -> REAL={t_real:.0f}")
            print(f"  {opp:>24} -> REAL={o_real:.0f}")
            print(f"  {'TOTAL':>24} -> REAL={tot_real:.0f}\n")
            continue

        note = "(ajustado por parciales)" if actuals else None

        mean_t, sd_t = float(mu_team[i]), float(std_team[i])
        mean_o, sd_o = float(mu_opp[i]), float(std_opp[i])
        mean_tot, sd_tot = float(mu_total[i]), float(std_total[i])

        print_quarter_prediction(q, team, opp, mean_t, sd_t, mean_o, sd_o, mean_tot, sd_tot, note=note)
        best = print_lines_and_best_bet(q, team, opp, mean_t, sd_t, mean_o, sd_o, mean_tot, sd_tot,
                                        total_lines, team_lines, opp_lines, min_prob)
        if best:
            bests.append(best)

    if bests:
        overall = sorted(bests, key=lambda b: (b.prob, b.zdist), reverse=True)[0]
        print("=== Resumen de recomendaciones ===")
        for b in bests:
            print(f"- {b.quarter}: {b.label(team, opp)} -> {fmt_pct(b.prob)} (separación≈{b.zdist:.2f}σ)")
        print(f"\n🏆 Mejor apuesta GLOBAL (entre tus líneas): {overall.quarter} -> {overall.label(team, opp)} = {fmt_pct(overall.prob)}\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nba_quarter_predictor.py",
        description="Entrena/predice puntos por cuarto con O/U + LIVE (Q1/Q2/Q3 reales).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train", help="Entrenar modelo")
    t.add_argument("--csv", nargs="+", required=True)
    t.add_argument("--model", required=True)
    t.add_argument("--alpha", type=float, default=5.0)
    t.add_argument("--opp-col", default=None)
    t.add_argument("--loc-col", default=None)
    t.add_argument("--team-q-cols", default=None)
    t.add_argument("--opp-q-cols", default=None)

    pr = sub.add_parser("predict", help="Predecir (pre-partido)")
    pr.add_argument("--model", required=True)
    pr.add_argument("--team", required=True)
    pr.add_argument("--opp", required=True)
    pr.add_argument("--location", choices=["HOME", "AWAY"], required=True)
    pr.add_argument("--total-lines", default=None)
    pr.add_argument("--team-lines", default=None)
    pr.add_argument("--opp-lines", default=None)
    pr.add_argument("--min-prob", type=float, default=0.55)

    pl = sub.add_parser("predict-live", help="LIVE con Q1 real (ajusta Q2–Q4)")
    pl.add_argument("--model", required=True)
    pl.add_argument("--team", required=True)
    pl.add_argument("--opp", required=True)
    pl.add_argument("--location", choices=["HOME", "AWAY"], required=True)
    pl.add_argument("--q1-score", required=True)
    pl.add_argument("--live-weight", type=float, default=0.30)
    pl.add_argument("--total-lines", default=None)
    pl.add_argument("--team-lines", default=None)
    pl.add_argument("--opp-lines", default=None)
    pl.add_argument("--min-prob", type=float, default=0.55)

    pl2 = sub.add_parser("predict-live2", help="LIVE con Q1 y/o Q2 real (ajusta Q3–Q4)")
    pl2.add_argument("--model", required=True)
    pl2.add_argument("--team", required=True)
    pl2.add_argument("--opp", required=True)
    pl2.add_argument("--location", choices=["HOME", "AWAY"], required=True)
    pl2.add_argument("--q1-score", default=None)
    pl2.add_argument("--q2-score", default=None)
    pl2.add_argument("--live-weight", type=float, default=0.30)
    pl2.add_argument("--total-lines", default=None)
    pl2.add_argument("--team-lines", default=None)
    pl2.add_argument("--opp-lines", default=None)
    pl2.add_argument("--min-prob", type=float, default=0.55)

    pl3 = sub.add_parser("predict-live3", help="LIVE con Q1 y/o Q2 y/o Q3 real (ajusta los cuartos restantes)")
    pl3.add_argument("--model", required=True)
    pl3.add_argument("--team", required=True)
    pl3.add_argument("--opp", required=True)
    pl3.add_argument("--location", choices=["HOME", "AWAY"], required=True)
    pl3.add_argument("--q1-score", default=None)
    pl3.add_argument("--q2-score", default=None)
    pl3.add_argument("--q3-score", default=None)
    pl3.add_argument("--live-weight", type=float, default=0.30)
    pl3.add_argument("--w-q1", type=float, default=0.15)
    pl3.add_argument("--w-q2", type=float, default=0.35)
    pl3.add_argument("--w-q3", type=float, default=0.50)
    pl3.add_argument("--total-lines", default=None)
    pl3.add_argument("--team-lines", default=None)
    pl3.add_argument("--opp-lines", default=None)
    pl3.add_argument("--min-prob", type=float, default=0.55)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "train":
        cfg = DatasetConfig(
            opp_col=args.opp_col,
            loc_col=args.loc_col,
            team_q_cols=parse_cols_list(args.team_q_cols),
            opp_q_cols=parse_cols_list(args.opp_q_cols),
        )
        model = train_model(args.csv, args.model, alpha=float(args.alpha), cfg=cfg)
        print(f"\n✅ Modelo guardado en: {args.model}")
        print(f"   Equipos en el modelo: {len(model.entity_to_idx)}")
        return 0

    model = load_model(args.model)
    total_lines = parse_lines(getattr(args, "total_lines", None))
    team_lines = parse_lines(getattr(args, "team_lines", None))
    opp_lines = parse_lines(getattr(args, "opp_lines", None))

    mu_team, std_team, mu_opp, std_opp = predict_quarters(model, args.team, args.opp, args.location)

    if args.cmd == "predict":
        run_prediction(args.team, args.opp, args.location, mu_team, std_team, mu_opp, std_opp,
                       total_lines, team_lines, opp_lines, float(args.min_prob))
        return 0

    if args.cmd == "predict-live":
        q1 = parse_score(args.q1_score)
        mu_team_adj, mu_opp_adj, meta, actuals = apply_live_adjustment(mu_team, mu_opp, q1=q1, q2=None, q3=None,
                                                                       live_weight=float(args.live_weight))
        run_prediction(args.team, args.opp, args.location, mu_team_adj, std_team, mu_opp_adj, std_opp,
                       total_lines, team_lines, opp_lines, float(args.min_prob),
                       actuals=actuals, live_meta=meta)
        return 0

    if args.cmd == "predict-live2":
        q1 = parse_score(args.q1_score) if args.q1_score else None
        q2 = parse_score(args.q2_score) if args.q2_score else None
        mu_team_adj, mu_opp_adj, meta, actuals = apply_live_adjustment(mu_team, mu_opp, q1=q1, q2=q2, q3=None,
                                                                       live_weight=float(args.live_weight))
        run_prediction(args.team, args.opp, args.location, mu_team_adj, std_team, mu_opp_adj, std_opp,
                       total_lines, team_lines, opp_lines, float(args.min_prob),
                       actuals=actuals, live_meta=meta)
        return 0

    if args.cmd == "predict-live3":
        q1 = parse_score(args.q1_score) if args.q1_score else None
        q2 = parse_score(args.q2_score) if args.q2_score else None
        q3 = parse_score(args.q3_score) if args.q3_score else None
        mu_team_adj, mu_opp_adj, meta, actuals = apply_live_adjustment(
            mu_team, mu_opp, q1=q1, q2=q2, q3=q3,
            live_weight=float(args.live_weight),
            w_q1=float(args.w_q1), w_q2=float(args.w_q2), w_q3=float(args.w_q3),
        )
        run_prediction(args.team, args.opp, args.location, mu_team_adj, std_team, mu_opp_adj, std_opp,
                       total_lines, team_lines, opp_lines, float(args.min_prob),
                       actuals=actuals, live_meta=meta)
        return 0

    raise SystemExit("Comando inválido.")


if __name__ == "__main__":
    raise SystemExit(main())
