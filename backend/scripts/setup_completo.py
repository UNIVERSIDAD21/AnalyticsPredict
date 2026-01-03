#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_completo.py — Script TODO EN UNO para configurar el sistema NBA.

Este script hace TODO de una sola vez:
1. Entrena el modelo Ridge con TODOS los equipos
2. Crea el usuario de desarrollo
3. Pobla la tabla estadisticas_equipos (agregados)
4. Pobla la tabla partidos (TODOS los partidos individuales)

Uso desde la carpeta backend:
    python setup_completo.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

Q_KEYS = ("Q1", "Q2", "Q3", "Q4")
USUARIO_DESARROLLO_ID = "00000000-0000-0000-0000-000000000001"

# MAPEO CRÍTICO: Los CSVs usan "LA Clippers" pero el frontend usa "Los Angeles Clippers"
MAPEO_NOMBRES = {
    "la clippers": "los angeles clippers",
    "la lakers": "los angeles lakers",
}

MAPEO_NOMBRES_CSV_A_BD = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
}


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ══════════════════════════════════════════════════════════════

def normalize_name(nombre: str) -> str:
    """Normaliza el nombre de un equipo para el modelo."""
    nombre = " ".join((nombre or "").strip().lower().replace("_", " ").split())
    return MAPEO_NOMBRES.get(nombre, nombre)


def normalizar_nombre_bd(nombre: str) -> str:
    """Normaliza el nombre para la BD."""
    return MAPEO_NOMBRES_CSV_A_BD.get(nombre, nombre)


def parse_location_value(valor) -> int:
    """Convierte ubicación a 1 (local) o 0 (visitante)."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return 1
    texto = str(valor).strip().upper()
    if texto in ("HOME", "H", "LOCAL"):
        return 1
    if texto in ("AWAY", "A", "VISITOR", "VISITANTE") or texto.startswith("@"):
        return 0
    return 1


def parse_location_str(valor) -> str:
    """Convierte ubicación a string."""
    return "HOME" if parse_location_value(valor) == 1 else "AWAY"


def obtener_database_url() -> str:
    """Obtiene la URL de la base de datos."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return ""
    if "sslmode=" not in url:
        separador = "&" if "?" in url else "?"
        url = f"{url}{separador}sslmode=require"
    return url


# ══════════════════════════════════════════════════════════════
# FUNCIONES DEL MODELO
# ══════════════════════════════════════════════════════════════

def build_design_matrix(
    team_names: Sequence[str],
    opp_names: Sequence[str],
    is_home: Sequence[int],
    entity_to_idx: Dict[str, int],
) -> np.ndarray:
    """Construye la matriz de diseño para regresión Ridge."""
    n = len(team_names)
    k = len(entity_to_idx)
    X = np.zeros((n, 1 + k + k + 1), dtype=float)
    X[:, 0] = 1.0
    for i, (team, opp, home) in enumerate(zip(team_names, opp_names, is_home)):
        team_norm = normalize_name(team)
        opp_norm = normalize_name(opp)
        ti = entity_to_idx[team_norm]
        oi = entity_to_idx[opp_norm]
        X[i, 1 + ti] = 1.0
        X[i, 1 + k + oi] = 1.0
        X[i, -1] = float(home)
    return X


def fit_ridge(X: np.ndarray, Y: np.ndarray, alpha: float) -> Tuple[np.ndarray, np.ndarray]:
    """Ajusta regresión Ridge."""
    p = X.shape[1]
    I = np.eye(p, dtype=float)
    I[0, 0] = 0.0
    A = X.T @ X + alpha * I
    B = X.T @ Y
    W = np.linalg.solve(A, B)
    resid = Y - X @ W
    std = np.sqrt(np.mean(resid**2, axis=0) + 1e-9)
    return W, std


