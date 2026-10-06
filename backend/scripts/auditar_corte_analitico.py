#!/usr/bin/env python3
"""Corte agregado de solo lectura; no entrena, ingiere ni certifica futuro.

Uso: cd backend && python scripts/auditar_corte_analitico.py > /tmp/corte.json
DATABASE_URL se carga de backend/.env sin imprimirla. El JSON no contiene filas ni IDs.
"""
from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def metricas_binarias(pares: list[tuple[float, int]]) -> dict:
    if not pares:
        return {"n": 0, "brier": None, "log_loss": None, "ece_10": None}
    n = len(pares)
    brier = sum((p - y) ** 2 for p, y in pares) / n
    log_loss = -sum(y * math.log(max(1e-12, min(1 - 1e-12, p))) +
                    (1 - y) * math.log(max(1e-12, min(1 - 1e-12, 1 - p)))
                    for p, y in pares) / n
    buckets: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for p, y in pares:
        buckets[min(9, int(p * 10))].append((p, y))
    ece = sum(len(b) / n * abs(sum(p for p, _ in b) / len(b) -
                              sum(y for _, y in b) / len(b)) for b in buckets.values())
    return {"n": n, "brier": round(brier, 6), "log_loss": round(log_loss, 6),
            "ece_10": round(ece, 6)}


def resumen_bets(filas: list[tuple]) -> dict:
    grupos: dict[str, list[tuple]] = defaultdict(list)
    for estado, cuota, stake, ganancia, confianza, _ in filas:
        if estado not in {"GANADA", "PERDIDA"}:
            continue
        grupos["global"].append((estado, cuota, stake, ganancia))
        grupos[f"confianza:{confianza or 'SIN_DATO'}"].append((estado, cuota, stake, ganancia))
        if cuota is None:
            tramo = "SIN_DATO"
        elif cuota <= 1.5:
            tramo = "<=1.5"
        elif cuota <= 2:
            tramo = "(1.5,2]"
        else:
            tramo = ">2"
        grupos[f"cuota:{tramo}"].append((estado, cuota, stake, ganancia))
    out = {}
    for nombre, grupo in sorted(grupos.items()):
        n = len(grupo)
        apostado = sum(float(stake or 0) for _, _, stake, _ in grupo)
        ganancia = sum(float(g or 0) for _, _, _, g in grupo)
        out[nombre] = {"n": n, "ganadas": sum(e == "GANADA" for e, *_ in grupo),
                       "win_rate_pct": round(100 * sum(e == "GANADA" for e, *_ in grupo) / n, 2),
                       "roi_registrado_no_certificado_pct": round(100 * ganancia / apostado, 2) if apostado else None,
                       "stake_total": round(apostado, 2), "ganancia_total": round(ganancia, 2)}
    return out


