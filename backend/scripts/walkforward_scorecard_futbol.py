#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import obtener_pool
from metricas_probabilisticas import resumir_pares_binarios
from motor_futbol.madurez_beta import clasificar_madurez_mercado, mapear_status_promocion, CRITERIOS_DEFAULT


@dataclass
class VentanaWF:
    idx: int
    inicio_train: datetime
    fin_train: datetime
    inicio_cal: datetime
    fin_cal: datetime
    inicio_eval: datetime
    fin_eval: datetime


def ece_bin(prob: List[float], y: List[int], bins: int = 10) -> float | None:
    if len(prob) != len(y):
        raise ValueError("Probabilidades y outcomes deben corresponder uno a uno")
    return resumir_pares_binarios(zip(prob, y), n_bins=bins)["ece"]


def generar_ventanas(fin: datetime, train_days: int, cal_days: int, eval_days: int, n_windows: int) -> List[VentanaWF]:
    ventanas: List[VentanaWF] = []
    cursor = fin
    for i in range(n_windows):
        fin_eval = cursor
        inicio_eval = fin_eval - timedelta(days=eval_days)
        fin_cal = inicio_eval
        inicio_cal = fin_cal - timedelta(days=cal_days)
        fin_train = inicio_cal
        inicio_train = fin_train - timedelta(days=train_days)
        ventanas.append(VentanaWF(i + 1, inicio_train, fin_train, inicio_cal, fin_cal, inicio_eval, fin_eval))
        cursor = inicio_eval
    ventanas.reverse()
    return ventanas


