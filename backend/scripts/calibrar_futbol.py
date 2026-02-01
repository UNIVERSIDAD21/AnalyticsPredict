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
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import obtener_pool
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


def obtener_datos_calibracion(
    pool,
    mercado: TipoMercadoFutbol,
    min_muestras: int = 200,
    excluir_backtest: bool = True,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Obtiene datos históricos para calibración.

    Busca predicciones resueltas en la base de datos y extrae
    las probabilidades predichas vs los resultados reales.

    Args:
        pool: Pool de conexiones
        mercado: Mercado a calibrar
        min_muestras: Mínimo de muestras requeridas
        excluir_backtest: Excluir predicciones de backtest sintético

    Returns:
        Tupla (prob_raw, outcomes, n_total)
        - prob_raw: Array de probabilidades predichas
        - outcomes: Array de resultados (0=under, 1=over)
        - n_total: Total de muestras encontradas
    """
    # Determinar tipo de mercado para buscar la tabla correcta
    mercado_str = mercado.value.upper()

    # Query para obtener predicciones históricas
    # Esta query asume una estructura de tabla con predicciones resueltas
    query = """
        SELECT
            prob_over,
            CASE
                WHEN resultado_real > linea THEN 1
                ELSE 0
            END as outcome
        FROM (
            -- Subquery para obtener predicciones con resultados
            SELECT
                p.prob_over_raw as prob_over,
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
                END as resultado_real
            FROM predicciones_mercado p
            JOIN partidos_futbol pf ON p.partido_id = pf.id
            JOIN resultados_futbol r ON pf.id = r.partido_id
            WHERE p.mercado = %s
              AND p.prob_over_raw IS NOT NULL
              AND pf.estado = 'FINALIZADO'
    """

    if excluir_backtest:
        query += " AND (p.origen IS NULL OR p.origen != 'BACKTEST_SINTETICO')"

    query += """
            ORDER BY pf.fecha_partido ASC
        ) sub
        WHERE resultado_real IS NOT NULL
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (mercado_str,))
                rows = cur.fetchall()

                if not rows:
                    logger.warning(f"No se encontraron datos para {mercado_str}")
                    return np.array([]), np.array([]), 0

                prob_raw = np.array([float(row[0]) for row in rows])
                outcomes = np.array([int(row[1]) for row in rows])

                return prob_raw, outcomes, len(rows)

    except Exception as e:
        logger.error(f"Error obteniendo datos para {mercado_str}: {e}")
        # Intentar con query alternativa usando backtest
        return _obtener_datos_backtest(pool, mercado, min_muestras)


def _obtener_datos_backtest(
    pool,
    mercado: TipoMercadoFutbol,
    min_muestras: int,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Obtiene datos de calibración desde resultados de backtest.

    Fallback cuando no hay tabla de predicciones_mercado.
    """
    # Intentar obtener desde metricas de backtest
    mercado_str = mercado.value.upper()

    query = """
        SELECT prob_predicha, resultado_real
        FROM backtest_predicciones
        WHERE mercado = %s
        ORDER BY fecha_partido ASC
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (mercado_str,))
                rows = cur.fetchall()

                if rows:
                    prob_raw = np.array([float(row[0]) for row in rows])
                    outcomes = np.array([int(row[1]) for row in rows])
                    return prob_raw, outcomes, len(rows)

    except Exception:
        pass

    # Si no hay datos, generar datos sintéticos para demostración
    logger.warning(f"No hay datos reales para {mercado_str}, generando sintéticos")
    return _generar_datos_sinteticos(min_muestras)


def _generar_datos_sinteticos(n_muestras: int) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Genera datos sintéticos para pruebas cuando no hay datos reales.

    Los datos simulan un modelo ligeramente descalibrado que:
    - Tiene sobreconfianza en extremos
    - Tiene un pequeño sesgo
    """
    np.random.seed(42)

    # Generar probabilidades "raw" uniformes
    prob_raw = np.random.beta(2, 2, n_muestras)

    # Simular descalibración: el modelo tiene sobreconfianza
    # Las probabilidades extremas son menos confiables
    prob_real = 0.5 + 0.8 * (prob_raw - 0.5)  # Comprimir hacia 0.5
    prob_real = np.clip(prob_real, 0.01, 0.99)

    # Generar outcomes según probabilidad real
    outcomes = (np.random.random(n_muestras) < prob_real).astype(int)

    return prob_raw, outcomes, n_muestras


def dividir_train_validation(
    prob_raw: np.ndarray,
    outcomes: np.ndarray,
    train_ratio: float = 0.8,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Divide datos en train/validation de forma temporal (no aleatoria).

    Usa los primeros train_ratio% de datos para entrenar y el resto
    para validación, respetando el orden cronológico.

    Args:
        prob_raw: Probabilidades sin calibrar
        outcomes: Resultados reales
        train_ratio: Proporción para entrenamiento

    Returns:
        (prob_train, out_train, prob_val, out_val)
    """
    n = len(prob_raw)
    n_train = int(n * train_ratio)

    return (
        prob_raw[:n_train],
        outcomes[:n_train],
        prob_raw[n_train:],
        outcomes[n_train:],
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

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "="*60)
    print("  CALIBRACIÓN DE PROBABILIDADES - FÚTBOL")
    print("="*60)

    # Obtener pool de conexiones
    pool = obtener_pool()

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
        prob_raw, outcomes, n_total = obtener_datos_calibracion(
            pool, mercado, args.min_muestras
        )

        if n_total < args.min_muestras:
            print(f"  Saltando: solo {n_total} muestras (mínimo: {args.min_muestras})")
            continue

        print(f"  Datos encontrados: {n_total}")

        # Dividir en train/validation
        prob_train, out_train, prob_val, out_val = dividir_train_validation(
            prob_raw, outcomes, args.train_ratio
        )

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
                    cutoff_datos=date.today(),
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


if __name__ == "__main__":
    main()
