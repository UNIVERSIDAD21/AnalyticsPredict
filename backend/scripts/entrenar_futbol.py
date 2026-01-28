#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entrenar_futbol.py — Script de entrenamiento para el motor de predicción de fútbol.

Uso:
    python entrenar_futbol.py [--alpha ALPHA] [--min-partidos N] [--guardar]

Opciones:
    --alpha         Parámetro de regularización Ridge (default: 5.0)
    --min-partidos  Número mínimo de partidos para entrenar (default: 100)
    --guardar       Guardar modelos entrenados en la base de datos
    --validar       Ejecutar validación cruzada temporal
    --verbose       Mostrar información detallada

Ejemplo:
    python entrenar_futbol.py --alpha 5.0 --min-partidos 200 --guardar --validar
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psycopg_pool import ConnectionPool

from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.entrenamiento.gestor_versiones import GestorVersiones
from motor_futbol.tipos import TipoModelo, ResultadoEntrenamiento
from motor_futbol.constantes import ALPHA_RIDGE_DEFAULT
from motor_futbol.excepciones import DatosInsuficientes


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("entrenamiento_futbol.log"),
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


def imprimir_metricas(resultado: ResultadoEntrenamiento, tipo: str) -> None:
    """Imprime las métricas de entrenamiento de forma formateada."""
    print(f"\n{'='*60}")
    print(f"  MODELO: {tipo.upper()}")
    print(f"{'='*60}")

    metricas = resultado.metricas

    print(f"\n  Métricas de Regresión:")
    print(f"    - MAE:    {metricas.get('mae', 'N/A'):.4f}")
    print(f"    - RMSE:   {metricas.get('rmse', 'N/A'):.4f}")
    print(f"    - R²:     {metricas.get('r2', 'N/A'):.4f}")

    if "brier_score" in metricas:
        print(f"\n  Métricas de Calibración:")
        print(f"    - Brier Score: {metricas.get('brier_score', 'N/A'):.4f}")
        print(f"    - ECE:         {metricas.get('ece', 'N/A'):.4f}")

    print(f"\n  Información del Modelo:")
    print(f"    - Partidos utilizados: {resultado.n_partidos}")
    print(f"    - Equipos:             {resultado.n_equipos}")
    print(f"    - Alpha Ridge:         {resultado.alpha}")
    print(f"    - Fecha entrenamiento: {resultado.fecha_entrenamiento}")


def entrenar_modelos(
    pool: ConnectionPool,
    alpha: float,
    min_partidos: int,
    validar: bool = False,
    verbose: bool = False,
) -> Dict[str, ResultadoEntrenamiento]:
    """
    Entrena todos los modelos del motor de fútbol.

    Args:
        pool: Pool de conexiones a la base de datos
        alpha: Parámetro de regularización Ridge
        min_partidos: Número mínimo de partidos requeridos
        validar: Si ejecutar validación cruzada temporal
        verbose: Si mostrar información detallada

    Returns:
        Diccionario con resultados de entrenamiento por tipo de modelo
    """
    logger.info(f"Iniciando entrenamiento con alpha={alpha}, min_partidos={min_partidos}")

    entrenador = EntrenadorFutbol(
        pool=pool,
        alpha=alpha,
        min_partidos=min_partidos,
    )

    try:
        # Entrenar todos los modelos
        resultados = entrenador.entrenar_completo(validar_temporal=validar)

        logger.info(f"Entrenamiento completado exitosamente")

        # Mostrar métricas
        for tipo, resultado in resultados.items():
            imprimir_metricas(resultado, tipo)

        return resultados

    except DatosInsuficientes as e:
        logger.error(f"Datos insuficientes para entrenar: {e}")
        raise


def guardar_modelos(
    pool: ConnectionPool,
    resultados: Dict[str, ResultadoEntrenamiento],
) -> str:
    """
    Guarda los modelos entrenados en la base de datos.

    Args:
        pool: Pool de conexiones
        resultados: Resultados del entrenamiento

    Returns:
        Versión asignada a los modelos
    """
    gestor = GestorVersiones(pool=pool)
    version = gestor.generar_version()

    logger.info(f"Guardando modelos con versión: {version}")

    for tipo_str, resultado in resultados.items():
        tipo = TipoModelo(tipo_str)

        gestor.guardar_modelo(
            modelo=resultado.modelo,
            tipo=tipo,
            version=version,
            metricas=resultado.metricas,
        )

        logger.info(f"Modelo {tipo.value} guardado correctamente")

    # Marcar como versión activa
    gestor.activar_version(version)

    print(f"\n{'='*60}")
    print(f"  MODELOS GUARDADOS")
    print(f"{'='*60}")
    print(f"  Versión: {version}")
    print(f"  Modelos: {', '.join(resultados.keys())}")
    print(f"{'='*60}\n")

    return version


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Entrenar modelos de predicción de fútbol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--alpha",
        type=float,
        default=ALPHA_RIDGE_DEFAULT,
        help=f"Parámetro de regularización Ridge (default: {ALPHA_RIDGE_DEFAULT})",
    )

    parser.add_argument(
        "--min-partidos",
        type=int,
        default=100,
        help="Número mínimo de partidos para entrenar (default: 100)",
    )

    parser.add_argument(
        "--guardar",
        action="store_true",
        help="Guardar modelos entrenados en la base de datos",
    )

    parser.add_argument(
        "--validar",
        action="store_true",
        help="Ejecutar validación cruzada temporal",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar información detallada",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "="*60)
    print("  MOTOR DE PREDICCIÓN DE FÚTBOL - ENTRENAMIENTO")
    print("="*60)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Alpha: {args.alpha}")
    print(f"  Min. partidos: {args.min_partidos}")
    print(f"  Validación temporal: {'Sí' if args.validar else 'No'}")
    print(f"  Guardar modelos: {'Sí' if args.guardar else 'No'}")
    print("="*60 + "\n")

    try:
        pool = obtener_pool()

        # Entrenar modelos
        resultados = entrenar_modelos(
            pool=pool,
            alpha=args.alpha,
            min_partidos=args.min_partidos,
            validar=args.validar,
            verbose=args.verbose,
        )

        # Guardar si se solicita
        if args.guardar:
            version = guardar_modelos(pool, resultados)
            logger.info(f"Modelos guardados con versión: {version}")

        # Resumen final
        print("\n" + "="*60)
        print("  RESUMEN DE ENTRENAMIENTO")
        print("="*60)

        for tipo, resultado in resultados.items():
            print(f"\n  {tipo}:")
            print(f"    MAE: {resultado.metricas.get('mae', 'N/A'):.4f}")

            # Verificar objetivos
            mae = resultado.metricas.get('mae', float('inf'))
            if tipo == TipoModelo.CORNERS.value and mae < 2.5:
                print(f"    ✓ MAE < 2.5 (objetivo cumplido)")
            elif tipo == TipoModelo.GOLES.value and mae < 1.0:
                print(f"    ✓ MAE < 1.0 (objetivo cumplido)")

        print("\n" + "="*60 + "\n")

    except DatosInsuficientes as e:
        print(f"\n❌ Error: Datos insuficientes para entrenar")
        print(f"   Detalles: {e}")
        sys.exit(1)

    except Exception as e:
        logger.exception("Error durante el entrenamiento")
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
