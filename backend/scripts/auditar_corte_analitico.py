#!/usr/bin/env python3
"""Corte agregado de solo lectura; no entrena, ingiere ni certifica futuro.

Uso: cd backend && python scripts/auditar_corte_analitico.py > /tmp/corte.json
DATABASE_URL se carga de backend/.env sin imprimirla. El JSON no contiene filas ni IDs.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from metricas_probabilisticas import resumir_pares_binarios


def metricas_binarias(pares: list[tuple[float, int]]) -> dict:
    resultado = resumir_pares_binarios(pares)
    return {"n": resultado["n"],
            "brier": round(resultado["brier"], 6) if resultado["brier"] is not None else None,
            "log_loss": round(resultado["log_loss"], 6) if resultado["log_loss"] is not None else None,
            "ece_10": round(resultado["ece"], 6) if resultado["ece"] is not None else None}


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
    # El histórico se conserva; un 0–0 NBA no constituye outcome evaluable.
    join_partido = (
        "LEFT JOIN partidos_baloncesto pb ON pb.id = p.partido_id"
        if tabla == "predicciones_registradas" else ""
    )
    dudoso = (
        "(pb.local_total = 0 AND pb.visitante_total = 0)"
        if join_partido else "NULL::boolean"
    )
    cur.execute(f"SELECT p.{raw}, p.{calibrada}, p.outcome_binario, p.resuelto, "
                f"p.timestamp_generacion, p.timestamp_resolucion, p.modelo_version_id, "
                f"p.calibrador_id, p.mercado, {dudoso} FROM {tabla} p {join_partido}")
    filas = cur.fetchall()
    raw_pares, cal_pares = [], []
    mercados: dict[str, list[tuple[float, int]]] = defaultdict(list)
    sin_modelo = sin_calibrador = violaciones = cal_sin_procedencia = 0
    resueltas = outcomes_no_acreditados = 0
    for p_raw, p_cal, y, resuelto, generado, resuelto_en, modelo, calibrador, mercado, cero_cero in filas:
        sin_modelo += modelo is None
        sin_calibrador += calibrador is None
        resueltas += bool(resuelto)
        if generado and resuelto_en and generado >= resuelto_en:
            violaciones += 1
        if resuelto and y is not None and cero_cero:
            outcomes_no_acreditados += 1
            continue
        if not resuelto or y is None:
            continue
        yi = int(y)
        if p_raw is not None and 0 <= p_raw <= 1:
            raw_pares.append((float(p_raw), yi))
            mercados[str(mercado)].append((float(p_raw), yi))
        if p_cal is not None and calibrador is None:
            cal_sin_procedencia += 1
        if p_cal is not None and calibrador is not None and 0 <= p_cal <= 1:
            cal_pares.append((float(p_cal), yi))
    return {"total": len(filas), "resueltas": resueltas,
            "outcomes_cero_cero_no_acreditados": outcomes_no_acreditados,
            "sin_modelo_id": sin_modelo,
            "sin_calibrador_id": sin_calibrador, "generacion_no_anterior_a_resolucion": violaciones,
            "calibrada_resuelta_sin_calibrador_id": cal_sin_procedencia,
            "raw": metricas_binarias(raw_pares), "calibrada": metricas_binarias(cal_pares),
            "por_mercado_raw": {m: metricas_binarias(p) for m, p in sorted(mercados.items())}}


def resumen_partidos_nba(cur) -> dict:
    """Cuenta únicamente NBA; `partidos_baloncesto` también contiene Euroliga."""
    cur.execute("""SELECT count(*), max(p.fecha_partido),
        count(*) FILTER (WHERE p.source IS NULL),
        count(*) FILTER (WHERE p.local_total=0 AND p.visitante_total=0),
        count(*) FILTER (WHERE p.local_q1 IS NULL OR p.visitante_q1 IS NULL
                          OR p.local_q4 IS NULL OR p.visitante_q4 IS NULL),
        count(*) FILTER (WHERE p.fecha_partido >= current_date-30)
        FROM partidos_baloncesto p
        JOIN competiciones_baloncesto c ON c.id=p.competicion_id
        WHERE c.codigo='nba'""")
    n, ultima, sin_fuente, cero_cero, sin_cuartos, ultimos_30 = cur.fetchone()
    cur.execute("""SELECT coalesce(sum(n-1),0) FROM (
        SELECT count(*) n FROM partidos_baloncesto p
        JOIN competiciones_baloncesto c ON c.id=p.competicion_id
        WHERE c.codigo='nba' AND p.source_game_id IS NOT NULL
        GROUP BY p.source,p.source_game_id HAVING count(*)>1) x""")
    duplicados = cur.fetchone()[0]
    return {"partidos": n, "fecha_max": ultima, "sin_source": sin_fuente,
            "cero_cero": cero_cero, "sin_cuartos_q1_q4": sin_cuartos,
            "partidos_ultimos_30_dias": ultimos_30,
            "duplicados_source_id": int(duplicados)}


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
            reporte["nba_datos"] = resumen_partidos_nba(cur)
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
            cur.execute("""SELECT
                count(*) FILTER (WHERE p_raw < 0 OR p_raw > 1 OR p_calibrada < 0 OR p_calibrada > 1)
                FROM predicciones_registradas""")
            nba_prob_fuera_rango = cur.fetchone()[0]
            cur.execute("""SELECT
                count(*) FILTER (WHERE prob_over < 0 OR prob_over > 1 OR prob_over_calibrada < 0 OR prob_over_calibrada > 1),
                count(*) FILTER (WHERE pf.id IS NULL)
                FROM predicciones_futbol p LEFT JOIN partidos_futbol pf ON pf.id=p.partido_id""")
            futbol_prob_fuera_rango, futbol_partido_huerfano = cur.fetchone()
            cur.execute("""SELECT count(*) FILTER (WHERE p.local_total < 0 OR p.visitante_total < 0
                OR p.local_total > 250 OR p.visitante_total > 250)
                FROM partidos_baloncesto p
                JOIN competiciones_baloncesto c ON c.id=p.competicion_id
                WHERE c.codigo='nba'""")
            nba_marcador_outlier = cur.fetchone()[0]
            cur.execute("""SELECT
                count(*) FILTER (WHERE estado='FINALIZADO' AND (local_goles_total IS NULL OR visitante_goles_total IS NULL)),
                count(*) FILTER (WHERE local_goles_total < 0 OR visitante_goles_total < 0
                    OR local_goles_total > 30 OR visitante_goles_total > 30)
                FROM partidos_futbol""")
            futbol_goles_finalizados_nulos, futbol_goles_outlier = cur.fetchone()
            cur.execute("""SELECT count(*) FILTER (WHERE stake IS NULL OR stake <= 0 OR cuota IS NULL OR cuota <= 1)
                FROM apuestas WHERE resultado IN ('GANADA','PERDIDA')""")
            nba_stake_cuota_invalidos = cur.fetchone()[0]
            reporte["null_outliers_integridad"] = {
                "nba_prob_fuera_rango": nba_prob_fuera_rango,
                "futbol_prob_fuera_rango": futbol_prob_fuera_rango,
                "nba_marcador_outlier_revision": nba_marcador_outlier,
                "futbol_goles_outlier_revision": futbol_goles_outlier,
                "futbol_finalizados_goles_nulos": futbol_goles_finalizados_nulos,
                "futbol_predicciones_partido_huerfano": futbol_partido_huerfano,
                "nba_stake_cuota_invalidos": nba_stake_cuota_invalidos,
            }
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
