#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poblar_estadisticas_equipos.py — Calcula y guarda estadísticas de equipos en PostgreSQL.

Uso desde la carpeta backend:
    python poblar_estadisticas_equipos.py

Este script:
1. Lee todos los CSVs de partidos
2. Calcula estadísticas por equipo y temporada
3. Inserta/actualiza en la tabla estadisticas_equipos
"""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
import psycopg

# Cargar variables de entorno
load_dotenv()

# ══════════════════════════════════════════════════════════════
# MAPEO DE NOMBRES (igual que en entrenar_modelo_completo.py)
# ══════════════════════════════════════════════════════════════

MAPEO_NOMBRES_CSV_A_BD = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
}


def normalizar_nombre_equipo(nombre: str) -> str:
    """Normaliza el nombre del equipo para que coincida con la BD."""
    return MAPEO_NOMBRES_CSV_A_BD.get(nombre, nombre)


def obtener_database_url() -> str:
    """Obtiene la URL de la base de datos."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está configurada en .env")
    if "sslmode=" not in url:
        separador = "&" if "?" in url else "?"
        url = f"{url}{separador}sslmode=require"
    return url


def parse_location(valor) -> str:
    """Convierte el valor de ubicación a 'HOME' o 'AWAY'."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "HOME"
    texto = str(valor).strip().upper()
    if texto in ("HOME", "H", "LOCAL"):
        return "HOME"
    if texto in ("AWAY", "A", "VISITOR", "VISITANTE") or texto.startswith("@"):
        return "AWAY"
    if texto.startswith("VS"):
        return "HOME"
    return "HOME"


def cargar_partidos(csv_paths: List[Path]) -> pd.DataFrame:
    """Carga todos los partidos de los CSVs."""
    frames = []
    
    for path in csv_paths:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"  ⚠️  Error leyendo {path.name}: {e}")
            continue
        
        # Solo partidos de temporada regular
        if "season_type" in df.columns:
            df = df[df["season_type"].fillna("").str.upper() == "REG"].copy()
        
        # Solo partidos válidos
        if "valid_linescore" in df.columns:
            df = df[df["valid_linescore"] == True].copy()
        
        # Columnas necesarias
        columnas = ["season", "team", "opponent", "location", 
                    "team_q1", "team_q2", "team_q3", "team_q4", "team_total",
                    "opp_q1", "opp_q2", "opp_q3", "opp_q4", "opp_total", "winner"]
        
        if not all(c in df.columns for c in columnas):
            print(f"  ⚠️  {path.name} no tiene todas las columnas requeridas")
            continue
        
        df = df[columnas].dropna()
        
        if len(df) == 0:
            continue
        
        # Normalizar nombres de equipos
        df["team"] = df["team"].apply(normalizar_nombre_equipo)
        df["opponent"] = df["opponent"].apply(normalizar_nombre_equipo)
        df["location"] = df["location"].apply(parse_location)
        
        frames.append(df)
        print(f"  ✅ {path.name}: {len(df)} partidos REG")
    
    if not frames:
        raise ValueError("No se encontraron datos válidos")
    
    return pd.concat(frames, ignore_index=True)


def calcular_estadisticas_equipo(
    df: pd.DataFrame, 
    nombre_equipo: str, 
    temporada: int
) -> Optional[Dict]:
    """Calcula estadísticas para un equipo en una temporada."""
    
    # Filtrar partidos del equipo en la temporada
    partidos = df[(df["team"] == nombre_equipo) & (df["season"] == temporada)]
    
    if len(partidos) == 0:
        return None
    
    # Calcular victorias/derrotas
    victorias = len(partidos[partidos["winner"] == "TEAM"])
    derrotas = len(partidos[partidos["winner"] == "OPP"])
    
    # Victorias/derrotas por ubicación
    partidos_local = partidos[partidos["location"] == "HOME"]
    partidos_visitante = partidos[partidos["location"] == "AWAY"]
    
    victorias_local = len(partidos_local[partidos_local["winner"] == "TEAM"])
    derrotas_local = len(partidos_local[partidos_local["winner"] == "OPP"])
    victorias_visitante = len(partidos_visitante[partidos_visitante["winner"] == "TEAM"])
    derrotas_visitante = len(partidos_visitante[partidos_visitante["winner"] == "OPP"])
    
    # Promedios por cuarto
    ppg_q1 = partidos["team_q1"].mean()
    ppg_q2 = partidos["team_q2"].mean()
    ppg_q3 = partidos["team_q3"].mean()
    ppg_q4 = partidos["team_q4"].mean()
    ppg_total = partidos["team_total"].mean()
    
    # Puntos rivales por cuarto
    opp_q1 = partidos["opp_q1"].mean()
    opp_q2 = partidos["opp_q2"].mean()
    opp_q3 = partidos["opp_q3"].mean()
    opp_q4 = partidos["opp_q4"].mean()
    opp_total = partidos["opp_total"].mean()
    
    # Porcentaje Over (línea promedio = ppg + opp / 2 por cuarto)
    # Usamos líneas típicas: Q1-Q4 = 55.5, Total = 220.5
    linea_q = 55.5
    linea_total = 220.5
    
    total_q1 = partidos["team_q1"] + partidos["opp_q1"]
    total_q2 = partidos["team_q2"] + partidos["opp_q2"]
    total_q3 = partidos["team_q3"] + partidos["opp_q3"]
    total_q4 = partidos["team_q4"] + partidos["opp_q4"]
    total_game = partidos["team_total"] + partidos["opp_total"]
    
    over_pct_q1 = (total_q1 > linea_q).mean()
    over_pct_q2 = (total_q2 > linea_q).mean()
    over_pct_q3 = (total_q3 > linea_q).mean()
    over_pct_q4 = (total_q4 > linea_q).mean()
    over_pct_total = (total_game > linea_total).mean()
    
    return {
        "victorias": victorias,
        "derrotas": derrotas,
        "victorias_local": victorias_local,
        "derrotas_local": derrotas_local,
        "victorias_visitante": victorias_visitante,
        "derrotas_visitante": derrotas_visitante,
        "ppg_q1": round(ppg_q1, 2),
        "ppg_q2": round(ppg_q2, 2),
        "ppg_q3": round(ppg_q3, 2),
        "ppg_q4": round(ppg_q4, 2),
        "ppg_total": round(ppg_total, 2),
        "opp_q1": round(opp_q1, 2),
        "opp_q2": round(opp_q2, 2),
        "opp_q3": round(opp_q3, 2),
        "opp_q4": round(opp_q4, 2),
        "opp_total": round(opp_total, 2),
        "over_pct_q1": round(over_pct_q1, 4),
        "over_pct_q2": round(over_pct_q2, 4),
        "over_pct_q3": round(over_pct_q3, 4),
        "over_pct_q4": round(over_pct_q4, 4),
        "over_pct_total": round(over_pct_total, 4),
        "partidos_jugados": len(partidos),
    }


def main() -> int:
    print("=" * 60)
    print("📊 POBLAR ESTADÍSTICAS DE EQUIPOS")
    print("=" * 60)
    print()
    
    # Buscar CSVs
    csv_dir = Path(".")
    csv_paths = [p for p in sorted(csv_dir.glob("*.csv")) 
                 if p.is_file() and p.name != "equipos.csv"]
    
    if not csv_paths:
        print("❌ No se encontraron CSVs de partidos")
        return 1
    
    print(f"📁 Encontrados {len(csv_paths)} archivos CSV")
    print()
    
    # Cargar partidos
    print("📥 Cargando partidos...")
    df = cargar_partidos(csv_paths)
    print()
    print(f"📊 Total partidos cargados: {len(df)}")
    
    # Obtener equipos y temporadas únicos
    equipos = sorted(df["team"].unique())
    temporadas = sorted(df["season"].unique())
    
    print(f"🏀 Equipos: {len(equipos)}")
    print(f"📅 Temporadas: {temporadas}")
    print()
    
    # Conectar a la BD
    print("🔌 Conectando a la base de datos...")
    try:
        conexion = psycopg.connect(obtener_database_url())
        print("✅ Conexión establecida")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return 1
    
    print()
    
    # Obtener mapeo de equipos (nombre -> id)
    print("📋 Obteniendo IDs de equipos...")
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM equipos WHERE activo = true")
        equipos_bd = {row[1]: row[0] for row in cursor.fetchall()}
    
    if not equipos_bd:
        print("❌ No hay equipos en la tabla 'equipos'. Ejecuta migrar_equipos.py primero.")
        conexion.close()
        return 1
    
    print(f"   Encontrados {len(equipos_bd)} equipos en BD")
    
    # Obtener o crear temporadas
    print("📅 Verificando temporadas...")
    temporadas_bd = {}
    with conexion.cursor() as cursor:
        for temp in temporadas:
            nombre_temp = f"{temp-1}-{temp}"
            cursor.execute(
                "SELECT id FROM temporadas_baloncesto WHERE nombre = %s",
                [nombre_temp]
            )
            resultado = cursor.fetchone()
            
            if resultado:
                temporadas_bd[temp] = resultado[0]
            else:
                # Crear temporada
                cursor.execute(
                    """
                    INSERT INTO temporadas_baloncesto (nombre, anio_inicio, anio_fin, activa)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    [nombre_temp, temp - 1, temp, temp == max(temporadas)]
                )
                temporadas_bd[temp] = cursor.fetchone()[0]
                print(f"   ✅ Creada temporada: {nombre_temp}")
        
        conexion.commit()
    
    print()
    
    # Calcular e insertar estadísticas
    print("📊 Calculando e insertando estadísticas...")
    insertados = 0
    actualizados = 0
    errores = 0
    
    with conexion.cursor() as cursor:
        for equipo in equipos:
            if equipo not in equipos_bd:
                print(f"   ⚠️  Equipo no encontrado en BD: {equipo}")
                errores += 1
                continue
            
            equipo_id = equipos_bd[equipo]
            
            for temporada in temporadas:
                if temporada not in temporadas_bd:
                    continue
                
                temporada_id = temporadas_bd[temporada]
                stats = calcular_estadisticas_equipo(df, equipo, temporada)
                
                if stats is None:
                    continue
                
                try:
                    cursor.execute(
                        """
                        INSERT INTO estadisticas_equipos (
                            equipo_id, temporada_id,
                            victorias, derrotas,
                            victorias_local, derrotas_local,
                            victorias_visitante, derrotas_visitante,
                            ppg_q1, ppg_q2, ppg_q3, ppg_q4, ppg_total,
                            opp_q1, opp_q2, opp_q3, opp_q4, opp_total,
                            over_pct_q1, over_pct_q2, over_pct_q3, over_pct_q4, over_pct_total,
                            partidos_jugados, ultima_actualizacion
                        ) VALUES (
                            %(equipo_id)s, %(temporada_id)s,
                            %(victorias)s, %(derrotas)s,
                            %(victorias_local)s, %(derrotas_local)s,
                            %(victorias_visitante)s, %(derrotas_visitante)s,
                            %(ppg_q1)s, %(ppg_q2)s, %(ppg_q3)s, %(ppg_q4)s, %(ppg_total)s,
                            %(opp_q1)s, %(opp_q2)s, %(opp_q3)s, %(opp_q4)s, %(opp_total)s,
                            %(over_pct_q1)s, %(over_pct_q2)s, %(over_pct_q3)s, %(over_pct_q4)s, %(over_pct_total)s,
                            %(partidos_jugados)s, NOW()
                        )
                        ON CONFLICT (equipo_id, temporada_id) DO UPDATE SET
                            victorias = EXCLUDED.victorias,
                            derrotas = EXCLUDED.derrotas,
                            victorias_local = EXCLUDED.victorias_local,
                            derrotas_local = EXCLUDED.derrotas_local,
                            victorias_visitante = EXCLUDED.victorias_visitante,
                            derrotas_visitante = EXCLUDED.derrotas_visitante,
                            ppg_q1 = EXCLUDED.ppg_q1,
                            ppg_q2 = EXCLUDED.ppg_q2,
                            ppg_q3 = EXCLUDED.ppg_q3,
                            ppg_q4 = EXCLUDED.ppg_q4,
                            ppg_total = EXCLUDED.ppg_total,
                            opp_q1 = EXCLUDED.opp_q1,
                            opp_q2 = EXCLUDED.opp_q2,
                            opp_q3 = EXCLUDED.opp_q3,
                            opp_q4 = EXCLUDED.opp_q4,
                            opp_total = EXCLUDED.opp_total,
                            over_pct_q1 = EXCLUDED.over_pct_q1,
                            over_pct_q2 = EXCLUDED.over_pct_q2,
                            over_pct_q3 = EXCLUDED.over_pct_q3,
                            over_pct_q4 = EXCLUDED.over_pct_q4,
                            over_pct_total = EXCLUDED.over_pct_total,
                            partidos_jugados = EXCLUDED.partidos_jugados,
                            ultima_actualizacion = NOW()
                        RETURNING (xmax = 0) AS insertado
                        """,
                        {
                            "equipo_id": str(equipo_id),
                            "temporada_id": str(temporada_id),
                            **stats
                        }
                    )
                    
                    resultado = cursor.fetchone()
                    if resultado and resultado[0]:
                        insertados += 1
                    else:
                        actualizados += 1
                        
                except Exception as e:
                    print(f"   ❌ Error con {equipo} ({temporada}): {e}")
                    errores += 1
        
        conexion.commit()
    
    # Verificar total
    with conexion.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM estadisticas_equipos")
        total = cursor.fetchone()[0]
    
    conexion.close()
    
    print()
    print("=" * 60)
    print("✅ ESTADÍSTICAS POBLADAS")
    print("=" * 60)
    print(f"   📥 Insertados:   {insertados}")
    print(f"   🔄 Actualizados: {actualizados}")
    print(f"   ⚠️  Errores:     {errores}")
    print(f"   📊 Total en BD:  {total}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
