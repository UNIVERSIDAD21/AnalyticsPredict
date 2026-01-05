#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_estadisticas_equipos.py — Genera JSON con estadísticas agregadas por equipo.

Uso:
    python generar_estadisticas_equipos.py --csv-dir ./ --equipos-json ../backend/datos/equipos_nba.json \
        --out ../backend/datos/estadisticas_equipos.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd


MAPA_NOMBRES = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
}


def cargar_csvs(csv_dir: Path) -> pd.DataFrame:
    paths = sorted(p for p in csv_dir.glob("*.csv") if p.is_file())
    if not paths:
        raise SystemExit(f"No se encontraron CSVs en {csv_dir}")
    frames = []
    for path in paths:
        df = pd.read_csv(path)
        if "season_type" in df.columns:
            df = df[df["season_type"].fillna("").str.upper() == "REG"].copy()
        if "valid_linescore" in df.columns:
            df = df[df["valid_linescore"] == True].copy()  # noqa: E712
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    return data


def calcular_estadisticas_equipo(df: pd.DataFrame) -> Dict[str, object]:
    df = df.dropna(subset=["team_total", "opp_total", "team_q1", "team_q2", "team_q3", "team_q4"])
    df = df.sort_values("date")

    wins = int((df["team_total"] > df["opp_total"]).sum())
    losses = int((df["team_total"] < df["opp_total"]).sum())

    racha = [
        "W" if row["team_total"] > row["opp_total"] else "L"
        for _, row in df.tail(5).iterrows()
    ]

    promedios_anotados = {
        "q1": float(df["team_q1"].mean()),
        "q2": float(df["team_q2"].mean()),
        "q3": float(df["team_q3"].mean()),
        "q4": float(df["team_q4"].mean()),
        "total": float(df["team_total"].mean()),
    }
    promedios_recibidos = {
        "q1": float(df["opp_q1"].mean()),
        "q2": float(df["opp_q2"].mean()),
        "q3": float(df["opp_q3"].mean()),
        "q4": float(df["opp_q4"].mean()),
        "total": float(df["opp_total"].mean()),
    }

    local_df = df[df["location"] == "HOME"]
    visitante_df = df[df["location"] == "AWAY"]

    linea_promedio = float((df["team_total"] + df["opp_total"]).mean())
    total_q = {
        "q1": df["team_q1"] + df["opp_q1"],
        "q2": df["team_q2"] + df["opp_q2"],
        "q3": df["team_q3"] + df["opp_q3"],
        "q4": df["team_q4"] + df["opp_q4"],
    }
    linea_q = {q: float(total_q[q].mean()) for q in total_q}
    tendencias_over = {
        "q1": float((total_q["q1"] > linea_q["q1"]).mean()),
        "q2": float((total_q["q2"] > linea_q["q2"]).mean()),
        "q3": float((total_q["q3"] > linea_q["q3"]).mean()),
        "q4": float((total_q["q4"] > linea_q["q4"]).mean()),
        "total": float(((df["team_total"] + df["opp_total"]) > linea_promedio).mean()),
    }

    # Diferencia de puntos agregada (anotados - recibidos) a lo largo de la temporada.
    diferencia_puntos = int(df["team_total"].sum() - df["opp_total"].sum())

    return {
        "record": {"victorias": wins, "derrotas": losses},
        "racha": racha,
        "promedios": {
            "anotados": promedios_anotados,
            "recibidos": promedios_recibidos,
        },
        "local": {
            "victorias": int((local_df["team_total"] > local_df["opp_total"]).sum()),
            "derrotas": int((local_df["team_total"] < local_df["opp_total"]).sum()),
            "ppg": float(local_df["team_total"].mean()) if not local_df.empty else 0.0,
        },
        "visitante": {
            "victorias": int((visitante_df["team_total"] > visitante_df["opp_total"]).sum()),
            "derrotas": int((visitante_df["team_total"] < visitante_df["opp_total"]).sum()),
            "ppg": float(visitante_df["team_total"].mean()) if not visitante_df.empty else 0.0,
        },
        "tendencias_over": tendencias_over,
        "linea_promedio": linea_promedio,
        # Guardar la diferencia de puntos para uso en el ordenamiento.
        "diferencia_puntos": diferencia_puntos,
    }


def normalizar_nombre_equipo(nombre: str) -> str:
    return MAPA_NOMBRES.get(nombre, nombre)


def determinar_temporada_objetivo(data: pd.DataFrame, temporada_arg: str | None) -> int:
    if "season" not in data.columns:
        raise SystemExit("No se encontró la columna season en los CSV.")

    seasons = pd.to_numeric(data["season"], errors="coerce")
    seasons_validos = seasons.dropna()
    if seasons_validos.empty:
        raise SystemExit("No se encontraron valores válidos en la columna season.")

    if temporada_arg is not None:
        temporada_objetivo = int(temporada_arg)
    else:
        temporada_objetivo = int(seasons_validos.max())

    return temporada_objetivo


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera estadísticas de equipos NBA.")
    parser.add_argument("--csv-dir", default=".", help="Directorio con CSVs")
    parser.add_argument("--equipos-json", default="../backend/datos/equipos_nba.json", help="JSON equipos base")
    parser.add_argument("--out", default="../backend/datos/estadisticas_equipos.json", help="Salida JSON")
    parser.add_argument("--season", default=None, help="Temporada objetivo (por defecto, la más reciente)")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    data = cargar_csvs(csv_dir)
    temporada_objetivo = determinar_temporada_objetivo(data, args.season)
    data = data[pd.to_numeric(data["season"], errors="coerce") == temporada_objetivo].copy()
    equipos_base = json.loads(Path(args.equipos_json).read_text(encoding="utf-8"))
    mapa_info = {e["nombre"]: e for e in equipos_base}

    equipos = []
    for nombre, df_equipo in data.groupby("team"):
        nombre_normalizado = normalizar_nombre_equipo(nombre)
        info = mapa_info.get(nombre_normalizado)
        if not info:
            continue
        estadisticas = calcular_estadisticas_equipo(df_equipo)
        equipos.append(
            {
                "nombre": nombre_normalizado,
                "abreviatura": info["abreviatura"],
                "conferencia": info.get("conferencia", ""),
                "record": estadisticas["record"],
                "posicion": 0,
                "racha": estadisticas["racha"],
                "promedios": estadisticas["promedios"],
                "local": estadisticas["local"],
                "visitante": estadisticas["visitante"],
                "tendencias_over": estadisticas["tendencias_over"],
                "linea_promedio": estadisticas["linea_promedio"],
                # Incluir diferencia de puntos para poder ordenar correctamente.
                "diferencia_puntos": estadisticas.get("diferencia_puntos", 0),
            }
        )

    # Ordenar equipos dentro de cada conferencia utilizando múltiples criterios:
    # porcentaje de victorias, luego victorias totales y luego diferencia de puntos.
    for conferencia in {"Este", "Oeste"}:
        equipos_conf = [e for e in equipos if e["conferencia"] == conferencia]
        equipos_conf.sort(
            key=lambda e: (
                e["record"]["victorias"] / max(1, (e["record"]["victorias"] + e["record"]["derrotas"])),
                e["record"]["victorias"],
                e.get("diferencia_puntos", 0),
            ),
            reverse=True,
        )
        for idx, equipo in enumerate(equipos_conf, start=1):
            equipo["posicion"] = idx

    salida = {
        "fecha_actualizacion": datetime.utcnow().isoformat(),
        "equipos": sorted(equipos, key=lambda e: e["nombre"]),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Estadísticas guardadas en {out_path}")


if __name__ == "__main__":
    main()
