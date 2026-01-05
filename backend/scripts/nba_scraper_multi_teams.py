#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nba_scraper_multi_teams.py — Scraper multi-equipos para descargar partidos NBA
y generar CSVs con estadísticas completas.

Este script se usa para obtener los datos de todos los equipos y guardarlos
en CSVs. Luego, setup_completo.py puede consumir esos CSVs para poblar la BD.

Uso desde la carpeta backend/scripts:
    python nba_scraper_multi_teams.py
"""

from __future__ import annotations

import json
import os
import re
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


def asegurar_unicidad_partidos(conexion) -> None:
    """
    CORREGIDO: Asegura columna espn_game_id y crea CONSTRAINTS únicos.
    
    El problema anterior era usar índices parciales que PostgreSQL NO permite
    en ON CONFLICT. La solución es:
    1. Usar UNIQUE CONSTRAINT (no índice) para partido_exacto
    2. Manejar espn_game_id con lógica en código, no en constraint parcial
    """
    print("   🔧 Configurando constraints de unicidad...")
    
    with conexion.cursor() as cursor:
        # 1. Agregar columna espn_game_id si no existe
        cursor.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS espn_game_id TEXT")
        
        # 2. Eliminar duplicados existentes (mantener el primero)
        print("   🧹 Limpiando duplicados existentes...")
        cursor.execute(
            """
            WITH duplicados AS (
                SELECT id,
                    ROW_NUMBER() OVER (
                        PARTITION BY temporada_id, fecha_partido, tipo_partido,
                                     equipo_local_id, equipo_visitante_id
                        ORDER BY id
                    ) AS rn
                FROM partidos
            )
            DELETE FROM partidos
            WHERE id IN (SELECT id FROM duplicados WHERE rn > 1)
            """
        )
        eliminados = cursor.rowcount
        if eliminados > 0:
            print(f"   🗑️  Eliminados {eliminados} duplicados")
        
        # 3. Eliminar índices/constraints antiguos que causan conflicto
        print("   🔄 Actualizando constraints...")
        
        # Eliminar índice parcial problemático (si existe)
        cursor.execute("DROP INDEX IF EXISTS partidos_unq_espn_game_id")
        cursor.execute("DROP INDEX IF EXISTS partidos_unq_partido_exacto")
        
        # Eliminar constraints antiguos (si existen)
        cursor.execute("""
            DO $$ 
            BEGIN
                ALTER TABLE partidos DROP CONSTRAINT IF EXISTS partidos_partido_exacto_key;
                ALTER TABLE partidos DROP CONSTRAINT IF EXISTS partidos_espn_game_id_key;
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END $$;
        """)
        
        # 4. Crear UNIQUE CONSTRAINT para partido exacto (funciona con ON CONFLICT)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'partidos_partido_exacto_key'
                ) THEN
                    ALTER TABLE partidos ADD CONSTRAINT partidos_partido_exacto_key
                    UNIQUE (temporada_id, fecha_partido, tipo_partido, equipo_local_id, equipo_visitante_id);
                END IF;
            END $$;
        """)
        
        # 5. Crear índice NO parcial para espn_game_id (para búsquedas rápidas)
        # NOTA: No usamos UNIQUE porque puede haber NULLs duplicados
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_partidos_espn_game_id 
            ON partidos (espn_game_id) 
            WHERE espn_game_id IS NOT NULL
        """)
    
    conexion.commit()
    print("   ✅ Constraints configurados correctamente")


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
            
            # Filtrar por temporada regular y linescore válido
            if "season_type" in df.columns:
                df = df[df["season_type"].fillna("").str.upper() == "REG"].copy()
            if "valid_linescore" in df.columns:
                df = df[df["valid_linescore"] == True].copy()
            
            # Normalizar nombres
            df["team"] = df["team"].apply(normalize_name)
            df["opponent"] = df["opponent"].apply(normalize_name)
            
            frames.append(df)
            print(f"    ✅ {csv_path.name}: {len(df)} partidos")
        except Exception as e:
            print(f"    ❌ {csv_path.name}: {e}")
    
    if not frames:
        raise ValueError("No se encontraron partidos válidos")
    
    df = pd.concat(frames, ignore_index=True)
    
    # Filtrar partidos válidos
    cols_puntos = ["team_q1", "team_q2", "team_q3", "team_q4", 
                   "opp_q1", "opp_q2", "opp_q3", "opp_q4"]
    df[cols_puntos] = df[cols_puntos].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=cols_puntos)
    
    print()
    print(f"📊 Total de partidos válidos: {len(df)}")
    
    # Obtener equipos únicos
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
    
    # Crear índices
    entity_to_idx = {e: i for i, e in enumerate(equipos)}
    
    # Preparar datos
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
    
    # Entrenar para cada cuarto
    from sklearn.linear_model import Ridge
    
    coefs = {}
    intercepts = {}
    
    for q in Q_KEYS:
        y_team = df[f"team_q{q[1]}"].values
        y_opp = df[f"opp_q{q[1]}"].values
        
        # Modelo para equipo
        model_team = Ridge(alpha=5.0)
        model_team.fit(X, y_team)
        
        # Modelo para oponente
        model_opp = Ridge(alpha=5.0)
        model_opp.fit(X, y_opp)
        
        coefs[f"team_{q}"] = model_team.coef_
        intercepts[f"team_{q}"] = model_team.intercept_
        coefs[f"opp_{q}"] = model_opp.coef_
        intercepts[f"opp_{q}"] = model_opp.intercept_
    
    # Guardar modelo
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
    
    # Verificar
    test = np.load(modelo_path, allow_pickle=True)
    equipos_guardados = test["equipos"]
    print(f"   ✅ Verificado: {len(equipos_guardados)} equipos cargados correctamente")


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════

def obtener_equipos_bd(conexion) -> Dict[str, str]:
    """Obtiene mapeo nombre -> id de equipos."""
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM equipos WHERE activo = true")
        return {row[1]: row[0] for row in cursor.fetchall()}


def obtener_temporadas_bd(conexion, temporadas_csv: List) -> Dict:
    """Obtiene o crea temporadas en la BD."""
    resultado = {}
    
    with conexion.cursor() as cursor:
        for temp in temporadas_csv:
            temp_str = str(temp)
            
            # Buscar temporada existente
            cursor.execute(
                "SELECT id FROM temporadas WHERE nombre LIKE %s OR nombre = %s",
                (f"%{temp_str}%", temp_str)
            )
            row = cursor.fetchone()
            
            if row:
                resultado[temp] = row[0]
            else:
                # Crear temporada
                nombre = f"{temp_str}-{int(temp_str)+1}"
                fecha_inicio = f"{temp_str}-10-01"
                fecha_fin = f"{int(temp_str)+1}-06-30"
                
                cursor.execute(
                    """
                    INSERT INTO temporadas (nombre, fecha_inicio, fecha_fin, activa)
                    VALUES (%s, %s, %s, true)
                    RETURNING id
                    """,
                    (nombre, fecha_inicio, fecha_fin)
                )
                resultado[temp] = cursor.fetchone()[0]
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
    """
    CORREGIDO: Pobla la tabla partidos con TODOS los partidos individuales.
    
    Ahora usa ON CONFLICT con el CONSTRAINT partido_exacto_key que SÍ funciona.
    """
    print()
    print("=" * 70)
    print("PASO 4: POBLAR TODOS LOS PARTIDOS INDIVIDUALES")
    print("=" * 70)
    print()
    
    # IMPORTANTE: Asegurar constraints ANTES de insertar
    asegurar_unicidad_partidos(conexion)

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
                
                def sumar_ot(prefix: str) -> int:
                    ot_cols = [col for col in row.index if str(col).startswith(f"{prefix}_ot")]
                    if not ot_cols:
                        return 0
                    valores = [row.get(col) for col in ot_cols]
                    return int(pd.to_numeric(valores, errors="coerce").fillna(0).sum())

                team_total = row.get("team_total")
                opp_total = row.get("opp_total")
                if pd.notna(team_total) and pd.notna(opp_total):
                    team_total = int(team_total)
                    opp_total = int(opp_total)
                else:
                    team_total = int(local_q1 + local_q2 + local_q3 + local_q4) if location == "HOME" else int(visit_q1 + visit_q2 + visit_q3 + visit_q4)
                    opp_total = int(visit_q1 + visit_q2 + visit_q3 + visit_q4) if location == "HOME" else int(local_q1 + local_q2 + local_q3 + local_q4)

                if location == "HOME":
                    local_total = team_total
                    visit_total = opp_total
                    local_ot = sumar_ot("team")
                    visit_ot = sumar_ot("opp")
                else:
                    local_total = opp_total
                    visit_total = team_total
                    local_ot = sumar_ot("opp")
                    visit_ot = sumar_ot("team")

                if local_ot == 0 and visit_ot == 0:
                    local_ot = max(0, local_total - int(local_q1 + local_q2 + local_q3 + local_q4))
                    visit_ot = max(0, visit_total - int(visit_q1 + visit_q2 + visit_q3 + visit_q4))
                
                # Determinar ganador
                ganador_id = None
                if local_total > visit_total:
                    ganador_id = equipos_bd[equipo_local]
                elif visit_total > local_total:
                    ganador_id = equipos_bd[equipo_visitante]
                
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
                    errores += 1
                    continue
                claves_vistas.add(clave_dedup)
                
                # CORREGIDO: Usar solo ON CONFLICT con el constraint que SÍ existe
                valores_partido = [
                    str(temporada_id), fecha, season_type, espn_game_id,
                    str(equipos_bd[equipo_local]), str(equipos_bd[equipo_visitante]),
                    int(local_q1), int(local_q2), int(local_q3), int(local_q4), local_ot, local_total,
                    int(visit_q1), int(visit_q2), int(visit_q3), int(visit_q4), visit_ot, visit_total,
                    str(ganador_id) if ganador_id else None,
                    row.get("ot_count", 0) > 0 if "ot_count" in row else False,
                ]
                
                # QUERY CORREGIDO: Usa el constraint correcto
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
                    if resultado[1]:  # inserted = true (nuevo)
                        insertados += 1
                    else:  # actualizado
                        actualizados += 1
                
            except Exception as e:
                errores += 1
                if errores <= 5:
                    print(f"   ⚠️  Error en fila {idx}: {e}")
            
            # Progreso y commit periódico
            if (idx + 1) % 500 == 0:
                conexion.commit()
                print(f"   Procesados: {idx + 1} / {len(df)} ({insertados} nuevos, {actualizados} actualizados)")
        
        conexion.commit()
    
    # Total en BD
    with conexion.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM partidos")
        total_bd = cursor.fetchone()[0]
    
    print()
    print(f"✅ Partidos nuevos: {insertados}")
    print(f"🔄 Partidos actualizados: {actualizados}")
    print(f"⚠️  Errores/duplicados en memoria: {errores}")
    print(f"📊 Total en tabla partidos: {total_bd}")
    
    return insertados


# ══════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main() -> int:
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 16 + "🏀 NBA SCRAPER MULTI TEAMS 🏀" + " " * 16 + "║")
    print("║" + " " * 14 + "Descarga partidos y genera CSVs" + " " * 15 + "║")
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
        print("   Ejecuta este script DESDE la carpeta backend/scripts:")
        print("   cd C:\\Users\\ING-ERIK\\Documents\\Proyectos\\AnalyticsPredict\\backend\\scripts")
        print("   python nba_scraper_multi_teams.py")
        return 1
    
    print(f"📁 CSVs encontrados: {len(csv_paths)}")
    
    # PASO 1: Entrenar modelo
    try:
        entrenar_modelo(cwd, csv_paths)
    except Exception as e:
        print(f"❌ Error entrenando modelo: {e}")
        import traceback
        traceback.print_exc()
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
            import traceback
            traceback.print_exc()
    
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
