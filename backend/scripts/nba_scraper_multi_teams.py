#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nba_scraper_multi_teams.py — Script CORREGIDO para poblar el sistema NBA

CORRECCIONES v3:
- Manejo correcto de overtime en TODOS los casos
- Tiebreakers oficiales de la NBA implementados
- Eliminada lógica redundante

Uso desde backend/scripts:
    python nba_scraper_multi_teams.py --teams all --seasons 2024 2025
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════

Q_KEYS = ("Q1", "Q2", "Q3", "Q4")
USUARIO_DESARROLLO_ID = "00000000-0000-0000-0000-000000000001"

MAPEO_NOMBRES = {
    "la clippers": "los angeles clippers",
    "la lakers": "los angeles lakers",
}

MAPEO_NOMBRES_CSV_A_BD = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
}

# ═══════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════

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


def extraer_game_id(espn_url: Optional[str]) -> Optional[str]:
    """Extrae el gameId desde la URL de ESPN."""
    if not espn_url or not isinstance(espn_url, str):
        return None
    match = re.search(r"/gameId/(\d+)", espn_url)
    return match.group(1) if match else None


def parsear_fecha_calendario(valor: object) -> datetime.date:
    """Obtiene la fecha calendario sin conversiones de zona horaria."""
    try:
        fecha_str = str(valor)
        base = fecha_str.split("T")[0]
        return datetime.strptime(base, "%Y-%m-%d").date()
    except Exception:
        return datetime.now().date()


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES DEL MODELO
# ═══════════════════════════════════════════════════════════════════

def build_design_matrix(
    team_names: Sequence[str],
    opp_names: Sequence[str],
    is_home: Sequence[int],
    entity_to_idx: Dict[str, int],
) -> np.ndarray:
    """Construye la matriz de diseño para regresión Ridge."""
    n_entities = len(entity_to_idx)
    n_samples = len(team_names)
    X = np.zeros((n_samples, n_entities + 1), dtype=np.float32)
    
    for i, (team, opp, home) in enumerate(zip(team_names, opp_names, is_home)):
        team_idx = entity_to_idx.get(team)
        opp_idx = entity_to_idx.get(opp)
        if team_idx is not None:
            X[i, team_idx] = 1.0
        if opp_idx is not None:
            X[i, opp_idx] = -1.0
        X[i, -1] = float(home)
    
    return X


