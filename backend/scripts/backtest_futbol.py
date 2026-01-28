#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtest_futbol.py — Script de backtesting para el motor de predicción de fútbol.

Implementa walk-forward validation para evaluar el rendimiento histórico
de los modelos de predicción sin data leakage.

Uso:
    python backtest_futbol.py --inicio 2024-01-01 --fin 2024-03-31 [opciones]

Opciones:
    --inicio        Fecha de inicio del backtest (YYYY-MM-DD)
    --fin           Fecha de fin del backtest (YYYY-MM-DD)
    --step          Días entre re-entrenamientos (default: 7)
    --umbral-edge   Edge mínimo para apostar (default: 0.05)
    --kelly         Fracción de Kelly (default: 0.25)
    --mercados      Mercados a evaluar (default: todos)
    --output        Archivo de salida para el reporte (default: backtest_report.json)
    --verbose       Mostrar información detallada

Ejemplo:
    python backtest_futbol.py --inicio 2024-01-01 --fin 2024-03-31 --step 7 --verbose
"""

import sys
import os
import argparse
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psycopg_pool import ConnectionPool

from motor_futbol.evaluacion.backtesting import (
    BacktesterFutbol,
    ConfiguracionBacktest,
    ResultadoBacktest,
    ReporteBacktest,
)
from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.prediccion.predictor import PredictorFutbol
from motor_futbol.tipos import TipoMercadoFutbol
from motor_futbol.constantes import ALPHA_RIDGE_DEFAULT


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backtest_futbol.log"),
    ],
)
logger = logging.getLogger(__name__)


def obtener_pool() -> ConnectionPool:
    """Obtiene el pool de conexiones a la base de datos."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/analyticspredict"
    )
    return ConnectionPool(database_url, min_size=1, max_size=5)


def parsear_fecha(fecha_str: str) -> date:
    """Convierte string a date."""
    return datetime.strptime(fecha_str, "%Y-%m-%d").date()


def parsear_mercados(mercados_str: Optional[str]) -> Optional[List[TipoMercadoFutbol]]:
    """Convierte string de mercados a lista de TipoMercadoFutbol."""
    if not mercados_str:
        return None  # Todos los mercados

    mercados = []
    for m in mercados_str.split(","):
        m = m.strip().upper()
        try:
            mercados.append(TipoMercadoFutbol(m.lower()))
        except ValueError:
            logger.warning(f"Mercado desconocido: {m}")

    return mercados if mercados else None


def imprimir_progreso(ventana: int, total: int, fecha: date) -> None:
    """Imprime el progreso del backtest."""
    porcentaje = (ventana / total) * 100
    barra = "█" * int(porcentaje / 2) + "░" * (50 - int(porcentaje / 2))
    print(f"\r  [{barra}] {porcentaje:.1f}% - Evaluando {fecha}", end="", flush=True)


def imprimir_resumen_metricas(resultado: ResultadoBacktest) -> None:
    """Imprime resumen de métricas del backtest."""
    metricas = resultado.metricas_rentabilidad
    calibracion = resultado.metricas_calibracion

    print(f"\n{'='*60}")
    print(f"  RESULTADOS DEL BACKTEST")
    print(f"{'='*60}")

    print(f"\n  Período: {resultado.config.fecha_inicio} a {resultado.config.fecha_fin}")
    print(f"  Total predicciones: {len(resultado.predicciones)}")
    print(f"  Total apuestas: {len(resultado.apuestas)}")

    print(f"\n  MÉTRICAS DE RENTABILIDAD:")
    print(f"    - ROI:        {metricas.get('roi', 0)*100:.2f}%")
    print(f"    - Win Rate:   {metricas.get('win_rate', 0)*100:.2f}%")
    print(f"    - Yield:      {metricas.get('yield', 0)*100:.2f}%")
    print(f"    - Beneficio:  {metricas.get('beneficio_neto', 0):.2f} unidades")

    print(f"\n  MÉTRICAS DE CALIBRACIÓN:")
    print(f"    - Brier Score: {calibracion.get('brier_score', 'N/A'):.4f}")
    print(f"    - ECE:         {calibracion.get('ece', 'N/A'):.4f}")
    print(f"    - MCE:         {calibracion.get('mce', 'N/A'):.4f}")

    # Verificar objetivos
    print(f"\n  VERIFICACIÓN DE OBJETIVOS:")

    brier = calibracion.get('brier_score', 1.0)
    roi = metricas.get('roi', -1)

    if brier < 0.25:
        print(f"    ✓ Brier Score < 0.25 ({brier:.4f})")
    else:
        print(f"    ✗ Brier Score >= 0.25 ({brier:.4f})")

    if roi > 0:
        print(f"    ✓ ROI > 0% ({roi*100:.2f}%)")
    else:
        print(f"    ✗ ROI <= 0% ({roi*100:.2f}%)")


def imprimir_metricas_por_mercado(resultado: ResultadoBacktest) -> None:
    """Imprime métricas desglosadas por mercado."""
    print(f"\n  MÉTRICAS POR MERCADO:")
    print(f"  {'-'*56}")
    print(f"  {'Mercado':<25} {'ROI':>10} {'Win Rate':>10} {'Apuestas':>10}")
    print(f"  {'-'*56}")

    for mercado, metricas in sorted(resultado.metricas_por_mercado.items()):
        roi = metricas.get('roi', 0) * 100
        win_rate = metricas.get('win_rate', 0) * 100
        n_apuestas = metricas.get('n_apuestas', 0)

        print(f"  {mercado:<25} {roi:>9.2f}% {win_rate:>9.2f}% {n_apuestas:>10}")

    print(f"  {'-'*56}")