def main() -> None:
    ap = argparse.ArgumentParser(description="Backtesting walk-forward + scorecard de promoción por mercado (fútbol)")
    ap.add_argument("--train-days", type=int, default=180)
    ap.add_argument("--cal-days", type=int, default=60)
    ap.add_argument("--eval-days", type=int, default=30)
    ap.add_argument("--windows", type=int, default=6)
    ap.add_argument("--out-prefix", type=str, default="docs/reportes/BLOQUE_10_WALKFORWARD_FUTBOL")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    ventanas = generar_ventanas(now, args.train_days, args.cal_days, args.eval_days, args.windows)

    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='predicciones_futbol'")
            cols = {r['column_name'] for r in cur.fetchall()}
            raw_col = 'prob_over_raw' if 'prob_over_raw' in cols else ('prob_over' if 'prob_over' in cols else None)
            p_col = (f'COALESCE(prob_over_calibrada, {raw_col})'
                     if 'prob_over_calibrada' in cols and raw_col else raw_col)
            fecha_col = (
                'fecha_prediccion' if 'fecha_prediccion' in cols else
                ('timestamp_generacion' if 'timestamp_generacion' in cols else
                 ('creado_en' if 'creado_en' in cols else
                  ('fecha_calculo' if 'fecha_calculo' in cols else None)))
            )
            if p_col is None or fecha_col is None or 'outcome_binario' not in cols:
                raise RuntimeError('predicciones_futbol no tiene columnas mínimas para walk-forward')

            score_rows: List[Dict[str, Any]] = []
            emitidas_por_mercado: Dict[str, int] = defaultdict(int)
            for w in ventanas:
                cur.execute(
                    f"""
                    SELECT mercado::text AS mercado, linea, {p_col} AS p, outcome_binario::int AS y,
                           {"CASE WHEN prob_over_calibrada IS NULL THEN 1 ELSE 0 END" if 'prob_over_calibrada' in cols else '1'} AS fallback
                    FROM predicciones_futbol
                    WHERE {fecha_col} >= %s AND {fecha_col} < %s
                    """,
                    [w.inicio_eval, w.fin_eval],
                )
                rows = cur.fetchall()
                acc: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"p": [], "y": [], "lineas": set(), "fallback": 0, "emitidas": 0})
                for r in rows:
                    m = str(r['mercado']).upper()
                    acc[m]["emitidas"] += 1
                    emitidas_por_mercado[m] += 1
                    if r['y'] is not None and r['p'] is not None:
                        acc[m]["p"].append(float(r['p']))
                        acc[m]["y"].append(int(r['y']))
                        if int(r.get('fallback') or 0) == 1:
                            acc[m]["fallback"] += 1
                    if r.get('linea') is not None:
                        acc[m]["lineas"].add(float(r['linea']))

                for mercado, a in acc.items():
                    n = len(a['p'])
                    if n == 0:
                        continue
                    medidas = resumir_pares_binarios(zip(a['p'], a['y']))
                    brier = medidas['brier']
                    logloss = medidas['log_loss']
                    ece = medidas['ece']
                    sharp = float(sum(abs(p - 0.5) for p in a['p']) / n)
                    fallback_rate = float(a['fallback'] / n)

                    score_rows.append({
                        'ventana': w.idx,
                        'mercado': mercado,
                        'train_inicio': w.inicio_train.isoformat(),
                        'train_fin': w.fin_train.isoformat(),
                        'cal_inicio': w.inicio_cal.isoformat(),
                        'cal_fin': w.fin_cal.isoformat(),
                        'eval_inicio': w.inicio_eval.isoformat(),
                        'eval_fin': w.fin_eval.isoformat(),
                        'n_resueltas': n,
                        'n_emitidas': a['emitidas'],
                        'lineas_cubiertas': len(a['lineas']),
                        'brier': brier,
                        'log_loss': logloss,
                        'ece': ece,
                        'sharpness': sharp,
                        'fallback_rate': fallback_rate,
                    })

    # agregación final por mercado
    final: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"rows": []})
    for mercado in emitidas_por_mercado:
        final[mercado]
    for r in score_rows:
        final[r['mercado']]['rows'].append(r)

    clasificados = []
    for mercado, d in final.items():
        rows = d['rows']
        n_total = sum(int(x['n_resueltas']) for x in rows)
        lineas = max((int(x['lineas_cubiertas']) for x in rows), default=0)
        n_emitidas = emitidas_por_mercado[mercado]
        brier_avg = sum(float(x['brier']) * x['n_resueltas'] for x in rows) / n_total if n_total else None
        logloss_avg = sum(float(x['log_loss']) * x['n_resueltas'] for x in rows) / n_total if n_total else None
        ece_avg = None  # ECE de ventanas no es aditiva sin pares/bins agregados.
        fallback_avg = sum(float(x['fallback_rate']) * x['n_resueltas'] for x in rows) / n_total if n_total else None
        drift = None
        if len(rows) > 1:
            drift = abs(float(rows[-1]['brier']) - float(rows[0]['brier']))

        metricas = {
            'n_resueltas': n_total,
            'lineas_cubiertas': lineas,
            'brier': brier_avg,
            'log_loss': logloss_avg,
            'ece': ece_avg,
            'resolved_rate': n_total / n_emitidas if n_emitidas else None,
            'fallback_rate': fallback_avg,
            'window_drift_brier': drift,
        }
        # Este script solo puntúa predicciones persistidas; no demuestra training
        # temporal, artefactos congelados ni procedencia del estado operativo.
        nivel, motivos = clasificar_madurez_mercado(metricas, estado_mercado=None)
        motivos.append('walk_forward_y_estado_mercado_no_verificados')
        status = mapear_status_promocion(nivel)
        clasificados.append({
            'mercado': mercado,
            'status_final': status,
            'nivel': nivel,
            'motivos': motivos,
            **metricas,
        })

    prefix = Path(args.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = prefix.with_suffix('.json')
    csv_path = prefix.with_suffix('.csv')

    payload = {
        'generated_at': now.isoformat(),
        'config': {
            'train_days': args.train_days,
            'cal_days': args.cal_days,
            'eval_days': args.eval_days,
            'windows': args.windows,
            'criterios': CRITERIOS_DEFAULT.__dict__,
            'sin_leakage_verificado': False,
            'limitacion': 'Ventanas nominales; no verifica cutoff de entrenamiento ni artefactos congelados',
        },
        'ventanas': [w.__dict__ for w in ventanas],
        'scorecard_windows': score_rows,
        'scorecard_market': sorted(clasificados, key=lambda x: (x['status_final'], x['mercado'])),
        'resumen': {
            'bloqueado': sorted([m['mercado'] for m in clasificados if m['status_final'] == 'BLOQUEADO']),
            'laboratorio': sorted([m['mercado'] for m in clasificados if m['status_final'] == 'LABORATORIO']),
            'validacion': sorted([m['mercado'] for m in clasificados if m['status_final'] == 'VALIDACION']),
            'promocionable': sorted([m['mercado'] for m in clasificados if m['status_final'] == 'PROMOCIONABLE']),
        }
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    with csv_path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['mercado', 'status_final', 'nivel', 'n_resueltas', 'lineas_cubiertas', 'brier', 'log_loss', 'ece', 'resolved_rate', 'fallback_rate', 'window_drift_brier', 'motivos'])
        w.writeheader()
        for row in sorted(clasificados, key=lambda x: x['mercado']):
            out = dict(row)
            out['motivos'] = ';'.join(row.get('motivos', []))
            w.writerow(out)

    print(f"Scorecard JSON: {json_path}")
    print(f"Scorecard CSV: {csv_path}")


if __name__ == '__main__':
    main()