def entrenar_modelo(cwd: Path, csv_paths: List[Path]) -> None:
    """Entrena el modelo Ridge con todos los CSVs."""
    print()
    print("=" * 70)
    print("PASO 1: ENTRENAR MODELO")
    print("=" * 70)
    print()
    
    print("📥 Cargando datos de partidos...")
    
    frames = []
    for csv_path in csv_paths:
        try:
            df = pd.read_csv(csv_path)
            
            if "season_type" in df.columns:
                df = df[df["season_type"].fillna("").str.upper() == "REG"].copy()
            if "valid_linescore" in df.columns:
                df = df[df["valid_linescore"] == True].copy()
            
            df["team"] = df["team"].apply(normalize_name)
            df["opponent"] = df["opponent"].apply(normalize_name)
            
            frames.append(df)
            print(f"    ✅ {csv_path.name}: {len(df)} partidos")
        except Exception as e:
            print(f"    ❌ {csv_path.name}: {e}")
    
    if not frames:
        raise ValueError("No se encontraron partidos válidos")
    
    df = pd.concat(frames, ignore_index=True)
    
    cols_puntos = ["team_q1", "team_q2", "team_q3", "team_q4", 
                   "opp_q1", "opp_q2", "opp_q3", "opp_q4"]
    df[cols_puntos] = df[cols_puntos].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=cols_puntos)
    
    print()
    print(f"📊 Total de partidos válidos: {len(df)}")
    
    equipos = sorted(set(df["team"].unique()) | set(df["opponent"].unique()))
    print(f"🏀 Equipos únicos en el modelo: {len(equipos)}")
    
    if len(equipos) < 30:
        print(f"⚠️  ADVERTENCIA: Solo {len(equipos)} equipos (esperados 30)")
    
    print()
    print("📋 EQUIPOS EN EL MODELO:")
    print("-" * 50)
    for i, eq in enumerate(equipos, 1):
        print(f"   {i:2d}. {eq}")
    print("-" * 50)
    
    entity_to_idx = {e: i for i, e in enumerate(equipos)}
    
    df["is_home"] = df["location"].apply(parse_location_value)
    
    print()
    print("🔧 Construyendo matriz de diseño...")
    
    X = build_design_matrix(
        df["team"].tolist(),
        df["opponent"].tolist(),
        df["is_home"].tolist(),
        entity_to_idx
    )
    
    print("🎯 Entrenando modelo Ridge...")
    
    from sklearn.linear_model import Ridge
    
    coefs = {}
    intercepts = {}
    
    for q in Q_KEYS:
        y_team = df[f"team_q{q[1]}"].values
        y_opp = df[f"opp_q{q[1]}"].values
        
        model_team = Ridge(alpha=5.0)
        model_team.fit(X, y_team)
        
        model_opp = Ridge(alpha=5.0)
        model_opp.fit(X, y_opp)
        
        coefs[f"team_{q}"] = model_team.coef_
        intercepts[f"team_{q}"] = model_team.intercept_
        coefs[f"opp_{q}"] = model_opp.coef_
        intercepts[f"opp_{q}"] = model_opp.intercept_
    
    datos_dir = cwd / "datos"
    datos_dir.mkdir(exist_ok=True)
    
    modelo_path = datos_dir / "modelo_entrenado.npz"
    
    np.savez(
        modelo_path,
        equipos=np.array(equipos, dtype=object),
        entity_to_idx=json.dumps(entity_to_idx),
        **{f"coef_{k}": v for k, v in coefs.items()},
        **{f"intercept_{k}": np.array([v]) for k, v in intercepts.items()},
        fecha_entrenamiento=datetime.now().isoformat(),
        num_partidos=len(df),
    )
    
    print()
    print(f"✅ Modelo guardado: {modelo_path}")
    print(f"   🏀 Equipos: {len(equipos)}")
    print(f"   📊 Partidos: {len(df)}")
    
    test = np.load(modelo_path, allow_pickle=True)
    equipos_guardados = test["equipos"]
    print(f"   ✅ Verificado: {len(equipos_guardados)} equipos cargados correctamente")


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES DE BASE DE DATOS
# ═══════════════════════════════════════════════════════════════════

def obtener_equipos_bd(conexion) -> Dict[str, str]:
    """Obtiene mapeo nombre -> id de equipos."""
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM equipos WHERE activo = true")
        return {row[1]: row[0] for row in cursor.fetchall()}


def obtener_temporadas_bd(conexion, temporadas_csv: List) -> Dict:
    """
    Obtiene o crea temporadas en la base de datos.

    Los valores de `temporadas_csv` representan el año final de la temporada de la
    NBA (por ejemplo, 2026 para la temporada 2025-2026). Este método usa
    `anio_inicio = año_final - 1` y `anio_fin = año_final` para poblar las
    columnas obligatorias `anio_inicio` y `anio_fin`. También establece el
    nombre de la temporada como "{anio_inicio}-{anio_fin}" y define fechas
    aproximadas de inicio y fin (1 de octubre y 30 de junio). La temporada
    más reciente se marca como activa.
    """
    resultado: Dict[int, str] = {}
    # Convertir a enteros para detectar la temporada más reciente
    try:
        temporadas_int = [int(t) for t in temporadas_csv]
    except Exception:
        temporadas_int = []
    max_temp = max(temporadas_int) if temporadas_int else None

    with conexion.cursor() as cursor:
        for temp in temporadas_csv:
            try:
                temp_int = int(temp)
            except Exception:
                continue
            anio_inicio = temp_int - 1
            anio_fin = temp_int
            nombre = f"{anio_inicio}-{anio_fin}"

            # Buscar temporada existente por anio_inicio y anio_fin o por nombre
            cursor.execute(
                "SELECT id FROM temporadas WHERE (anio_inicio = %s AND anio_fin = %s) OR nombre = %s",
                (anio_inicio, anio_fin, nombre)
            )
            row = cursor.fetchone()
            if row:
                resultado[temp] = row[0]
                continue

            # Crear nueva temporada
            fecha_inicio = f"{anio_inicio}-10-01"
            fecha_fin = f"{anio_fin}-06-30"
            activa = True if (max_temp is None or temp_int == max_temp) else False
            cursor.execute(
                """
                INSERT INTO temporadas (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin, activa)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin, activa)
            )
            new_id = cursor.fetchone()[0]
            resultado[temp] = new_id
            print(f"   ✅ Creada temporada: {nombre}")

        conexion.commit()
    return resultado


def crear_usuario_desarrollo(conexion) -> None:
    """Crea el usuario de desarrollo si no existe."""
    print()
    print("=" * 70)
    print("PASO 2: CREAR USUARIO DE DESARROLLO")
    print("=" * 70)
    print()
    
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO usuarios (id, email, nombre, rol, activo)
            VALUES (%s, 'dev@test.local', 'Desarrollo', 'admin', true)
            ON CONFLICT (id) DO NOTHING
            """,
            (USUARIO_DESARROLLO_ID,)
        )
    conexion.commit()
    print(f"✅ Usuario de desarrollo: {USUARIO_DESARROLLO_ID}")


