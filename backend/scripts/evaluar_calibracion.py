#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluar_calibracion.py — Script para evaluar y monitorear calibración de probabilidades.

Este script permite evaluar la calidad de la calibración actual,
generar reportes y alertas cuando la calibración se deteriora.

Uso:
    python evaluar_calibracion.py --mercado todos --periodo todo

Opciones:
    --mercado      Mercado específico o 'todos' (default: todos)
    --periodo      'semana' | 'mes' | 'temporada' | 'todo' (default: todo)
    --exportar     Exportar reporte a archivo JSON
    --umbral-ece   Umbral de alerta para ECE (default: 0.05)
    --verbose      Información detallada

Ejemplo:
    python evaluar_calibracion.py --mercado CORNERS_FT --periodo mes --exportar reporte.json
"""

import sys
import os
import argparse
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

import numpy as np

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import obtener_pool
from motor_futbol.tipos import TipoMercadoFutbol
from motor_futbol.calibracion import (
    GestorCalibradores,
    calcular_brier_score,
    calcular_log_loss,
    calcular_ece,
    calcular_mce,
    generar_reliability_diagram,
)


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def obtener_todos_mercados() -> List[TipoMercadoFutbol]:
    """Retorna lista de todos los mercados disponibles."""
    return (
        TipoMercadoFutbol.mercados_corners() +
        TipoMercadoFutbol.mercados_goles() +
        TipoMercadoFutbol.mercados_disparos()
    )


def calcular_fecha_inicio(periodo: str) -> Optional[date]:
    """Calcula la fecha de inicio según el período."""
    hoy = date.today()

    if periodo == "semana":
        return hoy - timedelta(days=7)
    elif periodo == "mes":
        return hoy - timedelta(days=30)
    elif periodo == "temporada":
        # Asumimos temporada desde agosto
        if hoy.month >= 8:
            return date(hoy.year, 8, 1)
        else:
            return date(hoy.year - 1, 8, 1)
    else:  # todo
        return None


def obtener_predicciones_periodo(
    pool,
    mercado: TipoMercadoFutbol,
    fecha_inicio: Optional[date] = None,
) -> tuple:
    """
    Obtiene predicciones y resultados para un período.

    Args:
        pool: Pool de conexiones
        mercado: Mercado a evaluar
        fecha_inicio: Fecha de inicio (None = todo)

    Returns:
        Tupla (prob_raw, prob_calibrada, outcomes)
    """
    mercado_str = mercado.value.upper()

    # Query base
    query = """
        SELECT
            prob_over_raw,
            prob_over_calibrada,
            CASE
                WHEN resultado_real > linea THEN 1
                ELSE 0
            END as outcome
        FROM (
            SELECT
                p.prob_over_raw,
                COALESCE(p.prob_over_calibrada, p.prob_over_raw) as prob_over_calibrada,
                p.linea,
                CASE
                    WHEN p.mercado LIKE '%%CORNERS%%' THEN
                        COALESCE(r.corners_local_ft + r.corners_visitante_ft,
                                 r.corners_local_1t + r.corners_visitante_1t +
                                 r.corners_local_2t + r.corners_visitante_2t)
                    WHEN p.mercado LIKE '%%GOLES%%' THEN
                        COALESCE(r.goles_local_ft + r.goles_visitante_ft,
                                 r.goles_local_1t + r.goles_visitante_1t +
                                 r.goles_local_2t + r.goles_visitante_2t)
                    WHEN p.mercado LIKE '%%DISPAROS%%' THEN
                        r.disparos_local_total + r.disparos_visitante_total
                    ELSE NULL
                END as resultado_real,
                pf.fecha_partido
            FROM predicciones_mercado p
            JOIN partidos_futbol pf ON p.partido_id = pf.id
            JOIN resultados_futbol r ON pf.id = r.partido_id
            WHERE p.mercado = %s
              AND p.prob_over_raw IS NOT NULL
              AND pf.estado = 'FINALIZADO'
    """

    params = [mercado_str]

    if fecha_inicio:
        query += " AND pf.fecha_partido >= %s"
        params.append(fecha_inicio)

    query += """
            ORDER BY pf.fecha_partido ASC
        ) sub
        WHERE resultado_real IS NOT NULL
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

                if not rows:
                    return np.array([]), np.array([]), np.array([])

                prob_raw = np.array([float(row[0]) for row in rows])
                prob_cal = np.array([float(row[1]) if row[1] else row[0] for row in rows])
                outcomes = np.array([int(row[2]) for row in rows])

                return prob_raw, prob_cal, outcomes

    except Exception as e:
        logger.error(f"Error obteniendo predicciones: {e}")
        return np.array([]), np.array([]), np.array([])