def cargar_datos_modelo(csv_paths: Sequence[Path]) -> pd.DataFrame:
    """Carga datos para entrenar el modelo."""
    frames: List[pd.DataFrame] = []
    
    for path in csv_paths:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"    ⚠️  Error leyendo {path.name}: {e}")
            continue
        
        if "season_type" in df.columns:
            df = df[df["season_type"].fillna("").str.upper() != "PRE"].copy()
        
        if "valid_linescore" in df.columns:
            df = df[df["valid_linescore"] == True].copy()

        cols_req = ["team_q1", "team_q2", "team_q3", "team_q4", 
                    "opp_q1", "opp_q2", "opp_q3", "opp_q4"]
        df = df.dropna(subset=cols_req)
        df = df[df["opponent"].notna() & (df["opponent"].astype(str) != "")]

        if len(df) == 0:
            continue

        frames.append(
            pd.DataFrame({
                "team": df["team"].astype(str),
                "opp": df["opponent"].astype(str),
                "is_home": df.get("location", "HOME").apply(parse_location_value),
                "team_q1": pd.to_numeric(df["team_q1"], errors="coerce"),
                "team_q2": pd.to_numeric(df["team_q2"], errors="coerce"),
                "team_q3": pd.to_numeric(df["team_q3"], errors="coerce"),
                "team_q4": pd.to_numeric(df["team_q4"], errors="coerce"),
                "opp_q1": pd.to_numeric(df["opp_q1"], errors="coerce"),
                "opp_q2": pd.to_numeric(df["opp_q2"], errors="coerce"),
                "opp_q3": pd.to_numeric(df["opp_q3"], errors="coerce"),
                "opp_q4": pd.to_numeric(df["opp_q4"], errors="coerce"),
            })
        )
        print(f"    ✅ {path.name}: {len(df)} partidos")

    if not frames:
        raise ValueError("No se encontraron datos válidos en los CSVs")
        
    return pd.concat(frames, ignore_index=True).dropna()


def entrenar_modelo(cwd: Path, csv_paths: List[Path]) -> bool:
    """Entrena y guarda el modelo."""
    print()
    print("=" * 70)
    print("PASO 1: ENTRENAR MODELO")
    print("=" * 70)
    print()
    
    print("📥 Cargando datos de partidos...")
    data = cargar_datos_modelo(csv_paths)
    print()
    print(f"📊 Total de partidos válidos: {len(data)}")
    
    # Obtener equipos únicos NORMALIZADOS
    equipos_team = set(data["team"].map(normalize_name))
    equipos_opp = set(data["opp"].map(normalize_name))
    entities = sorted(equipos_team | equipos_opp)
    entity_to_idx = {name: i for i, name in enumerate(entities)}
    
    print(f"🏀 Equipos únicos en el modelo: {len(entities)}")
    print()
    
    # Mostrar equipos
    print("📋 EQUIPOS EN EL MODELO:")
    print("-" * 50)
    for i, equipo in enumerate(entities, 1):
        print(f"   {i:2d}. {equipo}")
    print("-" * 50)
    print()
    
    # Construir matriz
    print("🔧 Construyendo matriz de diseño...")
    X = build_design_matrix(
        team_names=data["team"].tolist(),
        opp_names=data["opp"].tolist(),
        is_home=data["is_home"].astype(int).tolist(),
        entity_to_idx=entity_to_idx,
    )
    
    y_team = data[["team_q1", "team_q2", "team_q3", "team_q4"]].to_numpy(dtype=float)
    y_opp = data[["opp_q1", "opp_q2", "opp_q3", "opp_q4"]].to_numpy(dtype=float)
    
    # Entrenar
    print("🎯 Entrenando modelo Ridge...")
    alpha = 5.0
    w_team, std_team = fit_ridge(X, y_team, alpha)
    w_opp, std_opp = fit_ridge(X, y_opp, alpha)
    
    # Guardar
    output_dir = cwd / "datos"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "modelo_entrenado.npz"
    
    np.savez_compressed(
        output_path,
        alpha=np.array([float(alpha)], dtype=float),
        entity_json=np.array([json.dumps(entity_to_idx, ensure_ascii=False)], dtype=object),
        w_team=w_team,
        w_opp=w_opp,
        std_team=std_team,
        std_opp=std_opp,
    )
    
    print()
    print(f"✅ Modelo guardado: {output_path}")
    print(f"   🏀 Equipos: {len(entities)}")
    print(f"   📊 Partidos: {len(data)}")
    
    # Verificar
    with np.load(output_path, allow_pickle=True) as datos:
        loaded = json.loads(str(datos['entity_json'][0]))
        print(f"   ✅ Verificado: {len(loaded)} equipos cargados correctamente")
    
    return True


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════

def crear_usuario_desarrollo(conexion) -> bool:
    """Crea el usuario de desarrollo."""
    print()
    print("=" * 70)
    print("PASO 2: CREAR USUARIO DE DESARROLLO")
    print("=" * 70)
    print()
    
    with conexion.cursor() as cursor:
        try:
            cursor.execute("""
                INSERT INTO usuarios (
                    id, email, nombre, password_hash, rol, activo,
                    preferencias, bankroll_inicial
                ) VALUES (
                    %s, 'desarrollo@nba.local', 'Usuario Desarrollo',
                    'no_auth', 'admin', true,
                    '{"tema": "oscuro"}'::jsonb, 1000.00
                )
                ON CONFLICT (id) DO UPDATE SET activo = true
                RETURNING id
            """, [USUARIO_DESARROLLO_ID])
            conexion.commit()
            print(f"✅ Usuario de desarrollo: {USUARIO_DESARROLLO_ID}")
            return True
        except Exception as e:
            print(f"⚠️  No se pudo crear usuario (puede que la tabla no exista): {e}")
            conexion.rollback()
            return False