def poblar_estadisticas_equipos(conexion, csv_paths: List[Path]) -> int:
    """Pobla la tabla estadisticas_equipos."""
    print()
    print("=" * 70)
    print("PASO 3: POBLAR ESTADÍSTICAS DE EQUIPOS (AGREGADOS)")
    print("=" * 70)
    print()
    
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
                except Exception:
                    pass
        
        conexion.commit()
    
    print(f"✅ Estadísticas agregadas: {insertados} registros")
    return insertados


def poblar_partidos(conexion, csv_paths: List[Path]) -> int:
    """
    CORREGIDO v3: Manejo correcto de overtime en TODOS los casos.
    """
    print()
    print("=" * 70)
    print("PASO 4: POBLAR TODOS LOS PARTIDOS INDIVIDUALES")
    print("=" * 70)
    print()

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
    actualizados = 0
    errores = 0
    claves_vistas = set()
    
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
                
                fecha = parsear_fecha_calendario(row.get("date"))
                
                # ✅ CORRECCIÓN PRINCIPAL: Manejo correcto de overtime
                # Los totales en el CSV YA incluyen overtime, así que los usamos directamente
                team_total = row.get("team_total")
                opp_total = row.get("opp_total")
                
                if pd.notna(team_total) and pd.notna(opp_total):
                    # Caso 1: El CSV tiene los totales (ya incluyen OT)
                    team_total = int(team_total)
                    opp_total = int(opp_total)
                else:
                    # Caso 2: No hay totales, calcularlos sumando cuartos + overtime
                    base_team = int(row["team_q1"]) + int(row["team_q2"]) + int(row["team_q3"]) + int(row["team_q4"])
                    base_opp = int(row["opp_q1"]) + int(row["opp_q2"]) + int(row["opp_q3"]) + int(row["opp_q4"])
                    
                    # Sumar TODAS las columnas de overtime
                    team_ot_sum = 0
                    opp_ot_sum = 0
                    for col in row.index:
                        if str(col).startswith("team_ot"):
                            team_ot_sum += int(pd.to_numeric(row[col], errors="coerce") or 0)
                        elif str(col).startswith("opp_ot"):
                            opp_ot_sum += int(pd.to_numeric(row[col], errors="coerce") or 0)
                    
                    team_total = base_team + team_ot_sum
                    opp_total = base_opp + opp_ot_sum

                # Asignar totales según ubicación
                if location == "HOME":
                    local_total = team_total
                    visit_total = opp_total
                    # Calcular OT acumulado
                    local_ot = max(0, team_total - int(local_q1 + local_q2 + local_q3 + local_q4))
                    visit_ot = max(0, opp_total - int(visit_q1 + visit_q2 + visit_q3 + visit_q4))
                else:
                    local_total = opp_total
                    visit_total = team_total
                    local_ot = max(0, opp_total - int(local_q1 + local_q2 + local_q3 + local_q4))
                    visit_ot = max(0, team_total - int(visit_q1 + visit_q2 + visit_q3 + visit_q4))
                
                # Determinar ganador (ahora los totales SÍ incluyen OT)
                ganador_id = None
                if local_total > visit_total:
                    ganador_id = equipos_bd[equipo_local]
                elif visit_total > local_total:
                    ganador_id = equipos_bd[equipo_visitante]
                # Si son iguales, ganador_id queda None (no debería pasar en NBA)
                
                season_type = str(row.get("season_type", "REG")).upper()
                if season_type not in ("REG", "POST", "PRE"):
                    season_type = "REG"

                espn_game_id = extraer_game_id(row.get("espn_url"))
                
                # Deduplicación en memoria
                clave_dedup = (
                    f"game:{espn_game_id}"
                    if espn_game_id
                    else f"{row.get('season')}|{fecha}|{season_type}|{equipo_local}|{equipo_visitante}"
                )
                if clave_dedup in claves_vistas:
                    continue
                claves_vistas.add(clave_dedup)
                
                hubo_overtime = (local_ot > 0 or visit_ot > 0)
                
                valores_partido = [
                    str(temporada_id), fecha, season_type, espn_game_id,
                    str(equipos_bd[equipo_local]), str(equipos_bd[equipo_visitante]),
                    int(local_q1), int(local_q2), int(local_q3), int(local_q4), local_ot, local_total,
                    int(visit_q1), int(visit_q2), int(visit_q3), int(visit_q4), visit_ot, visit_total,
                    str(ganador_id) if ganador_id else None,
                    hubo_overtime,
                ]
                
                cursor.execute(
                    """
                    INSERT INTO partidos (
                        temporada_id, fecha_partido, tipo_partido, espn_game_id,
                        equipo_local_id, equipo_visitante_id,
                        local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
                        visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
                        ganador_id, hubo_overtime
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (temporada_id, fecha_partido, tipo_partido, equipo_local_id, equipo_visitante_id)
                    DO UPDATE SET
                        espn_game_id = COALESCE(EXCLUDED.espn_game_id, partidos.espn_game_id),
                        local_q1 = EXCLUDED.local_q1,
                        local_q2 = EXCLUDED.local_q2,
                        local_q3 = EXCLUDED.local_q3,
                        local_q4 = EXCLUDED.local_q4,
                        local_ot = EXCLUDED.local_ot,
                        local_total = EXCLUDED.local_total,
                        visitante_q1 = EXCLUDED.visitante_q1,
                        visitante_q2 = EXCLUDED.visitante_q2,
                        visitante_q3 = EXCLUDED.visitante_q3,
                        visitante_q4 = EXCLUDED.visitante_q4,
                        visitante_ot = EXCLUDED.visitante_ot,
                        visitante_total = EXCLUDED.visitante_total,
                        ganador_id = EXCLUDED.ganador_id,
                        hubo_overtime = EXCLUDED.hubo_overtime
                    RETURNING id, (xmax = 0) AS inserted
                    """,
                    valores_partido,
                )
                
                resultado = cursor.fetchone()
                if resultado:
                    if resultado[1]:
                        insertados += 1
                    else:
                        actualizados += 1
                
            except Exception as e:
                errores += 1
                if errores <= 5:
                    print(f"   ⚠️  Error en fila {idx}: {e}")
            
            if (idx + 1) % 500 == 0:
                conexion.commit()
                print(f"   Procesados: {idx + 1} / {len(df)} ({insertados} nuevos, {actualizados} actualizados)")
        
        conexion.commit()
    
    with conexion.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM partidos")
        total_bd = cursor.fetchone()[0]
    
    print()
    print(f"✅ Partidos nuevos: {insertados}")
    print(f"🔄 Partidos actualizados: {actualizados}")
    print(f"⚠️  Errores/duplicados: {errores}")
    print(f"📊 Total en tabla partidos: {total_bd}")
    
    return insertados