def guardar_reporte(resultado: ResultadoBacktest, output_path: str) -> None:
    """Guarda el reporte del backtest en formato JSON."""
    reporte = ReporteBacktest.generar(resultado)

    reporte_dict = {
        "resumen": reporte.resumen,
        "metricas_por_mercado": reporte.metricas_por_mercado,
        "curva_equity": reporte.curva_equity,
        "periodo": {
            "inicio": resultado.config.fecha_inicio.isoformat(),
            "fin": resultado.config.fecha_fin.isoformat(),
        },
        "configuracion": {
            "step_dias": resultado.config.step_dias,
            "umbral_edge": resultado.config.umbral_edge,
            "fraccion_kelly": resultado.config.fraccion_kelly,
        },
        "timestamp": datetime.now().isoformat(),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reporte_dict, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"Reporte guardado en: {output_path}")


def ejecutar_backtest(
    pool: ConnectionPool,
    config: ConfiguracionBacktest,
    mercados: Optional[List[TipoMercadoFutbol]] = None,
    verbose: bool = False,
) -> ResultadoBacktest:
    """
    Ejecuta el backtest walk-forward.

    Args:
        pool: Pool de conexiones a la base de datos
        config: Configuración del backtest
        mercados: Lista de mercados a evaluar (None = todos)
        verbose: Si mostrar información detallada

    Returns:
        Resultado del backtest
    """
    logger.info(f"Iniciando backtest: {config.fecha_inicio} - {config.fecha_fin}")

    entrenador = EntrenadorFutbol(pool=pool, alpha=ALPHA_RIDGE_DEFAULT)
    predictor = PredictorFutbol(pool=pool)

    backtester = BacktesterFutbol(
        pool=pool,
        entrenador=entrenador,
        predictor=predictor,
    )

    if mercados:
        config.mercados_filtro = mercados

    # Callback de progreso
    def callback_progreso(ventana: int, total: int, fecha: date):
        if verbose:
            imprimir_progreso(ventana, total, fecha)

    resultado = backtester.ejecutar(config, callback_progreso=callback_progreso)

    if verbose:
        print()  # Nueva línea después de la barra de progreso

    logger.info("Backtest completado")

    return resultado


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Backtest del motor de predicción de fútbol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--inicio",
        type=str,
        required=True,
        help="Fecha de inicio del backtest (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--fin",
        type=str,
        required=True,
        help="Fecha de fin del backtest (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--step",
        type=int,
        default=7,
        help="Días entre re-entrenamientos (default: 7)",
    )

    parser.add_argument(
        "--umbral-edge",
        type=float,
        default=0.05,
        help="Edge mínimo para apostar (default: 0.05)",
    )

    parser.add_argument(
        "--kelly",
        type=float,
        default=0.25,
        help="Fracción de Kelly (default: 0.25)",
    )

    parser.add_argument(
        "--mercados",
        type=str,
        default=None,
        help="Mercados a evaluar, separados por coma (default: todos)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="backtest_report.json",
        help="Archivo de salida para el reporte (default: backtest_report.json)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar información detallada",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parsear fechas
    fecha_inicio = parsear_fecha(args.inicio)
    fecha_fin = parsear_fecha(args.fin)

    if fecha_inicio >= fecha_fin:
        print("❌ Error: La fecha de inicio debe ser anterior a la fecha de fin")
        sys.exit(1)

    # Parsear mercados
    mercados = parsear_mercados(args.mercados)

    print("\n" + "="*60)
    print("  MOTOR DE PREDICCIÓN DE FÚTBOL - BACKTEST")
    print("="*60)
    print(f"  Fecha ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Período: {fecha_inicio} a {fecha_fin}")
    print(f"  Step: {args.step} días")
    print(f"  Umbral edge: {args.umbral_edge*100:.1f}%")
    print(f"  Fracción Kelly: {args.kelly*100:.0f}%")
    print(f"  Mercados: {'Todos' if not mercados else ', '.join(m.value for m in mercados)}")
    print("="*60 + "\n")

    try:
        pool = obtener_pool()

        # Configurar backtest
        config = ConfiguracionBacktest(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            step_dias=args.step,
            umbral_edge=args.umbral_edge,
            fraccion_kelly=args.kelly,
        )

        # Ejecutar backtest
        print("  Ejecutando backtest walk-forward...")
        resultado = ejecutar_backtest(
            pool=pool,
            config=config,
            mercados=mercados,
            verbose=args.verbose,
        )

        # Mostrar resultados
        imprimir_resumen_metricas(resultado)

        if args.verbose:
            imprimir_metricas_por_mercado(resultado)

        # Guardar reporte
        guardar_reporte(resultado, args.output)
        print(f"\n  📄 Reporte guardado en: {args.output}")

        print("\n" + "="*60 + "\n")

    except Exception as e:
        logger.exception("Error durante el backtest")
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