def obtener_equipos_bd(conexion) -> Dict[str, str]:
    """Obtiene mapeo nombre -> id de equipos."""
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM equipos WHERE activo = true")
        return {row[1]: row[0] for row in cursor.fetchall()}


def obtener_temporadas_bd(conexion, temporadas: List[int]) -> Dict[int, str]:
    """Obtiene o crea temporadas."""
    temporadas_bd = {}
    with conexion.cursor() as cursor:
        for temp in temporadas:
            nombre_temp = f"{temp-1}-{temp}"
            cursor.execute("SELECT id FROM temporadas WHERE nombre = %s", [nombre_temp])
            resultado = cursor.fetchone()
            
            if resultado:
                temporadas_bd[temp] = resultado[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO temporadas (nombre, anio_inicio, anio_fin, activa)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    [nombre_temp, temp - 1, temp, temp == max(temporadas)]
                )
                temporadas_bd[temp] = cursor.fetchone()[0]
                print(f"   ✅ Creada temporada: {nombre_temp}")
        
        conexion.commit()
    return temporadas_bd


def poblar_estadisticas_equipos(conexion, csv_paths: List[Path]) -> int:
    """Pobla la tabla estadisticas_equipos con estadísticas AGREGADAS."""
    print()
    print("=" * 70)
    print("PASO 3: POBLAR ESTADÍSTICAS DE EQUIPOS (AGREGADOS)")
    print("=" * 70)
    print()
    
    # Cargar datos
    frames = []
    for path in csv_paths:
        try:
            df = pd.read_csv(path)
            if "season_type" in df.columns:
                df = df[df["season_type"].fillna("").str.upper() == "REG"].copy()
            if "valid_linescore" in df.columns:
                df = df[df["valid_linescore"] == True].copy()
            
            df["team"] = df["team"].apply(normalizar_nombre_bd)
            df["opponent"] = df["opponent"].apply(normalizar_nombre_bd)
            frames.append(df)
        except:
            continue
    
    if not frames:
        print("❌ No se pudieron cargar datos")
        return 0
    
    df = pd.concat(frames, ignore_index=True)
    
    equipos_bd = obtener_equipos_bd(conexion)
    temporadas = sorted(df["season"].unique())
    temporadas_bd = obtener_temporadas_bd(conexion, temporadas)
    
    insertados = 0
    with conexion.cursor() as cursor:
        for equipo in sorted(df["team"].unique()):
            if equipo not in equipos_bd:
                continue
            
            equipo_id = equipos_bd[equipo]
            
            for temporada in temporadas:
                if temporada not in temporadas_bd:
                    continue
                
                partidos = df[(df["team"] == equipo) & (df["season"] == temporada)]
                if len(partidos) == 0:
                    continue
                
                stats = {
                    "victorias": len(partidos[partidos["winner"] == "TEAM"]),
                    "derrotas": len(partidos[partidos["winner"] == "OPP"]),
                    "ppg_q1": round(partidos["team_q1"].mean(), 2),
                    "ppg_q2": round(partidos["team_q2"].mean(), 2),
                    "ppg_q3": round(partidos["team_q3"].mean(), 2),
                    "ppg_q4": round(partidos["team_q4"].mean(), 2),
                    "ppg_total": round(partidos["team_total"].mean(), 2) if "team_total" in partidos else 0,
                    "opp_q1": round(partidos["opp_q1"].mean(), 2),
                    "opp_q2": round(partidos["opp_q2"].mean(), 2),
                    "opp_q3": round(partidos["opp_q3"].mean(), 2),
                    "opp_q4": round(partidos["opp_q4"].mean(), 2),
                    "opp_total": round(partidos["opp_total"].mean(), 2) if "opp_total" in partidos else 0,
                    "partidos_jugados": len(partidos),
                }
                
                try:
                    cursor.execute(
                        """
                        INSERT INTO estadisticas_equipos (
                            equipo_id, temporada_id, victorias, derrotas,
                            ppg_q1, ppg_q2, ppg_q3, ppg_q4, ppg_total,
                            opp_q1, opp_q2, opp_q3, opp_q4, opp_total,
                            partidos_jugados, ultima_actualizacion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (equipo_id, temporada_id) DO UPDATE SET
                            victorias = EXCLUDED.victorias,
                            derrotas = EXCLUDED.derrotas,
                            ppg_q1 = EXCLUDED.ppg_q1, ppg_q2 = EXCLUDED.ppg_q2,
                            ppg_q3 = EXCLUDED.ppg_q3, ppg_q4 = EXCLUDED.ppg_q4,
                            ppg_total = EXCLUDED.ppg_total,
                            opp_q1 = EXCLUDED.opp_q1, opp_q2 = EXCLUDED.opp_q2,
                            opp_q3 = EXCLUDED.opp_q3, opp_q4 = EXCLUDED.opp_q4,
                            opp_total = EXCLUDED.opp_total,
                            partidos_jugados = EXCLUDED.partidos_jugados,
                            ultima_actualizacion = NOW()
                        """,
                        [str(equipo_id), str(temporadas_bd[temporada]),
                         stats["victorias"], stats["derrotas"],
                         stats["ppg_q1"], stats["ppg_q2"], stats["ppg_q3"], stats["ppg_q4"], stats["ppg_total"],
                         stats["opp_q1"], stats["opp_q2"], stats["opp_q3"], stats["opp_q4"], stats["opp_total"],
                         stats["partidos_jugados"]]
                    )
                    insertados += 1
                except Exception as e:
                    pass
        
        conexion.commit()
    
    print(f"✅ Estadísticas agregadas: {insertados} registros (30 equipos × temporadas)")
    return insertados


