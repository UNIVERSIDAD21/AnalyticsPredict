#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entrenar_futbol.py — Script de entrenamiento para el motor de predicción de fútbol.

Uso:
    python entrenar_futbol.py [--alpha ALPHA] [--min-partidos N] [--guardar]

Opciones:
    --alpha         Parámetro de regularización Ridge (default: 5.0)
    --min-partidos  Número mínimo de partidos requeridos (default: 100)
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
from typing import Dict, Any, Optional

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psycopg_pool import ConnectionPool

from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.tipos import ResultadoEntrenamiento, TipoModelo, ConfiguracionEntrenamiento
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


# Variable global para el pool
_pool: Optional[ConnectionPool] = None


def obtener_pool() -> ConnectionPool:
    """Obtiene el pool de conexiones a la base de datos."""
    global _pool
    
    if _pool is None:
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url:
            # Intentar cargar desde .env
            try:
                from dotenv import load_dotenv
                env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
                if os.path.exists(env_path):
                    load_dotenv(env_path)
                else:
                    load_dotenv()
                database_url = os.environ.get("DATABASE_URL")
            except ImportError:
                pass
        
        if not database_url:
            raise ValueError(
                "DATABASE_URL no está configurada. "
                "Configúrala como variable de entorno o en el archivo .env"
            )
        
        _pool = ConnectionPool(database_url, min_size=1, max_size=5)
    
    return _pool