def obtener_calibradores_activos_info(pool) -> Dict[str, Dict[str, Any]]:
    """Obtiene información de calibradores activos desde BD."""
    info = {}

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        mercado,
                        metodo,
                        fecha_entrenamiento,
                        brier_antes,
                        brier_despues,
                        mejora_validacion,
                        n_muestras_entrenamiento,
                        creado_en
                    FROM calibradores_futbol
                    WHERE activo = TRUE
                """)

                for row in cur.fetchall():
                    info[row[0]] = {
                        "metodo": row[1],
                        "fecha_entrenamiento": row[2].isoformat() if row[2] else None,
                        "brier_antes": float(row[3]) if row[3] else None,
                        "brier_despues": float(row[4]) if row[4] else None,
                        "mejora_validacion": float(row[5]) if row[5] else None,
                        "n_muestras": row[6],
                        "creado_en": row[7].isoformat() if row[7] else None,
                    }

    except Exception as e:
        logger.error(f"Error obteniendo calibradores activos: {e}")

    return info


def evaluar_mercado(
    pool,
    mercado: TipoMercadoFutbol,
    fecha_inicio: Optional[date],
    umbral_ece: float,
) -> Dict[str, Any]:
    """
    Evalúa la calibración de un mercado.

    Args:
        pool: Pool de conexiones
        mercado: Mercado a evaluar
        fecha_inicio: Fecha de inicio del período
        umbral_ece: Umbral para alertas de ECE

    Returns:
        Diccionario con métricas y alertas
    """
    prob_raw, prob_cal, outcomes = obtener_predicciones_periodo(
        pool, mercado, fecha_inicio
    )

    if len(outcomes) == 0:
        return {
            "mercado": mercado.value,
            "n_muestras": 0,
            "error": "Sin datos para el período",
        }

    # Calcular métricas
    resultado = {
        "mercado": mercado.value,
        "n_muestras": len(outcomes),
        "metricas_raw": {
            "brier_score": calcular_brier_score(prob_raw, outcomes),
            "log_loss": calcular_log_loss(prob_raw, outcomes),
            "ece": calcular_ece(prob_raw, outcomes),
            "mce": calcular_mce(prob_raw, outcomes),
        },
        "metricas_calibradas": {
            "brier_score": calcular_brier_score(prob_cal, outcomes),
            "log_loss": calcular_log_loss(prob_cal, outcomes),
            "ece": calcular_ece(prob_cal, outcomes),
            "mce": calcular_mce(prob_cal, outcomes),
        },
    }

    # Calcular mejoras
    resultado["mejora"] = {
        "brier_score": (
            (resultado["metricas_raw"]["brier_score"] - resultado["metricas_calibradas"]["brier_score"])
            / resultado["metricas_raw"]["brier_score"] * 100
            if resultado["metricas_raw"]["brier_score"] > 0 else 0
        ),
        "ece": (
            (resultado["metricas_raw"]["ece"] - resultado["metricas_calibradas"]["ece"])
            / resultado["metricas_raw"]["ece"] * 100
            if resultado["metricas_raw"]["ece"] > 0 else 0
        ),
    }

    # Verificar alertas
    resultado["alertas"] = []

    if resultado["metricas_calibradas"]["ece"] > umbral_ece:
        resultado["alertas"].append({
            "tipo": "ECE_ALTO",
            "mensaje": f"ECE ({resultado['metricas_calibradas']['ece']:.4f}) supera umbral ({umbral_ece})",
            "severidad": "WARNING" if resultado["metricas_calibradas"]["ece"] < umbral_ece * 2 else "ERROR",
        })

    if resultado["mejora"]["brier_score"] < 0:
        resultado["alertas"].append({
            "tipo": "BRIER_EMPEORO",
            "mensaje": f"Calibración empeoró Brier Score en {abs(resultado['mejora']['brier_score']):.2f}%",
            "severidad": "WARNING",
        })

    # Generar datos para reliability diagram
    reliability = generar_reliability_diagram(prob_cal, outcomes)
    resultado["reliability_diagram"] = reliability.to_dict()

    return resultado


def imprimir_resultado(resultado: Dict[str, Any], verbose: bool = False) -> None:
    """Imprime resultado de evaluación formateado."""
    mercado = resultado["mercado"]
    n = resultado.get("n_muestras", 0)

    if "error" in resultado:
        print(f"\n  {mercado}: {resultado['error']}")
        return

    print(f"\n  {'='*50}")
    print(f"  {mercado}")
    print(f"  {'='*50}")
    print(f"  Muestras evaluadas: {n:,}")

    # Métricas raw vs calibradas
    print(f"\n  {'Métrica':<15} {'Raw':>10} {'Calibrada':>10} {'Mejora':>10}")
    print(f"  {'-'*45}")

    raw = resultado["metricas_raw"]
    cal = resultado["metricas_calibradas"]
    mejora = resultado["mejora"]

    for metrica in ["brier_score", "log_loss", "ece", "mce"]:
        mejora_pct = mejora.get(metrica, "-")
        if isinstance(mejora_pct, float):
            mejora_str = f"{mejora_pct:+.1f}%"
        else:
            mejora_str = "-"
        print(f"  {metrica:<15} {raw[metrica]:>10.4f} {cal[metrica]:>10.4f} {mejora_str:>10}")

    # Alertas
    if resultado.get("alertas"):
        print(f"\n  ALERTAS:")
        for alerta in resultado["alertas"]:
            simbolo = "ALERTA" if alerta["severidad"] == "WARNING" else "ERROR"
            print(f"    [{simbolo}] {alerta['mensaje']}")

    if verbose and "reliability_diagram" in resultado:
        print(f"\n  Reliability Diagram:")
        rd = resultado["reliability_diagram"]
        print(f"    {'Bin':<15} {'Predicho':>10} {'Real':>10} {'Conteo':>10}")
        for i, (bin_range, pred, real, cnt) in enumerate(zip(
            rd["bins"], rd["frecuencia_predicha"], rd["frecuencia_real"], rd["conteo"]
        )):
            print(f"    {bin_range[0]:.1f}-{bin_range[1]:.1f} {pred:>10.3f} {real:>10.3f} {cnt:>10}")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Evaluación de calibración de probabilidades",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--mercado",
        type=str,
        default="todos",
        help="Mercado específico o 'todos' (default: todos)",
    )
    parser.add_argument(
        "--periodo",
        type=str,
        choices=["semana", "mes", "temporada", "todo"],
        default="todo",
        help="Período a evaluar (default: todo)",
    )
    parser.add_argument(
        "--exportar",
        type=str,
        default=None,
        help="Exportar reporte a archivo JSON",
    )
    parser.add_argument(
        "--umbral-ece",
        type=float,
        default=0.05,
        help="Umbral de alerta para ECE (default: 0.05)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Información detallada",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "="*60)
    print("  EVALUACIÓN DE CALIBRACIÓN - FÚTBOL")
    print("="*60)

    # Obtener pool de conexiones
    pool = obtener_pool()

    # Calcular fecha de inicio
    fecha_inicio = calcular_fecha_inicio(args.periodo)

    print(f"\n  Período: {args.periodo}")
    if fecha_inicio:
        print(f"  Desde: {fecha_inicio}")
    else:
        print(f"  Desde: Todo el historial")

    # Determinar mercados a evaluar
    if args.mercado.lower() == "todos":
        mercados = obtener_todos_mercados()
    else:
        try:
            mercados = [TipoMercadoFutbol(args.mercado.upper())]
        except ValueError:
            print(f"\nError: Mercado desconocido: {args.mercado}")
            sys.exit(1)

    # Obtener info de calibradores activos
    calibradores_info = obtener_calibradores_activos_info(pool)

    print(f"\n  Calibradores activos: {len(calibradores_info)}")
    for merc, info in calibradores_info.items():
        print(f"    - {merc}: {info['metodo']} (entrenado: {info['fecha_entrenamiento']})")

    # Evaluar cada mercado
    resultados = []
    alertas_totales = []

    for mercado in mercados:
        resultado = evaluar_mercado(pool, mercado, fecha_inicio, args.umbral_ece)
        resultados.append(resultado)
        imprimir_resultado(resultado, args.verbose)

        if resultado.get("alertas"):
            alertas_totales.extend(resultado["alertas"])

    # Resumen final
    resultados_validos = [r for r in resultados if "error" not in r]

    if resultados_validos:
        print("\n" + "="*60)
        print("  RESUMEN")
        print("="*60)

        total_muestras = sum(r["n_muestras"] for r in resultados_validos)
        print(f"\n  Mercados evaluados: {len(resultados_validos)}")
        print(f"  Total muestras: {total_muestras:,}")

        if resultados_validos:
            avg_ece_raw = np.mean([r["metricas_raw"]["ece"] for r in resultados_validos])
            avg_ece_cal = np.mean([r["metricas_calibradas"]["ece"] for r in resultados_validos])
            avg_brier_raw = np.mean([r["metricas_raw"]["brier_score"] for r in resultados_validos])
            avg_brier_cal = np.mean([r["metricas_calibradas"]["brier_score"] for r in resultados_validos])

            print(f"\n  Promedios:")
            print(f"    ECE:    {avg_ece_raw:.4f} -> {avg_ece_cal:.4f}")
            print(f"    Brier:  {avg_brier_raw:.4f} -> {avg_brier_cal:.4f}")

        if alertas_totales:
            print(f"\n  ALERTAS TOTALES: {len(alertas_totales)}")
            for alerta in alertas_totales:
                print(f"    [{alerta['severidad']}] {alerta['mensaje']}")

    # Exportar si se solicita
    if args.exportar:
        reporte = {
            "fecha_generacion": datetime.now().isoformat(),
            "periodo": args.periodo,
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "calibradores_activos": calibradores_info,
            "resultados": resultados,
            "alertas": alertas_totales,
        }

        with open(args.exportar, "w", encoding="utf-8") as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)

        print(f"\n  Reporte exportado a: {args.exportar}")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
