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
import inspect
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Configurar encoding UTF-8 para evitar problemas en Windows
if sys.platform == 'win32':
    # Configurar stdout y stderr para UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar el pool de conexiones del módulo db del proyecto
from db import obtener_pool, cerrar_pool

from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.entrenamiento.gestor_versiones import GestorVersiones
from motor_futbol.tipos import TipoModelo, ResultadoEntrenamiento
from motor_futbol.constantes import ALPHA_RIDGE_DEFAULT
from motor_futbol.excepciones import DatosInsuficientes


# Configurar logging con UTF-8
log_handlers = [
    logging.StreamHandler(),
]

# Intentar crear archivo de log con UTF-8
try:
    log_handlers.append(
        logging.FileHandler("entrenamiento_futbol.log", encoding='utf-8')
    )
except Exception:
    pass  # Si falla, solo usar StreamHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger(__name__)


def imprimir_metricas(resultado: ResultadoEntrenamiento, tipo: str) -> None:
    """Imprime las métricas de entrenamiento de forma formateada."""
    print(f"\n{'='*60}")
    print(f"  MODELO: {tipo.upper()}")
    print(f"{'='*60}")

    metricas = resultado.metricas

    print(f"\n  Métricas de Regresión:")
    if 'mae' in metricas:
        print(f"    - MAE:    {metricas['mae']:.4f}")
    if 'rmse' in metricas:
        print(f"    - RMSE:   {metricas['rmse']:.4f}")
    if 'r2' in metricas:
        print(f"    - R²:     {metricas['r2']:.4f}")

    if "brier_score" in metricas:
        print(f"\n  Métricas de Calibración:")
        print(f"    - Brier Score: {metricas['brier_score']:.4f}")
        if 'ece' in metricas:
            print(f"    - ECE:         {metricas['ece']:.4f}")

    print(f"\n  Información del Modelo:")
    if hasattr(resultado, 'n_partidos'):
        print(f"    - Partidos utilizados: {resultado.n_partidos}")
    if hasattr(resultado, 'n_equipos'):
        print(f"    - Equipos:             {resultado.n_equipos}")
    
    # Mostrar alpha si está disponible
    if hasattr(resultado, 'alpha'):
        print(f"    - Alpha Ridge:         {resultado.alpha}")
    elif 'alpha' in metricas:
        print(f"    - Alpha Ridge:         {metricas['alpha']}")
    
    if hasattr(resultado, 'fecha_entrenamiento'):
        print(f"    - Fecha entrenamiento: {resultado.fecha_entrenamiento}")


def crear_entrenador_flexible(
    pool,
    alpha: float,
    min_partidos: int,
    verbose: bool = False,
) -> EntrenadorFutbol:
    """
    Crea una instancia de EntrenadorFutbol de forma flexible,
    adaptándose a los parámetros que acepta el constructor.
    
    Args:
        pool: Pool de conexiones
        alpha: Parámetro de regularización
        min_partidos: Mínimo de partidos
        verbose: Logging verbose
        
    Returns:
        Instancia de EntrenadorFutbol configurada
    """
    # Obtener la firma del constructor
    sig = inspect.signature(EntrenadorFutbol.__init__)
    params = sig.parameters
    
    # Preparar argumentos para el constructor
    constructor_args = {}
    
    # Pool siempre debe estar (es lo mínimo que necesita)
    if 'pool' in params:
        constructor_args['pool'] = pool
    
    # Agregar otros parámetros si son aceptados
    if 'alpha' in params:
        constructor_args['alpha'] = alpha
        if verbose:
            logger.debug(f"Pasando alpha={alpha} al constructor")
    
    if 'min_partidos' in params:
        constructor_args['min_partidos'] = min_partidos
        if verbose:
            logger.debug(f"Pasando min_partidos={min_partidos} al constructor")
    
    # Crear instancia
    if verbose:
        logger.debug(f"Creando EntrenadorFutbol con args: {list(constructor_args.keys())}")
    
    entrenador = EntrenadorFutbol(**constructor_args)
    
    # Configurar atributos que no se pudieron pasar al constructor
    if 'alpha' not in constructor_args and hasattr(entrenador, 'alpha'):
        entrenador.alpha = alpha
        if verbose:
            logger.debug(f"Configurando alpha={alpha} como atributo")
    
    if 'min_partidos' not in constructor_args:
        # Intentar configurarlo como atributo
        if hasattr(entrenador, 'min_partidos'):
            entrenador.min_partidos = min_partidos
            if verbose:
                logger.debug(f"Configurando min_partidos={min_partidos} como atributo")
        # O en la configuración si existe
        elif hasattr(entrenador, 'config'):
            if isinstance(entrenador.config, dict):
                entrenador.config['min_partidos'] = min_partidos
                if verbose:
                    logger.debug(f"Configurando min_partidos={min_partidos} en config")
    
    return entrenador