def predicciones(cur, tabla: str, raw: str, calibrada: str) -> dict:
    cur.execute(f"SELECT {raw}, {calibrada}, outcome_binario, resuelto, timestamp_generacion, "
                f"timestamp_resolucion, modelo_version_id, calibrador_id, mercado FROM {tabla}")
    filas = cur.fetchall()
    raw_pares, cal_pares = [], []
    mercados: dict[str, list[tuple[float, int]]] = defaultdict(list)
    sin_modelo = sin_calibrador = violaciones = 0
    resueltas = 0
    for p_raw, p_cal, y, resuelto, generado, resuelto_en, modelo, calibrador, mercado in filas:
        sin_modelo += modelo is None
        sin_calibrador += calibrador is None
        resueltas += bool(resuelto)
        if generado and resuelto_en and generado >= resuelto_en:
            violaciones += 1
        if not resuelto or y is None:
            continue
        yi = int(y)
        if p_raw is not None and 0 <= p_raw <= 1:
            raw_pares.append((float(p_raw), yi))
            mercados[str(mercado)].append((float(p_raw), yi))
        if p_cal is not None and 0 <= p_cal <= 1:
            cal_pares.append((float(p_cal), yi))
    return {"total": len(filas), "resueltas": resueltas, "sin_modelo_id": sin_modelo,
            "sin_calibrador_id": sin_calibrador, "generacion_no_anterior_a_resolucion": violaciones,
            "raw": metricas_binarias(raw_pares), "calibrada": metricas_binarias(cal_pares),
            "por_mercado_raw": {m: metricas_binarias(p) for m, p in sorted(mercados.items())}}


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL no configurada")
    reporte = {"corte_utc": datetime.now(timezone.utc).isoformat(),
               "metodo": "consulta agregada en transacción READ ONLY; sin retraining ni ingesta"}
    with psycopg.connect(url, options="-c default_transaction_read_only=on") as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW transaction_read_only")
            if cur.fetchone()[0] != "on":
                raise RuntimeError("La conexión no es read-only")
            cur.execute("SET LOCAL statement_timeout = '30s'")
            cur.execute("""SELECT count(*), max(fecha_partido),
                count(*) FILTER (WHERE source IS NULL),
                count(*) FILTER (WHERE local_total=0 AND visitante_total=0),
                count(*) FILTER (WHERE local_q1 IS NULL OR visitante_q1 IS NULL OR local_q4 IS NULL OR visitante_q4 IS NULL),
                count(*) FILTER (WHERE fecha_partido >= current_date-30)
                FROM partidos_baloncesto""")
            n, ultima, sin_fuente, cero_cero, sin_cuartos, ultimos_30 = cur.fetchone()
            cur.execute("""SELECT coalesce(sum(n-1),0) FROM (
                SELECT count(*) n FROM partidos_baloncesto
                WHERE source_game_id IS NOT NULL GROUP BY source,source_game_id HAVING count(*)>1) x""")
            duplicados = cur.fetchone()[0]
            reporte["nba_datos"] = {"partidos": n, "fecha_max": ultima, "sin_source": sin_fuente,
                "cero_cero": cero_cero, "sin_cuartos_q1_q4": sin_cuartos,
                "partidos_ultimos_30_dias": ultimos_30, "duplicados_source_id": int(duplicados)}
            cur.execute("""SELECT count(*), max(fecha_partido) FILTER (WHERE estado='FINALIZADO'),
                count(*) FILTER (WHERE estado='FINALIZADO'),
                count(*) FILTER (WHERE estado='FINALIZADO' AND fecha_partido >= now()-interval '30 days'),
                count(*) FILTER (WHERE estado='FINALIZADO' AND datos_corners_completos),
                count(*) FILTER (WHERE estado='FINALIZADO' AND datos_disparos_completos)
                FROM partidos_futbol""")
            n, ultima, finalizados, ultimos_30, corners, disparos = cur.fetchone()
            reporte["futbol_datos"] = {"partidos": n, "ultimo_finalizado": ultima,
                "finalizados": finalizados, "finalizados_ultimos_30_dias": ultimos_30,
                "finalizados_con_corners_completos": corners, "finalizados_con_disparos_completos": disparos}
            cur.execute("""SELECT coalesce(sum(n-1),0) FROM (
                SELECT count(*) n FROM partidos_futbol WHERE sofascore_match_id IS NOT NULL
                GROUP BY sofascore_match_id HAVING count(*)>1) x""")
            reporte["futbol_datos"]["duplicados_sofascore_id"] = int(cur.fetchone()[0])
            reporte["predicciones_nba"] = predicciones(cur, "predicciones_registradas", "p_raw", "p_calibrada")
            reporte["predicciones_futbol"] = predicciones(cur, "predicciones_futbol", "prob_over", "prob_over_calibrada")
            cur.execute("""SELECT count(*) FILTER (WHERE m.id IS NULL),
                count(*) FILTER (WHERE m.cutoff_entrenamiento IS NULL),
                count(*) FILTER (WHERE m.cutoff_entrenamiento::date > p.timestamp_generacion::date),
                count(*) FILTER (WHERE m.cutoff_entrenamiento::date = p.timestamp_generacion::date),
                count(*) FILTER (WHERE m.cutoff_entrenamiento::date < p.timestamp_generacion::date),
                count(*) FILTER (WHERE m.fecha_entrenamiento > p.timestamp_generacion)
                FROM predicciones_registradas p LEFT JOIN modelo_versiones m ON m.id=p.modelo_version_id""")
            sin_modelo, sin_cutoff, posterior, mismo_dia, anterior, entrenamiento_posterior = cur.fetchone()
            reporte["walk_forward_nba_auditoria_metadata"] = {
                "modelo_no_encontrado": sin_modelo, "cutoff_nulo": sin_cutoff,
                "cutoff_posterior_a_generacion_dia": posterior,
                "cutoff_mismo_dia_sin_orden_horario": mismo_dia,
                "cutoff_anterior_a_generacion_dia": anterior,
                "entrenamiento_posterior_a_generacion": entrenamiento_posterior}
            cur.execute("SELECT resultado,cuota,stake,ganancia,confianza_sistema,fecha_partido FROM apuestas")
            filas = cur.fetchall()
            reporte["bitacora_nba"] = {"total": len(filas), "segmentos_resueltos": resumen_bets(filas)}
            cur.execute("""SELECT
                count(*) FILTER (WHERE resultado='GANADA' AND abs(ganancia-stake*(cuota-1))>0.02),
                count(*) FILTER (WHERE resultado='PERDIDA' AND abs(ganancia+stake)>0.02),
                count(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA') AND
                    (ganancia IS NULL OR stake IS NULL OR cuota IS NULL OR stake<=0 OR cuota<=1))
                FROM apuestas""")
            victorias_inconsistentes, derrotas_inconsistentes, sin_base = cur.fetchone()
            reporte["bitacora_nba"]["calidad_pnl"] = {
                "ganadas_con_ganancia_inconsistente": victorias_inconsistentes,
                "perdidas_con_ganancia_inconsistente": derrotas_inconsistentes,
                "sin_base_valida": sin_base,
                "regla": "ganada=stake*(cuota-1); perdida=-stake; tolerancia absoluta 0.02"}
            for deporte, tabla in (("futbol", "apuestas_futbol"), ("combinadas", "apuestas_combinadas")):
                cur.execute(f"SELECT resultado,count(*) FROM {tabla} GROUP BY resultado ORDER BY resultado")
                reporte[f"bitacora_{deporte}"] = dict(cur.fetchall())
            cur.execute("""SELECT count(*), max(fecha_entrenamiento), max(cutoff_entrenamiento)
                FROM modelo_versiones""")
            n, entrenado, cutoff = cur.fetchone()
            reporte["versiones_modelo_nba"] = {"n": n, "ultimo_entrenamiento": entrenado,
                                               "ultimo_cutoff_registrado": cutoff}
    print(json.dumps(reporte, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
