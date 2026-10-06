#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calibrar_futbol.py — Script de calibración de probabilidades para fútbol.

Este script entrena calibradores de probabilidad usando datos históricos
de predicciones y sus resultados reales.

Uso:
    python calibrar_futbol.py --mercado todos --metodo auto --guardar --activar --verbose

Opciones:
    --mercado      Mercado específico o 'todos' (default: todos)
    --metodo       'platt' | 'isotonic' | 'auto' (default: auto)
    --min-muestras Mínimo de predicciones para entrenar (default: 200)
    --guardar      Guardar calibrador en BD
    --activar      Activar calibrador si mejora el actual
    --verbose      Información detallada
    --dry-run      Simular sin guardar

Ejemplo:
    python calibrar_futbol.py --mercado CORNERS_FT --metodo platt --guardar --activar
"""

import sys
import os
import argparse
import logging
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from psycopg_pool import ConnectionPool

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import obtener_database_url, obtener_pool
from motor_futbol.tipos import TipoMercadoFutbol, ResultadoCalibracion
from motor_futbol.calibracion import (
    CalibradorPlatt,
    CalibradorIsotonic,
    GestorCalibradores,
    calcular_brier_score,
    calcular_ece,
    calcular_log_loss,
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


@dataclass(frozen=True)
class ParTemporal:
    fecha_partido: datetime
    generacion: datetime
    resolucion: datetime


def obtener_datos_calibracion(
    pool,
    mercado: TipoMercadoFutbol,
) -> Tuple[np.ndarray, np.ndarray, List[ParTemporal]]:
    """Pares reales, resueltos y anteriores al partido, ordenados por evento.

    Nunca sustituye una consulta fallida o una muestra vacía por backtest ni
    por datos sintéticos. La probabilidad raw persistida en Neon es prob_over.
    """
    query = """
        SELECT p.prob_over, p.outcome_binario::int, pf.fecha_partido,
               p.timestamp_generacion, p.timestamp_resolucion
        FROM predicciones_futbol p
        JOIN partidos_futbol pf ON pf.id = p.partido_id
        WHERE p.mercado = %s
          AND p.origen::text = 'API_USUARIO'
          AND p.resuelto = true
          AND p.outcome_binario IS NOT NULL
          AND p.prob_over BETWEEN 0 AND 1
          AND pf.estado = 'FINALIZADO'
          AND p.timestamp_generacion IS NOT NULL
          AND p.timestamp_resolucion IS NOT NULL
          AND p.timestamp_generacion < pf.fecha_partido
          AND p.timestamp_resolucion >= pf.fecha_partido
          AND p.timestamp_generacion < p.timestamp_resolucion
    """
    query += " ORDER BY pf.fecha_partido ASC, p.timestamp_generacion ASC, p.id ASC"

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (mercado.value,))
                rows = cur.fetchall()
    except Exception as exc:
        raise RuntimeError(
            f"No se pudieron consultar pares reales de {mercado.value} "
            f"({type(exc).__name__}); calibración cancelada"
        ) from None

    return (
        np.asarray([float(row[0]) for row in rows], dtype=float),
        np.asarray([int(row[1]) for row in rows], dtype=int),
        [ParTemporal(row[2], row[3], row[4]) for row in rows],
    )


def dividir_train_validation(
    prob_raw: np.ndarray,
    outcomes: np.ndarray,
    pares_temporales: List[ParTemporal],
    train_ratio: float = 0.8,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, date]:
    """Holdout cronológico por día de partido, sin compartir día entre cortes."""
    n = len(prob_raw)
    if not 0 < train_ratio < 1 or n != len(outcomes) or n != len(pares_temporales):
        raise ValueError("Ratio o tamaños inválidos para holdout temporal")
    if any(
        a.fecha_partido > b.fecha_partido
        for a, b in zip(pares_temporales, pares_temporales[1:])
    ):
        raise ValueError("Los pares deben estar ordenados por fecha de partido")
    n_train = int(n * train_ratio)
    if not 0 < n_train < n:
        raise ValueError("Sin masa suficiente para train y validación")
    dia_corte = pares_temporales[n_train - 1].fecha_partido.date()
    while n_train < n and pares_temporales[n_train].fecha_partido.date() <= dia_corte:
        n_train += 1
    if n_train == n:
        raise ValueError("No hay fecha posterior independiente para validar")
    ultima_resolucion_train = max(par.resolucion for par in pares_temporales[:n_train])
    primera_generacion_val = min(par.generacion for par in pares_temporales[n_train:])
    if ultima_resolucion_train >= primera_generacion_val:
        raise ValueError(
            "Resultados de train no disponibles antes de generar validación"
        )
    return (
        prob_raw[:n_train], outcomes[:n_train],
        prob_raw[n_train:], outcomes[n_train:], ultima_resolucion_train.date(),
    )


def entrenar_calibrador(
    mercado: TipoMercadoFutbol,
    prob_train: np.ndarray,
    out_train: np.ndarray,
    prob_val: np.ndarray,
    out_val: np.ndarray,
    metodo: str = "platt",
) -> Tuple[Any, ResultadoCalibracion]:
    """
    Entrena un calibrador y evalúa en validación.

    Args:
        mercado: Tipo de mercado
        prob_train: Probabilidades de entrenamiento
        out_train: Outcomes de entrenamiento
        prob_val: Probabilidades de validación
        out_val: Outcomes de validación
        metodo: Método de calibración ('platt' o 'isotonic')

    Returns:
        Tupla (calibrador, resultado)
    """
    # Crear calibrador según método
    if metodo == "platt":
        calibrador = CalibradorPlatt(mercado)
    elif metodo == "isotonic":
        calibrador = CalibradorIsotonic(mercado)
    else:
        raise ValueError(f"Método desconocido: {metodo}")

    # Entrenar con datos de train
    resultado_train = calibrador.entrenar(prob_train, out_train)

    # Evaluar en validación
    prob_val_calibrada = calibrador.calibrar(prob_val)

    # Calcular métricas en validación
    brier_antes = calcular_brier_score(prob_val, out_val)
    brier_despues = calcular_brier_score(prob_val_calibrada, out_val)
    log_loss_antes = calcular_log_loss(prob_val, out_val)
    log_loss_despues = calcular_log_loss(prob_val_calibrada, out_val)
    ece_antes = calcular_ece(prob_val, out_val)
    ece_despues = calcular_ece(prob_val_calibrada, out_val)

    # Crear resultado con métricas de validación
    resultado = ResultadoCalibracion(
        mercado=mercado,
        metodo=metodo,
        brier_antes=brier_antes,
        log_loss_antes=log_loss_antes,
        ece_antes=ece_antes,
        brier_despues=brier_despues,
        log_loss_despues=log_loss_despues,
        ece_despues=ece_despues,
        n_muestras=len(prob_train) + len(prob_val),
        n_muestras_train=len(prob_train),
        n_muestras_validation=len(prob_val),
        fecha_entrenamiento=datetime.now(),
        parametros=calibrador.parametros,
    )

    return calibrador, resultado


def imprimir_resultado(resultado: ResultadoCalibracion, verbose: bool = False) -> None:
    """Imprime el resultado de calibración formateado."""
    print(f"\n{'='*60}")
    print(f"  CALIBRACIÓN: {resultado.mercado.value}")
    print(f"{'='*60}")
    print(f"\n  Método: {resultado.metodo}")
    print(f"  Muestras: {resultado.n_muestras:,} (train: {resultado.n_muestras_train:,}, "
          f"validation: {resultado.n_muestras_validation:,})")

    print(f"\n  MÉTRICAS ANTES DE CALIBRACIÓN:")
    print(f"    Brier Score: {resultado.brier_antes:.4f}")
    print(f"    Log Loss:    {resultado.log_loss_antes:.4f}")
    print(f"    ECE:         {resultado.ece_antes:.4f}")

    print(f"\n  MÉTRICAS DESPUÉS DE CALIBRACIÓN:")

    # Brier Score con mejora
    mejora_brier = resultado.mejora_brier_porcentual
    signo_brier = "+" if mejora_brier >= 0 else ""
    color_brier = "MEJOR" if mejora_brier > 0 else "PEOR"
    print(f"    Brier Score: {resultado.brier_despues:.4f} ({signo_brier}{mejora_brier:.1f}%) [{color_brier}]")

    # Log Loss con mejora
    if resultado.log_loss_antes > 0:
        mejora_ll = (resultado.log_loss_antes - resultado.log_loss_despues) / resultado.log_loss_antes * 100
    else:
        mejora_ll = 0
    signo_ll = "+" if mejora_ll >= 0 else ""
    print(f"    Log Loss:    {resultado.log_loss_despues:.4f} ({signo_ll}{mejora_ll:.1f}%)")

    # ECE con mejora
    mejora_ece = resultado.mejora_ece_porcentual
    signo_ece = "+" if mejora_ece >= 0 else ""
    print(f"    ECE:         {resultado.ece_despues:.4f} ({signo_ece}{mejora_ece:.1f}%)")

    if verbose:
        print(f"\n  Parámetros: {resultado.parametros}")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Calibración de probabilidades para fútbol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--mercado",
        type=str,
        default="todos",
        help="Mercado específico o 'todos' (default: todos)",
    )
    parser.add_argument(
        "--metodo",
        type=str,
        choices=["platt", "isotonic", "auto"],
        default="auto",
        help="Método de calibración (default: auto)",
    )
    parser.add_argument(
        "--min-muestras",
        type=int,
        default=200,
        help="Mínimo de predicciones para entrenar (default: 200)",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Proporción de datos para entrenamiento (default: 0.8)",
    )
    parser.add_argument(
        "--guardar",
        action="store_true",
        help="Guardar calibrador en BD",
    )
    parser.add_argument(
        "--activar",
        action="store_true",
        help="Activar calibrador si mejora el actual",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Información detallada",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sin guardar",
    )

    args = parser.parse_args()
    if args.min_muestras < 2 or not 0 < args.train_ratio < 1:
        parser.error("min-muestras debe ser >= 2 y train-ratio debe estar entre 0 y 1")
    if args.activar and not args.guardar:
        parser.error("--activar requiere --guardar")
    if args.guardar and args.min_muestras < 200:
        parser.error("guardar requiere al menos 200 muestras por mercado")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "="*60)
    print("  CALIBRACIÓN DE PROBABILIDADES - FÚTBOL")
    print("="*60)

    # Obtener pool de conexiones
    solo_lectura = args.dry_run or not args.guardar
    pool = (
        ConnectionPool(
            conninfo=obtener_database_url(),
            kwargs={"options": "-c default_transaction_read_only=on"},
            min_size=1,
            max_size=2,
            open=True,
        )
        if solo_lectura else obtener_pool()
    )
    if solo_lectura:
        with pool.connection() as conn:
            if conn.execute("SHOW transaction_read_only").fetchone()[0] != "on":
                raise RuntimeError("El modo diagnóstico debe usar una conexión read-only")

    # Determinar mercados a procesar
    if args.mercado.lower() == "todos":
        mercados = obtener_todos_mercados()
    else:
        try:
            mercados = [TipoMercadoFutbol(args.mercado.upper())]
        except ValueError:
            print(f"\nError: Mercado desconocido: {args.mercado}")
            print("Mercados válidos:")
            for m in obtener_todos_mercados():
                print(f"  - {m.value}")
            sys.exit(1)

    # Gestor para guardar calibradores
    gestor = GestorCalibradores(pool)

    # Procesar cada mercado
    resultados_totales = []

    for mercado in mercados:
        print(f"\n--- Procesando {mercado.value} ---")

        # Obtener datos
        prob_raw, outcomes, fechas_partido = obtener_datos_calibracion(pool, mercado)
        n_total = len(prob_raw)

        if n_total < args.min_muestras:
            print(f"  Saltando: solo {n_total} muestras (mínimo: {args.min_muestras})")
            continue

        print(f"  Datos encontrados: {n_total}")

        # Dividir en train/validation
        try:
            prob_train, out_train, prob_val, out_val, cutoff_datos = dividir_train_validation(
                prob_raw, outcomes, fechas_partido, args.train_ratio
            )
        except ValueError as exc:
            print(f"  Saltando: {exc}")
            continue

        # Determinar métodos a probar
        if args.metodo == "auto":
            metodos = ["platt", "isotonic"]
        else:
            metodos = [args.metodo]

        mejores: Dict[str, Tuple[Any, ResultadoCalibracion]] = {}

        for metodo in metodos:
            try:
                calibrador, resultado = entrenar_calibrador(
                    mercado, prob_train, out_train, prob_val, out_val, metodo
                )
                mejores[metodo] = (calibrador, resultado)

                if args.verbose or len(metodos) > 1:
                    imprimir_resultado(resultado, args.verbose)

            except Exception as e:
                logger.error(f"Error entrenando {metodo} para {mercado.value}: {e}")

        if not mejores:
            print(f"  No se pudo entrenar ningún calibrador")
            continue

        # Seleccionar el mejor por Brier Score
        mejor_metodo = min(mejores.keys(), key=lambda m: mejores[m][1].brier_despues)
        mejor_calibrador, mejor_resultado = mejores[mejor_metodo]

        if args.metodo == "auto":
            print(f"\n  Mejor método: {mejor_metodo}")

        imprimir_resultado(mejor_resultado, args.verbose)
        resultados_totales.append(mejor_resultado)

        # Guardar si se solicita
        if args.guardar and not args.dry_run:
            try:
                calibrador_id = gestor.guardar_calibrador(
                    mejor_calibrador,
                    mejor_resultado,
                    cutoff_datos=cutoff_datos,
                    notas=f"Calibrado con {mejor_resultado.n_muestras} muestras",
                )
                print(f"\n  Calibrador guardado: {calibrador_id}")

                # Activar si se solicita
                if args.activar:
                    if mejor_resultado.mejora_brier_porcentual > 0:
                        activado = gestor.activar_calibrador(calibrador_id, validar_mejora=True)
                        if activado:
                            print(f"  Calibrador activado")
                        else:
                            print(f"  No activado (no mejora el actual)")
                    else:
                        print(f"  No activado (Brier Score empeoró)")

            except Exception as e:
                logger.error(f"Error guardando calibrador: {e}")

        elif args.dry_run:
            print(f"\n  [DRY-RUN] No se guardó el calibrador")

    # Resumen final
    if resultados_totales:
        print("\n" + "="*60)
        print("  RESUMEN FINAL")
        print("="*60)
        print(f"\n  Mercados calibrados: {len(resultados_totales)}")

        mejora_promedio = np.mean([r.mejora_brier_porcentual for r in resultados_totales])
        print(f"  Mejora Brier promedio: {mejora_promedio:+.2f}%")

        ece_promedio_antes = np.mean([r.ece_antes for r in resultados_totales])
        ece_promedio_despues = np.mean([r.ece_despues for r in resultados_totales])
        print(f"  ECE promedio: {ece_promedio_antes:.4f} -> {ece_promedio_despues:.4f}")

    print("\n" + "="*60 + "\n")
    if solo_lectura:
        pool.close()


if __name__ == "__main__":
    main()