def entrenar_modelos(
    pool,
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

    try:
        # Crear entrenador de forma flexible
        entrenador = crear_entrenador_flexible(
            pool=pool,
            alpha=alpha,
            min_partidos=min_partidos,
            verbose=verbose,
        )
        
        # Obtener la firma del método entrenar_completo
        sig = inspect.signature(entrenador.entrenar_completo)
        params = sig.parameters
        
        # Preparar argumentos para entrenar_completo
        train_args = {}
        
        if 'alpha' in params:
            train_args['alpha'] = alpha
            if verbose:
                logger.debug(f"Pasando alpha={alpha} a entrenar_completo")
        
        if 'validar_temporal' in params:
            train_args['validar_temporal'] = validar
            if verbose:
                logger.debug(f"Pasando validar_temporal={validar} a entrenar_completo")
        elif 'validar' in params:
            train_args['validar'] = validar
            if verbose:
                logger.debug(f"Pasando validar={validar} a entrenar_completo")
        
        # Llamar al método de entrenamiento
        if verbose:
            logger.debug(f"Llamando entrenar_completo con args: {list(train_args.keys())}")
        
        resultados = entrenador.entrenar_completo(**train_args)

        logger.info(f"Entrenamiento completado exitosamente")

        # Mostrar métricas
        for tipo, resultado in resultados.items():
            imprimir_metricas(resultado, tipo)

        return resultados

    except DatosInsuficientes as e:
        logger.error(f"Datos insuficientes para entrenar: {e}")
        raise
    except Exception as e:
        logger.error(f"Error durante el entrenamiento: {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        raise


def guardar_modelos(
    pool,
    resultados: Dict[str, ResultadoEntrenamiento],
    verbose: bool = False,
) -> str:
    """
    Guarda los modelos entrenados en la base de datos.

    Args:
        pool: Pool de conexiones
        resultados: Resultados del entrenamiento
        verbose: Logging verbose

    Returns:
        Versión asignada a los modelos
    """
    try:
        gestor = GestorVersiones(pool=pool)
        version = gestor.generar_version()

        logger.info(f"Guardando modelos con versión: {version}")

        for tipo_str, resultado in resultados.items():
            # Convertir string a TipoModelo si es necesario
            if isinstance(tipo_str, str):
                tipo = TipoModelo(tipo_str)
            else:
                tipo = tipo_str

            gestor.guardar_modelo(
                modelo=resultado.modelo,
                tipo=tipo,
                version=version,
                metricas=resultado.metricas,
            )

            logger.info(f"Modelo {tipo.value if hasattr(tipo, 'value') else tipo} guardado correctamente")

        # Marcar como versión activa
        gestor.activar_version(version)

        print(f"\n{'='*60}")
        print(f"  MODELOS GUARDADOS")
        print(f"{'='*60}")
        print(f"  Versión: {version}")
        print(f"  Modelos: {', '.join(str(k) for k in resultados.keys())}")
        print(f"{'='*60}\n")

        return version
    
    except Exception as e:
        logger.error(f"Error guardando modelos: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise


def verificar_conexion_bd(pool) -> bool:
    """
    Verifica que la conexión a la base de datos funcione.
    
    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    try:
        conn = pool.getconn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        pool.putconn(conn)
        return True
    except Exception as e:
        logger.error(f"Error verificando conexión a BD: {e}")
        return False


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

    pool = None
    
    try:
        # Obtener pool de conexiones usando la función del módulo db
        logger.info("Estableciendo conexión a la base de datos...")
        pool = obtener_pool()
        
        # Verificar que la conexión funcione
        if not verificar_conexion_bd(pool):
            print("\n❌ Error: No se pudo conectar a la base de datos")
            print("   Por favor verifica:")
            print("   1. Que la variable de entorno DATABASE_URL esté configurada")
            print("   2. Que la base de datos esté accesible")
            print("   3. Que las credenciales sean correctas")
            sys.exit(1)
        
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

        # Resumen final
        print("\n" + "="*60)
        print("  RESUMEN DE ENTRENAMIENTO")
        print("="*60)

        for tipo, resultado in resultados.items():
            print(f"\n  {tipo}:")
            mae_val = resultado.metricas.get('mae', None)
            
            if mae_val is not None:
                if isinstance(mae_val, (int, float)):
                    print(f"    MAE: {mae_val:.4f}")
                    
                    # Verificar objetivos
                    tipo_str = str(tipo)
                    if hasattr(tipo, 'value'):
                        tipo_str = tipo.value
                    
                    if 'CORNERS' in tipo_str.upper() and mae_val < 2.5:
                        print(f"    ✓ MAE < 2.5 (objetivo cumplido)")
                    elif 'GOLES' in tipo_str.upper() and mae_val < 1.0:
                        print(f"    ✓ MAE < 1.0 (objetivo cumplido)")
                else:
                    print(f"    MAE: {mae_val}")
            else:
                print(f"    MAE: N/A")

        print("\n" + "="*60 + "\n")
        
        # Código de salida basado en éxito
        sys.exit(0)

    except DatosInsuficientes as e:
        print(f"\n❌ Error: Datos insuficientes para entrenar")
        print(f"   Detalles: {e}")
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