def poblar_partidos(conexion, csv_paths: List[Path]) -> int:
    """Pobla la tabla partidos con TODOS los partidos individuales."""
    print()
    print("=" * 70)
    print("PASO 4: POBLAR TODOS LOS PARTIDOS INDIVIDUALES")
    print("=" * 70)
    print()
    
    # Cargar TODOS los datos
    frames = []
    for path in csv_paths:
        try:
            df = pd.read_csv(path)
            if "valid_linescore" in df.columns:
                df = df[df["valid_linescore"] == True].copy()
            df["team"] = df["team"].apply(normalizar_nombre_bd)
            df["opponent"] = df["opponent"].apply(normalizar_nombre_bd)
            frames.append(df)
            print(f"   📄 {path.name}: {len(df)} partidos")
        except Exception as e:
            print(f"   ⚠️  Error en {path.name}: {e}")
    
    if not frames:
        print("❌ No se pudieron cargar datos")
        return 0
    
    df = pd.concat(frames, ignore_index=True)
    print()
    print(f"📊 Total partidos a procesar: {len(df)}")

    cols_puntos = [
        "team_q1", "team_q2", "team_q3", "team_q4",
        "opp_q1", "opp_q2", "opp_q3", "opp_q4",
    ]
    df[cols_puntos] = df[cols_puntos].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=cols_puntos)
    if len(df) == 0:
        print("❌ No hay partidos válidos tras limpiar puntajes.")
        return 0
    
    equipos_bd = obtener_equipos_bd(conexion)
    temporadas = sorted(df["season"].unique())
    temporadas_bd = obtener_temporadas_bd(conexion, temporadas)
    
    insertados = 0
    errores = 0
    
    print()
    print("📤 Insertando partidos...")
    
    with conexion.cursor() as cursor:
        for idx, row in df.iterrows():
            try:
                location = parse_location_str(row.get("location", "HOME"))
                
                if location == "HOME":
                    equipo_local = row["team"]
                    equipo_visitante = row["opponent"]
                    local_q1, local_q2, local_q3, local_q4 = row["team_q1"], row["team_q2"], row["team_q3"], row["team_q4"]
                    visit_q1, visit_q2, visit_q3, visit_q4 = row["opp_q1"], row["opp_q2"], row["opp_q3"], row["opp_q4"]
                else:
                    equipo_local = row["opponent"]
                    equipo_visitante = row["team"]
                    local_q1, local_q2, local_q3, local_q4 = row["opp_q1"], row["opp_q2"], row["opp_q3"], row["opp_q4"]
                    visit_q1, visit_q2, visit_q3, visit_q4 = row["team_q1"], row["team_q2"], row["team_q3"], row["team_q4"]
                
                if equipo_local not in equipos_bd or equipo_visitante not in equipos_bd:
                    errores += 1
                    continue
                
                temporada_id = temporadas_bd.get(row["season"])
                if not temporada_id:
                    errores += 1
                    continue
                
                # Parsear fecha
                try:
                    fecha_str = str(row["date"])
                    if "T" in fecha_str:
                        fecha = datetime.fromisoformat(
                            fecha_str.replace("+00:00", "").replace("Z", "")
                        ).date()
                    else:
                        fecha = datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
                except:
                    fecha = datetime.now().date()
                
                local_total = int(local_q1 + local_q2 + local_q3 + local_q4)
                visit_total = int(visit_q1 + visit_q2 + visit_q3 + visit_q4)
                
                # Determinar ganador
                ganador_id = None
                if local_total > visit_total:
                    ganador_id = equipos_bd[equipo_local]
                elif visit_total > local_total:
                    ganador_id = equipos_bd[equipo_visitante]
                
                season_type = str(row.get("season_type", "REG")).upper()
                if season_type not in ("REG", "POST", "PRE"):
                    season_type = "REG"
                
                cursor.execute("SAVEPOINT insertar_partido")
                cursor.execute(
                    """
                    INSERT INTO partidos (
                        temporada_id, fecha_partido, tipo_partido,
                        equipo_local_id, equipo_visitante_id,
                        local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
                        visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
                        ganador_id, hubo_overtime
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    [
                        str(temporada_id), fecha, season_type,
                        str(equipos_bd[equipo_local]), str(equipos_bd[equipo_visitante]),
                        int(local_q1), int(local_q2), int(local_q3), int(local_q4), 0, local_total,
                        int(visit_q1), int(visit_q2), int(visit_q3), int(visit_q4), 0, visit_total,
                        str(ganador_id) if ganador_id else None,
                        row.get("ot_count", 0) > 0 if "ot_count" in row else False
                    ]
                )
                
                if cursor.fetchone():
                    insertados += 1
                cursor.execute("RELEASE SAVEPOINT insertar_partido")
                
            except Exception as e:
                errores += 1
                if errores <= 5:
                    print(f"   ⚠️  Error en fila {idx}: {e}")
                cursor.execute("ROLLBACK TO SAVEPOINT insertar_partido")
            
            # Progreso
            if (idx + 1) % 2000 == 0:
                conexion.commit()
                print(f"   Procesados: {idx + 1} / {len(df)} ({insertados} insertados)")
        
        conexion.commit()
    
    # Total en BD
    with conexion.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM partidos")
        total_bd = cursor.fetchone()[0]
    
    print()
    print(f"✅ Partidos insertados: {insertados}")
    print(f"⚠️  Errores/duplicados: {errores}")
    print(f"📊 Total en tabla partidos: {total_bd}")
    
    return insertados


# ══════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main() -> int:
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "🏀 SETUP COMPLETO NBA 🏀" + " " * 21 + "║")
    print("║" + " " * 15 + "Modelo + Usuario + Base de Datos" + " " * 16 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    cwd = Path.cwd()
    print(f"📂 Directorio: {cwd}")
    
    # Buscar CSVs
    csv_paths = [p for p in sorted(cwd.glob("*.csv")) 
                 if p.is_file() and p.name != "equipos.csv"]
    
    if not csv_paths:
        print()
        print("❌ ERROR: No se encontraron CSVs de partidos.")
        print()
        print("   Ejecuta este script DESDE la carpeta backend:")
        print("   cd C:\\Users\\ING-ERIK\\Documents\\Proyectos\\AnalyticsPredict\\backend")
        print("   python setup_completo.py")
        return 1
    
    print(f"📁 CSVs encontrados: {len(csv_paths)}")
    
    # PASO 1: Entrenar modelo
    try:
        entrenar_modelo(cwd, csv_paths)
    except Exception as e:
        print(f"❌ Error entrenando modelo: {e}")
        return 1
    
    # PASOS 2-4: Base de datos (solo si hay DATABASE_URL)
    db_url = obtener_database_url()
    if not db_url:
        print()
        print("⚠️  DATABASE_URL no configurada. Solo se entrenó el modelo.")
        print("   Crea un archivo .env con DATABASE_URL para poblar la BD.")
    else:
        try:
            import psycopg
            print()
            print("🔌 Conectando a PostgreSQL...")
            conexion = psycopg.connect(db_url)
            print("✅ Conexión establecida")
            
            crear_usuario_desarrollo(conexion)
            poblar_estadisticas_equipos(conexion, csv_paths)
            poblar_partidos(conexion, csv_paths)
            
            conexion.close()
        except ImportError:
            print("⚠️  psycopg no instalado. Instala con: pip install psycopg[binary]")
        except Exception as e:
            print(f"❌ Error con BD: {e}")
    
    # Resumen final
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "✅ SETUP COMPLETADO ✅" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("🎉 ¡Todo listo! Ahora reinicia el servidor:")
    print()
    print("   python -m uvicorn app:app --reload --port 8000")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
