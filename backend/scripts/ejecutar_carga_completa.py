#!/usr/bin/env python3
"""
Script wrapper para cargar datos históricos de todas las ligas de fútbol.
Ejecuta el script de carga principal para cada liga y temporada.
"""

import subprocess
import sys
from datetime import datetime

# Configuración
LIGAS = [
    'laliga',
    'premier',
    'bundesliga',
    'seriea',
    'ligue1',
    'champions',
    'europa',
    'conference',
    'copa_rey',
    'fa_cup'
]

TEMPORADAS = [
    '2018-19',
    '2019-20',
    '2020-21',
    '2021-22',
    '2022-23',
    '2023-24',
    '2024-25',
    '2025-26'
]

# Nombres descriptivos
NOMBRES_LIGAS = {
    'laliga': 'La Liga (España)',
    'premier': 'Premier League (Inglaterra)',
    'bundesliga': 'Bundesliga (Alemania)',
    'seriea': 'Serie A (Italia)',
    'ligue1': 'Ligue 1 (Francia)',
    'champions': 'Champions League',
    'europa': 'Europa League',
    'conference': 'Conference League',
    'copa_rey': 'Copa del Rey',
    'fa_cup': 'FA Cup'
}

def ejecutar_carga(liga, temporadas, sin_estadisticas=False, verbose=True):
    """Ejecuta el script de carga para una liga específica."""
    
    print(f"\n{'='*70}")
    print(f"🔵 Procesando: {NOMBRES_LIGAS.get(liga, liga)}")
    print(f"{'='*70}\n")
    
    # Construir comando
    cmd = [
        'python',
        'backend/scripts/cargar_historico_futbol_v3.py',
        '--liga', liga,
        '--temporadas', ','.join(temporadas)
    ]
    
    if sin_estadisticas:
        cmd.append('--sin-estadisticas')
    
    if verbose:
        cmd.append('--verbose')
    
    # Ejecutar
    try:
        resultado = subprocess.run(cmd, check=False)
        return resultado.returncode == 0
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("CARGA HISTÓRICA COMPLETA DE FÚTBOL")
    print("="*70)
    print(f"\n📋 Ligas a procesar: {len(LIGAS)}")
    print(f"📅 Temporadas: {len(TEMPORADAS)} ({TEMPORADAS[0]} a {TEMPORADAS[-1]})")
    print(f"📊 Total de combinaciones: {len(LIGAS) * len(TEMPORADAS)}")
    
    # Confirmación
    respuesta = input("\n¿Continuar? (s/n): ").strip().lower()
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Cancelado por el usuario")
        return 1
    
    # Opciones
    print("\nOpciones:")
    print("1. Procesar TODAS las ligas con TODAS las temporadas")
    print("2. Procesar TODAS las ligas SIN estadísticas (más rápido)")
    print("3. Procesar solo ligas principales (LaLiga, Premier, etc.)")
    
    opcion = input("\nSelecciona una opción (1-3): ").strip()
    
    ligas_a_procesar = LIGAS
    sin_estadisticas = False
    
    if opcion == '2':
        sin_estadisticas = True
    elif opcion == '3':
        ligas_a_procesar = ['laliga', 'premier', 'bundesliga', 'seriea', 'ligue1']
    
    # Contadores
    exitosas = 0
    fallidas = 0
    inicio = datetime.now()
    
    # Log
    log_file = f"carga_historica_{inicio.strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Inicio: {inicio}\n")
        f.write(f"Ligas: {ligas_a_procesar}\n")
        f.write(f"Temporadas: {TEMPORADAS}\n\n")
    
    # Procesar cada liga
    for i, liga in enumerate(ligas_a_procesar, 1):
        print(f"\n{'#'*70}")
        print(f"Liga {i}/{len(ligas_a_procesar)}")
        print(f"{'#'*70}")
        
        exito = ejecutar_carga(
            liga,
            TEMPORADAS,
            sin_estadisticas=sin_estadisticas,
            verbose=True
        )
        
        if exito:
            print(f"\n✅ {liga} completada exitosamente")
            exitosas += 1
        else:
            print(f"\n❌ Error procesando {liga}")
            fallidas += 1
        
        # Registrar en log
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{liga}: {'✅ OK' if exito else '❌ ERROR'}\n")
        
        # Pequeña pausa entre ligas
        if i < len(ligas_a_procesar):
            print("\n⏳ Pausa de 5 segundos...")
            import time
            time.sleep(5)
    
    # Resumen final
    duracion = datetime.now() - inicio
    
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    print(f"⏱️  Duración total: {duracion}")
    print(f"✅ Ligas exitosas: {exitosas}")
    print(f"❌ Ligas fallidas: {fallidas}")
    print(f"📝 Log guardado en: {log_file}")
    print("="*70 + "\n")
    
    return 0 if fallidas == 0 else 1


if __name__ == '__main__':
    sys.exit(main())