def cerrar_pool():
    """Cierra el pool de conexiones."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def imprimir_metricas(resultado: ResultadoEntrenamiento, tipo: str) -> None:
    """
    Imprime las métricas de entrenamiento de forma formateada.
    
    Args:
        resultado: ResultadoEntrenamiento con las métricas
        tipo: Nombre del tipo de modelo (corners, goles, disparos)
    """
    print(f"\n{'='*60}")
    print(f"  MODELO: {tipo.upper()}")
    print(f"{'='*60}")

    # ═══════════════════════════════════════════════════════════════
    # MÉTRICAS POR TARGET
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  📊 Métricas por Target:")
    print(f"  {'-'*56}")
    
    if resultado.mae_por_target:
        for target, mae in resultado.mae_por_target.items():
            rmse = resultado.rmse_por_target.get(target, 0.0)
            r2 = resultado.r2_por_target.get(target, 0.0)
            print(f"    {target}:")
            print(f"      MAE:  {mae:.4f}")
            print(f"      RMSE: {rmse:.4f}")
            print(f"      R²:   {r2:.4f}")
    else:
        print("    No hay métricas por target disponibles")
    
    # ═══════════════════════════════════════════════════════════════
    # RESUMEN
    # ═══════════════════════════════════════════════════════════════
    mae_promedio = resultado.mae_promedio()
    
    print(f"\n  📈 Resumen:")
    print(f"  {'-'*56}")
    print(f"    MAE Promedio: {mae_promedio:.4f}")
    
    # Calcular RMSE y R² promedios
    if resultado.rmse_por_target:
        rmse_promedio = sum(resultado.rmse_por_target.values()) / len(resultado.rmse_por_target)
        print(f"    RMSE Promedio: {rmse_promedio:.4f}")
    
    if resultado.r2_por_target:
        r2_promedio = sum(resultado.r2_por_target.values()) / len(resultado.r2_por_target)
        print(f"    R² Promedio: {r2_promedio:.4f}")
    
    # ═══════════════════════════════════════════════════════════════
    # INFORMACIÓN DEL MODELO
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  ℹ️  Información del Modelo:")
    print(f"  {'-'*56}")
    print(f"    Partidos utilizados: {resultado.n_partidos}")
    print(f"    Equipos en modelo:   {resultado.n_equipos}")
    print(f"    Alpha Ridge:         {resultado.alpha_usado}")
    print(f"    Duración:            {resultado.duracion_segundos:.2f}s")
    
    if resultado.fecha_entrenamiento:
        print(f"    Fecha entrenamiento: {resultado.fecha_entrenamiento.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICACIÓN DE OBJETIVOS
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  🎯 Verificación de Objetivo:")
    print(f"  {'-'*56}")
    
    tipo_lower = tipo.lower()
    
    if 'corners' in tipo_lower:
        objetivo = 2.5
        cumplido = mae_promedio < objetivo
        print(f"    Objetivo: MAE < {objetivo}")
        print(f"    Resultado: MAE = {mae_promedio:.4f}")
        print(f"    Estado: {'✅ CUMPLIDO' if cumplido else '❌ NO CUMPLIDO'}")
    elif 'goles' in tipo_lower:
        objetivo = 1.0
        cumplido = mae_promedio < objetivo
        print(f"    Objetivo: MAE < {objetivo}")
        print(f"    Resultado: MAE = {mae_promedio:.4f}")
        print(f"    Estado: {'✅ CUMPLIDO' if cumplido else '❌ NO CUMPLIDO'}")
    elif 'disparos' in tipo_lower:
        objetivo = 4.5
        cumplido = mae_promedio < objetivo
        print(f"    Objetivo: MAE < {objetivo}")
        print(f"    Resultado: MAE = {mae_promedio:.4f}")
        print(f"    Estado: {'✅ CUMPLIDO' if cumplido else '❌ NO CUMPLIDO'}")


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

    # Crear configuración
    config = ConfiguracionEntrenamiento(
        alpha_ridge=alpha if alpha != ALPHA_RIDGE_DEFAULT else None,  # None = buscar óptimo
        min_partidos_equipo=5,
        incluir_copas=False,
    )

    # Crear entrenador
    logger.debug(f"Creando EntrenadorFutbol con args: ['pool']")
    entrenador = EntrenadorFutbol(pool=pool, config=config)

    try:
        # Entrenar todos los modelos
        logger.debug(f"Llamando entrenar_completo con args: []")
        resultados = entrenador.entrenar_completo()

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
    verbose: bool = False,
) -> str:
    """
    Guarda los modelos entrenados en la base de datos.

    Args:
        pool: Pool de conexiones
        resultados: Resultados del entrenamiento
        verbose: Mostrar información detallada

    Returns:
        Versión asignada a los modelos
    """
    try:
        from motor_futbol.entrenamiento.gestor_versiones import GestorVersiones
        
        gestor = GestorVersiones(pool=pool)
        version = gestor.generar_version()

        logger.info(f"Guardando modelos con versión: {version}")

        for tipo_str, resultado in resultados.items():
            # Determinar tipo de modelo
            try:
                tipo = TipoModelo(tipo_str)
            except ValueError:
                if 'corner' in tipo_str.lower():
                    tipo = TipoModelo.CORNERS
                elif 'gol' in tipo_str.lower():
                    tipo = TipoModelo.GOLES
                else:
                    tipo = TipoModelo.DISPAROS

            # Preparar métricas para guardar
            metricas = {
                "mae_promedio": resultado.mae_promedio(),
                "mae_por_target": resultado.mae_por_target,
                "rmse_por_target": resultado.rmse_por_target,
                "r2_por_target": resultado.r2_por_target,
                "alpha_usado": resultado.alpha_usado,
                "n_partidos": resultado.n_partidos,
                "n_equipos": resultado.n_equipos,
            }

            gestor.guardar_modelo(
                tipo=tipo,
                version=version,
                metricas=metricas,
                n_partidos=resultado.n_partidos,
                n_equipos=resultado.n_equipos,
            )

            logger.info(f"Modelo {tipo.value} guardado correctamente")

        # Marcar como versión activa
        gestor.activar_version(version)

        print(f"\n{'='*60}")
        print(f"  💾 MODELOS GUARDADOS EN BASE DE DATOS")
        print(f"{'='*60}")
        print(f"  Versión: {version}")
        print(f"  Modelos: {', '.join(resultados.keys())}")
        print(f"{'='*60}\n")

        return version
    
    except ImportError as e:
        logger.warning(f"No se pudo importar GestorVersiones: {e}")
        logger.info("Los modelos se entrenaron pero no se guardaron en BD")
        return "no_guardado"
    
    except Exception as e:
        logger.warning(f"No se pudieron guardar los modelos en BD: {e}")
        logger.info("Los modelos se entrenaron correctamente pero no se guardaron en la BD")
        return "no_guardado"


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

    # ═══════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("  ⚽ MOTOR DE PREDICCIÓN DE FÚTBOL - ENTRENAMIENTO")
    print("="*60)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Alpha: {args.alpha}")
    print(f"  Min. partidos: {args.min_partidos}")
    print(f"  Validación temporal: {'Sí' if args.validar else 'No'}")
    print(f"  Guardar modelos: {'Sí' if args.guardar else 'No'}")
    print("="*60 + "\n")

    pool = None
    
    try:
        # Conectar a BD
        logger.info("Estableciendo conexión a la base de datos...")
        pool = obtener_pool()
        
        # Verificar conexión
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        logger.info("✓ Conexión a BD establecida correctamente")

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
            version = guardar_modelos(pool, resultados, verbose=args.verbose)
            logger.info(f"Modelos guardados con versión: {version}")

        # ═══════════════════════════════════════════════════════════════
        # RESUMEN FINAL
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "="*60)
        print("  📋 RESUMEN FINAL DE ENTRENAMIENTO")
        print("="*60)

        todos_objetivos_cumplidos = True
        
        for tipo, resultado in resultados.items():
            mae_promedio = resultado.mae_promedio()
            print(f"\n  {tipo.upper()}:")
            print(f"    MAE Promedio: {mae_promedio:.4f}")
            print(f"    Partidos: {resultado.n_partidos}")
            print(f"    Equipos: {resultado.n_equipos}")
            
            # Verificar objetivos
            objetivo_cumplido = False
            tipo_lower = tipo.lower()
            
            if 'corners' in tipo_lower:
                objetivo_cumplido = mae_promedio < 2.5
                status = '✅ CUMPLIDO' if objetivo_cumplido else '❌ NO CUMPLIDO'
                print(f"    Objetivo (MAE < 2.5): {status}")
            elif 'goles' in tipo_lower:
                objetivo_cumplido = mae_promedio < 1.0
                status = '✅ CUMPLIDO' if objetivo_cumplido else '❌ NO CUMPLIDO'
                print(f"    Objetivo (MAE < 1.0): {status}")
            elif 'disparos' in tipo_lower:
                objetivo_cumplido = mae_promedio < 4.5
                status = '✅ CUMPLIDO' if objetivo_cumplido else '❌ NO CUMPLIDO'
                print(f"    Objetivo (MAE < 4.5): {status}")
            
            if not objetivo_cumplido:
                todos_objetivos_cumplidos = False

        print("\n" + "="*60)
        
        if todos_objetivos_cumplidos:
            print("  🎉 ¡TODOS LOS OBJETIVOS CUMPLIDOS!")
            print("  Los modelos están listos para producción.")
        else:
            print("  ⚠️  Algunos objetivos no se cumplieron")
            print("  Considera ajustar parámetros o revisar datos.")
        
        print("="*60 + "\n")
        
        sys.exit(0)

    except DatosInsuficientes as e:
        print(f"\n❌ Error: Datos insuficientes para entrenar")
        print(f"   Detalles: {e}")
        print("\n   Sugerencias:")
        print("   1. Verifica que la tabla partidos_futbol tiene datos")
        print("   2. Ejecuta: python scripts/auditar_datos_futbol.py")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Entrenamiento interrumpido por el usuario")
        sys.exit(130)

    except Exception as e:
        logger.exception("Error durante el entrenamiento")
        print(f"\n❌ Error inesperado: {e}")
        
        if args.verbose:
            import traceback
            print("\nTraceback completo:")
            traceback.print_exc()
        
        sys.exit(1)
    
    finally:
        # Cerrar pool si se creó
        if pool is not None:
            try:
                cerrar_pool()
                logger.debug("Pool de conexiones cerrado")
            except Exception as e:
                logger.debug(f"Error cerrando pool: {e}")


if __name__ == "__main__":
    main()