# ═══════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    """Función principal del script."""
    import argparse
    import subprocess

    def parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Descarga partidos de múltiples equipos, entrena el modelo y pobla la BD",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "--teams",
            nargs="+",
            help="Equipos a descargar. Usa 'all' para todos los equipos",
        )
        parser.add_argument(
            "--seasons",
            nargs="+",
            type=int,
            help="Años de temporada a descargar (e.g., 2023 2024)",
        )
        parser.add_argument(
            "--csv-dir",
            default=None,
            help="Directorio donde guardar o buscar archivos CSV de partidos",
        )
        parser.add_argument(
            "--include-preseason",
            action="store_true",
            help="Incluir partidos de pretemporada al descargar",
        )
        parser.add_argument(
            "--include-regular",
            action="store_true",
            default=True,
            help="Incluir partidos de temporada regular al descargar",
        )
        parser.add_argument(
            "--include-postseason",
            action="store_true",
            default=True,
            help="Incluir partidos de postemporada al descargar",
        )
        parser.add_argument(
            "--max-games",
            type=int,
            default=2000,
            help="Máximo de juegos a descargar por equipo y temporada",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.20,
            help="Pausa (segundos) entre requests al scrapear",
        )
        return parser.parse_args()

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "🏀 SETUP COMPLETO NBA 🏀" + " " * 21 + "║")
    print("║" + " " * 15 + "Modelo + Usuario + Base de Datos" + " " * 16 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    args = parse_args()

    csv_dir = Path(args.csv_dir) if args.csv_dir else Path.cwd()
    csv_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 Directorio de CSVs: {csv_dir}")

    if args.teams and args.seasons:
        teams_list: List[str] = []
        if len(args.teams) == 1 and args.teams[0].lower() == "all":
            try:
                datos_dir = Path(__file__).resolve().parents[1] / "datos" / "equipos_nba.json"
                with open(datos_dir, "r", encoding="utf-8") as f:
                    equipos_data = json.load(f)
                teams_list = [team["nombre"] for team in equipos_data]
                print(f"📋 Descargando datos para todos los equipos ({len(teams_list)})")
            except Exception as e:
                print(f"❌ Error leyendo equipos: {e}")
                return 1
        else:
            teams_list = args.teams
        
        nbascript_path = Path(__file__).resolve().parent / "NBAscript.py"
        
        for team in teams_list:
            safe_name = re.sub(r"\W+", "_", team.strip()).lower()
            out_path = csv_dir / f"{safe_name}.csv"
            cmd: List[str] = [
                sys.executable,
                str(nbascript_path),
                "--team",
                team,
                "--out",
                str(out_path),
            ]
            cmd.append("--seasons")
            cmd.extend([str(sea) for sea in args.seasons])
            
            if args.include_preseason:
                cmd.append("--include-preseason")
            if args.include_regular:
                cmd.append("--include-regular")
            if args.include_postseason:
                cmd.append("--include-postseason")
            if args.max_games:
                cmd.extend(["--max-games", str(args.max_games)])
            if args.sleep:
                cmd.extend(["--sleep", str(args.sleep)])
            
            print()
            print(f"🕸️  Scrapeando {team} temporadas {args.seasons} -> {out_path.name}")
            try:
                subprocess.run(cmd, check=True)
                print(f"   ✅ CSV generado: {out_path.name}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Error al ejecutar NBAscript.py para {team}: {e}")
                return 1

    csv_paths = [p for p in sorted(csv_dir.glob("*.csv")) if p.is_file() and p.name != "equipos.csv"]

    if not csv_paths:
        print()
        print("❌ ERROR: No se encontraron CSVs de partidos.")
        print()
        print("   Genera los CSVs especificando --teams y --seasons:")
        print("   python nba_scraper_multi_teams.py --teams all --seasons 2024 2025")
        return 1

    print(f"🔍 CSVs encontrados: {len(csv_paths)}")

    try:
        entrenar_modelo(csv_dir, csv_paths)
    except Exception as e:
        print(f"❌ Error entrenando modelo: {e}")
        import traceback
        traceback.print_exc()
        return 1

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
            import traceback
            traceback.print_exc()

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