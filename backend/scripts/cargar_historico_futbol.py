#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de carga histórica de datos de fútbol desde Sofascore.

VERSIÓN 3 - CORREGIDA:
- Verifica y agrega columnas faltantes automáticamente
- Funciona con el esquema real de la BD
- 100% independiente, no depende de otros módulos

Uso:
    python cargar_historico_futbol_v3.py --liga laliga --temporadas 2024-25 --verbose
    python cargar_historico_futbol_v3.py --liga premier --temporadas 2024-25,2023-24
    python cargar_historico_futbol_v3.py --liga todas --temporadas 2024-25

Requisitos:
    pip install psycopg[binary] python-dotenv curl_cffi
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Cargar .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

LIGAS_SOFASCORE = {
    'laliga': 8,
    'premier': 17,
    'bundesliga': 35,
    'seriea': 23,
    'ligue1': 34,
    'champions': 7,
    'europa': 679,
    'conference': 17015,
    'copa_rey': 329,
    'fa_cup': 29,
    'dfb_pokal': 44,
    'coppa_italia': 327,
    'coupe_france': 335,
}

MAPEO_ESTADOS = {
    'finished': 'FINALIZADO',
    'notstarted': 'PROGRAMADO',
    'inprogress': 'EN_VIVO',
    'canceled': 'CANCELADO',
    'postponed': 'POSPUESTO',
    'suspended': 'SUSPENDIDO',
}

SOFASCORE_API_BASE = "https://api.sofascore.com/api/v1"

# ============================================================================
# CLIENTE HTTP
# ============================================================================

class SofascoreClientSimple:
    """Cliente HTTP para Sofascore con soporte para curl_cffi."""
    
    def __init__(self, min_intervalo: float = 1.0):
        self.min_intervalo = min_intervalo
        self.ultima_peticion = 0
        self.session = None
        self.usar_curl_cffi = False
        
        try:
            from curl_cffi import requests as curl_requests
            self.session = curl_requests.Session(impersonate="chrome")
            self.usar_curl_cffi = True
            logger.info("✅ Usando curl_cffi (bypass anti-bot)")
        except ImportError:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.sofascore.com/',
            })
            logger.warning("⚠️ curl_cffi no instalado. Puede haber bloqueos 403.")
    
    def _rate_limit(self):
        ahora = time.time()
        transcurrido = ahora - self.ultima_peticion
        if transcurrido < self.min_intervalo:
            time.sleep(self.min_intervalo - transcurrido)
        self.ultima_peticion = time.time()
    
    def get(self, endpoint: str, reintentos: int = 3) -> Optional[Dict]:
        url = f"{SOFASCORE_API_BASE}{endpoint}"
        
        for intento in range(reintentos):
            self._rate_limit()
            
            try:
                if self.usar_curl_cffi:
                    response = self.session.get(url)
                else:
                    response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    logger.warning(f"  403 en {endpoint} (intento {intento + 1}/{reintentos})")
                    time.sleep(2 ** intento)
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"  HTTP {response.status_code} en {endpoint}")
                    
            except Exception as e:
                logger.error(f"  Error en {endpoint}: {e}")
                time.sleep(1)
        
        return None
    
    def cerrar(self):
        if hasattr(self.session, 'close'):
            self.session.close()


# ============================================================================
# CONEXIÓN A BD
# ============================================================================

def obtener_conexion():
    """Obtiene conexión a la BD."""
    try:
        import psycopg
    except ImportError:
        logger.error("psycopg no instalado. Ejecuta: pip install psycopg[binary]")
        sys.exit(1)
    
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        logger.error("DATABASE_URL no configurada en .env")
        sys.exit(1)
    
    if "sslmode=" not in database_url:
        sep = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{sep}sslmode=require"
    
    try:
        return psycopg.connect(database_url)
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")
        sys.exit(1)


# ============================================================================
# VERIFICACIÓN Y MIGRACIÓN DE ESQUEMA
# ============================================================================

def verificar_y_migrar_esquema(conn):
    """Verifica que el esquema tenga todas las columnas necesarias y las agrega si faltan."""
    
    logger.info("🔍 Verificando esquema de BD...")
    
    migraciones = []
    
    with conn.cursor() as cur:
        # Verificar columna sofascore_season_id en temporadas_futbol
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'temporadas_futbol' AND column_name = 'sofascore_season_id'
        """)
        if not cur.fetchone():
            migraciones.append({
                'tabla': 'temporadas_futbol',
                'columna': 'sofascore_season_id',
                'sql': 'ALTER TABLE temporadas_futbol ADD COLUMN sofascore_season_id INTEGER'
            })
        
        # Verificar columna nombre_comun en equipos_futbol (puede faltar)
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'equipos_futbol' AND column_name = 'nombre_comun'
        """)
        if not cur.fetchone():
            migraciones.append({
                'tabla': 'equipos_futbol',
                'columna': 'nombre_comun',
                'sql': 'ALTER TABLE equipos_futbol ADD COLUMN nombre_comun VARCHAR(50)'
            })
        
        # Verificar columna sofascore_match_id en partidos_futbol
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'partidos_futbol' AND column_name = 'sofascore_match_id'
        """)
        if not cur.fetchone():
            migraciones.append({
                'tabla': 'partidos_futbol',
                'columna': 'sofascore_match_id',
                'sql': 'ALTER TABLE partidos_futbol ADD COLUMN sofascore_match_id INTEGER'
            })
        
        # Verificar columna fuente_datos en partidos_futbol
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'partidos_futbol' AND column_name = 'fuente_datos'
        """)
        if not cur.fetchone():
            migraciones.append({
                'tabla': 'partidos_futbol',
                'columna': 'fuente_datos',
                'sql': "ALTER TABLE partidos_futbol ADD COLUMN fuente_datos VARCHAR(50) DEFAULT 'SOFASCORE'"
            })
    
    # Aplicar migraciones
    if migraciones:
        logger.info(f"📝 Aplicando {len(migraciones)} migraciones de esquema...")
        
        for mig in migraciones:
            try:
                with conn.cursor() as cur:
                    cur.execute(mig['sql'])
                conn.commit()
                logger.info(f"   ✅ Agregada columna {mig['tabla']}.{mig['columna']}")
            except Exception as e:
                conn.rollback()
                logger.error(f"   ❌ Error agregando {mig['tabla']}.{mig['columna']}: {e}")
                return False
    else:
        logger.info("   ✅ Esquema OK - No se requieren migraciones")
    
    return True


# ============================================================================
# FUNCIONES DE BD
# ============================================================================

def verificar_competicion(conn, sofascore_id: int) -> Optional[Dict]:
    """Verifica que la competición existe y tiene sofascore_id configurado."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, codigo, nombre, sofascore_id 
            FROM competiciones_futbol 
            WHERE sofascore_id = %s AND activo = TRUE
        """, (sofascore_id,))
        row = cur.fetchone()
        
        if row:
            return {
                'id': row[0],
                'codigo': row[1],
                'nombre': row[2],
                'sofascore_id': row[3]
            }
    return None


def obtener_o_crear_temporada(conn, competicion_id, nombre: str, 
                               sofascore_season_id: int) -> Optional[str]:
    """Obtiene o crea una temporada."""
    with conn.cursor() as cur:
        # Buscar existente por nombre o sofascore_season_id
        cur.execute("""
            SELECT id, sofascore_season_id FROM temporadas_futbol
            WHERE competicion_id = %s AND nombre = %s
        """, (competicion_id, nombre))
        row = cur.fetchone()
        
        if row:
            # Actualizar sofascore_season_id si no lo tiene
            if row[1] is None and sofascore_season_id:
                cur.execute("""
                    UPDATE temporadas_futbol 
                    SET sofascore_season_id = %s
                    WHERE id = %s
                """, (sofascore_season_id, row[0]))
                conn.commit()
            return row[0]
        
        # Buscar por sofascore_season_id
        cur.execute("""
            SELECT id FROM temporadas_futbol
            WHERE competicion_id = %s AND sofascore_season_id = %s
        """, (competicion_id, sofascore_season_id))
        row = cur.fetchone()
        
        if row:
            return row[0]
        
        # Crear nueva temporada
        try:
            partes = nombre.replace('/', '-').split('-')
            anio_inicio = int(partes[0]) if len(partes[0]) == 4 else int(f"20{partes[0]}")
            if len(partes) > 1:
                anio_fin_str = partes[1]
                anio_fin = int(anio_fin_str) if len(anio_fin_str) == 4 else int(f"20{anio_fin_str}")
            else:
                anio_fin = anio_inicio + 1
            
            cur.execute("""
                INSERT INTO temporadas_futbol (
                    competicion_id, nombre, anio_inicio, anio_fin,
                    fecha_inicio, fecha_fin, sofascore_season_id, activa
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (
                competicion_id, nombre, anio_inicio, anio_fin,
                f"{anio_inicio}-08-01", f"{anio_fin}-06-30",
                sofascore_season_id
            ))
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"    ✅ Temporada creada: {nombre}")
            return nuevo_id
        except Exception as e:
            conn.rollback()
            logger.error(f"    ❌ Error creando temporada: {e}")
            return None


def obtener_o_crear_equipo(conn, sofascore_id: int, nombre: str, 
                           nombre_corto: str, competicion_id) -> Optional[str]:
    """Obtiene o crea un equipo."""
    with conn.cursor() as cur:
        # Buscar por sofascore_id
        cur.execute("""
            SELECT id FROM equipos_futbol WHERE sofascore_id = %s
        """, (sofascore_id,))
        row = cur.fetchone()
        
        if row:
            return row[0]
        
        # Crear nuevo
        try:
            nombre_comun = nombre.lower().strip()[:50] if nombre else ''
            nombre_corto_val = (nombre_corto or nombre[:50])[:50] if nombre else ''
            
            cur.execute("""
                INSERT INTO equipos_futbol (
                    nombre, nombre_corto, nombre_comun,
                    sofascore_id, competicion_principal_id, activo
                ) VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (
                nombre[:100] if nombre else 'Desconocido',
                nombre_corto_val,
                nombre_comun,
                sofascore_id, 
                competicion_id
            ))
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            return nuevo_id
        except Exception as e:
            conn.rollback()
            # Intentar buscar por nombre
            cur.execute("""
                SELECT id FROM equipos_futbol 
                WHERE nombre = %s OR nombre_corto = %s
                LIMIT 1
            """, (nombre, nombre_corto))
            row = cur.fetchone()
            if row:
                # Actualizar sofascore_id
                try:
                    cur.execute("""
                        UPDATE equipos_futbol SET sofascore_id = %s WHERE id = %s
                    """, (sofascore_id, row[0]))
                    conn.commit()
                except:
                    conn.rollback()
                return row[0]
            logger.debug(f"    Error creando equipo {nombre}: {e}")
            return None


def insertar_o_actualizar_partido(conn, datos: Dict, competicion_id, 
                                   temporada_id, equipos_map: Dict) -> Tuple[bool, bool]:
    """
    Inserta o actualiza un partido.
    Returns: (exito, fue_insercion)
    """
    try:
        sofascore_id = datos.get('id')
        home_team = datos.get('homeTeam', {})
        away_team = datos.get('awayTeam', {})
        
        home_sofascore_id = home_team.get('id')
        away_sofascore_id = away_team.get('id')
        
        if not all([sofascore_id, home_sofascore_id, away_sofascore_id]):
            return False, False
        
        equipo_local_id = equipos_map.get(home_sofascore_id)
        equipo_visitante_id = equipos_map.get(away_sofascore_id)
        
        if not equipo_local_id or not equipo_visitante_id:
            return False, False
        
        # Extraer datos
        timestamp = datos.get('startTimestamp', 0)
        fecha_partido = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
        home_score = datos.get('homeScore', {})
        away_score = datos.get('awayScore', {})
        
        local_goles_1t = home_score.get('period1')
        local_goles_2t = home_score.get('period2')
        local_goles_total = home_score.get('current') or home_score.get('normaltime')
        
        visitante_goles_1t = away_score.get('period1')
        visitante_goles_2t = away_score.get('period2')
        visitante_goles_total = away_score.get('current') or away_score.get('normaltime')
        
        estado_sofascore = datos.get('status', {}).get('type', 'notstarted')
        estado = MAPEO_ESTADOS.get(estado_sofascore.lower(), 'PROGRAMADO')
        
        jornada = datos.get('roundInfo', {}).get('round')
        
        # Calcular ganador
        ganador_id = None
        if local_goles_total is not None and visitante_goles_total is not None:
            if local_goles_total > visitante_goles_total:
                ganador_id = equipo_local_id
            elif visitante_goles_total > local_goles_total:
                ganador_id = equipo_visitante_id
        
        with conn.cursor() as cur:
            # Verificar si existe
            cur.execute("""
                SELECT id FROM partidos_futbol WHERE sofascore_match_id = %s
            """, (sofascore_id,))
            existente = cur.fetchone()
            
            if existente:
                # Actualizar
                cur.execute("""
                    UPDATE partidos_futbol SET
                        local_goles_1t = COALESCE(%s, local_goles_1t),
                        local_goles_2t = COALESCE(%s, local_goles_2t),
                        local_goles_total = COALESCE(%s, local_goles_total),
                        visitante_goles_1t = COALESCE(%s, visitante_goles_1t),
                        visitante_goles_2t = COALESCE(%s, visitante_goles_2t),
                        visitante_goles_total = COALESCE(%s, visitante_goles_total),
                        estado = %s::estado_partido_futbol,
                        ganador_id = %s,
                        actualizado_en = NOW()
                    WHERE sofascore_match_id = %s
                """, (
                    local_goles_1t, local_goles_2t, local_goles_total,
                    visitante_goles_1t, visitante_goles_2t, visitante_goles_total,
                    estado, ganador_id, sofascore_id
                ))
                conn.commit()
                return True, False
            else:
                # Insertar
                cur.execute("""
                    INSERT INTO partidos_futbol (
                        competicion_id, temporada_id, 
                        equipo_local_id, equipo_visitante_id,
                        fecha_partido, fecha_partido_local, jornada, estado,
                        local_goles_1t, local_goles_2t, local_goles_total,
                        visitante_goles_1t, visitante_goles_2t, visitante_goles_total,
                        ganador_id, sofascore_match_id, fuente_datos
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s::estado_partido_futbol,
                        %s, %s, %s, %s, %s, %s, %s, %s, 'SOFASCORE'
                    )
                """, (
                    competicion_id, temporada_id,
                    equipo_local_id, equipo_visitante_id,
                    fecha_partido, fecha_partido.date(), jornada, estado,
                    local_goles_1t, local_goles_2t, local_goles_total,
                    visitante_goles_1t, visitante_goles_2t, visitante_goles_total,
                    ganador_id, sofascore_id
                ))
                conn.commit()
                return True, True
                
    except Exception as e:
        conn.rollback()
        logger.debug(f"    Error partido {datos.get('id')}: {e}")
        return False, False


def actualizar_estadisticas_partido(conn, sofascore_id: int, stats: Dict) -> bool:
    """Actualiza estadísticas de un partido."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE partidos_futbol SET
                    local_corners_1t = COALESCE(%s, local_corners_1t),
                    local_corners_2t = COALESCE(%s, local_corners_2t),
                    local_corners_total = COALESCE(%s, local_corners_total),
                    visitante_corners_1t = COALESCE(%s, visitante_corners_1t),
                    visitante_corners_2t = COALESCE(%s, visitante_corners_2t),
                    visitante_corners_total = COALESCE(%s, visitante_corners_total),
                    local_disparos_total = COALESCE(%s, local_disparos_total),
                    local_disparos_arco = COALESCE(%s, local_disparos_arco),
                    visitante_disparos_total = COALESCE(%s, visitante_disparos_total),
                    visitante_disparos_arco = COALESCE(%s, visitante_disparos_arco),
                    local_posesion = COALESCE(%s, local_posesion),
                    visitante_posesion = COALESCE(%s, visitante_posesion),
                    local_xg = COALESCE(%s, local_xg),
                    visitante_xg = COALESCE(%s, visitante_xg),
                    datos_corners_completos = TRUE,
                    datos_disparos_completos = TRUE,
                    actualizado_en = NOW()
                WHERE sofascore_match_id = %s
            """, (
                stats.get('corners_local_1t'),
                stats.get('corners_local_2t'),
                stats.get('corners_local_total'),
                stats.get('corners_visitante_1t'),
                stats.get('corners_visitante_2t'),
                stats.get('corners_visitante_total'),
                stats.get('disparos_local_total'),
                stats.get('disparos_local_arco'),
                stats.get('disparos_visitante_total'),
                stats.get('disparos_visitante_arco'),
                stats.get('posesion_local'),
                stats.get('posesion_visitante'),
                stats.get('xg_local'),
                stats.get('xg_visitante'),
                sofascore_id
            ))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.debug(f"    Error stats: {e}")
        return False


# ============================================================================
# FUNCIONES DE SOFASCORE
# ============================================================================

def obtener_temporadas_sofascore(cliente: SofascoreClientSimple, liga_id: int) -> List[Dict]:
    """Obtiene las temporadas disponibles de una liga."""
    datos = cliente.get(f'/unique-tournament/{liga_id}/seasons')
    if datos:
        return datos.get('seasons', [])
    return []


def buscar_temporada_sofascore(temporadas: List[Dict], nombre_buscado: str) -> Optional[Dict]:
    """Busca una temporada por nombre."""
    nombre_buscado = nombre_buscado.lower().replace(' ', '').replace('-', '')
    
    for temp in temporadas:
        nombre = temp.get('name', '').lower().replace(' ', '').replace('-', '').replace('/', '')
        year = str(temp.get('year', ''))
        
        # Comparar
        if nombre_buscado in nombre or nombre in nombre_buscado:
            return temp
        # Por año: "202425" en "laliga24/25"
        if nombre_buscado[-4:] in nombre or nombre_buscado[-2:] in nombre[-2:]:
            return temp
        # Por año final
        if year and nombre_buscado.endswith(year[-2:]):
            return temp
    
    return None


def obtener_partidos_temporada(cliente: SofascoreClientSimple, 
                                liga_id: int, season_id: int,
                                verbose: bool = False) -> List[Dict]:
    """Obtiene todos los partidos de una temporada."""
    todos = []
    page = 0
    max_pages = 50
    
    while page < max_pages:
        datos = cliente.get(f'/unique-tournament/{liga_id}/season/{season_id}/events/last/{page}')
        
        if not datos:
            break
        
        events = datos.get('events', [])
        if not events:
            break
        
        todos.extend(events)
        page += 1
        
        if verbose:
            print(f"\r    Obteniendo partidos: página {page}, total {len(todos)}...", end='', flush=True)
    
    if verbose:
        print()
    
    return todos


def obtener_estadisticas_partido(cliente: SofascoreClientSimple, evento_id: int) -> Optional[Dict]:
    """Obtiene estadísticas de un partido."""
    datos = cliente.get(f'/event/{evento_id}/statistics')
    if not datos:
        return None
    
    statistics = datos.get('statistics', [])
    if not statistics:
        return None
    
    resultado = {}
    
    for periodo in statistics:
        period_name = periodo.get('period', 'ALL')
        groups = periodo.get('groups', [])
        
        for group in groups:
            for item in group.get('statisticsItems', []):
                nombre = item.get('name', '')
                home = item.get('home')
                away = item.get('away')
                
                if nombre == 'Corner kicks':
                    if period_name == 'ALL':
                        resultado['corners_local_total'] = home
                        resultado['corners_visitante_total'] = away
                    elif period_name == '1ST':
                        resultado['corners_local_1t'] = home
                        resultado['corners_visitante_1t'] = away
                    elif period_name == '2ND':
                        resultado['corners_local_2t'] = home
                        resultado['corners_visitante_2t'] = away
                
                elif nombre == 'Total shots' and period_name == 'ALL':
                    resultado['disparos_local_total'] = home
                    resultado['disparos_visitante_total'] = away
                
                elif nombre == 'Shots on target' and period_name == 'ALL':
                    resultado['disparos_local_arco'] = home
                    resultado['disparos_visitante_arco'] = away
                
                elif nombre == 'Ball possession' and period_name == 'ALL':
                    try:
                        if isinstance(home, str):
                            home = float(home.replace('%', ''))
                        if isinstance(away, str):
                            away = float(away.replace('%', ''))
                        resultado['posesion_local'] = home
                        resultado['posesion_visitante'] = away
                    except:
                        pass
                
                elif nombre == 'Expected goals' and period_name == 'ALL':
                    try:
                        resultado['xg_local'] = float(home) if home else None
                        resultado['xg_visitante'] = float(away) if away else None
                    except:
                        pass
    
    return resultado if resultado else None


# ============================================================================
# FUNCIÓN PRINCIPAL DE CARGA
# ============================================================================

def cargar_temporada(conn, cliente: SofascoreClientSimple,
                     liga_id: int, temporada_nombre: str,
                     competicion: Dict, con_estadisticas: bool = True,
                     verbose: bool = False) -> Dict[str, int]:
    """Carga todos los partidos de una temporada."""
    
    resultado = {
        'partidos_insertados': 0,
        'partidos_actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0
    }
    
    competicion_id = competicion['id']
    
    # 1. Obtener temporadas de Sofascore
    logger.info(f"  Obteniendo temporadas de Sofascore...")
    temporadas = obtener_temporadas_sofascore(cliente, liga_id)
    
    if not temporadas:
        logger.error(f"  ❌ No se pudieron obtener temporadas")
        resultado['errores'] = 1
        return resultado
    
    # 2. Buscar la temporada solicitada
    temporada_sf = buscar_temporada_sofascore(temporadas, temporada_nombre)
    
    if not temporada_sf:
        logger.warning(f"  ⚠️ Temporada '{temporada_nombre}' no encontrada")
        logger.info(f"  Disponibles: {[t.get('name') for t in temporadas[:5]]}")
        resultado['errores'] = 1
        return resultado
    
    sofascore_season_id = temporada_sf.get('id')
    season_name = temporada_sf.get('name', temporada_nombre)
    logger.info(f"  ✅ Temporada: {season_name} (ID: {sofascore_season_id})")
    
    # 3. Crear/obtener temporada en BD
    temporada_id = obtener_o_crear_temporada(conn, competicion_id, 
                                              temporada_nombre, sofascore_season_id)
    if not temporada_id:
        logger.error(f"  ❌ No se pudo crear temporada en BD")
        resultado['errores'] = 1
        return resultado
    
    # 4. Obtener partidos
    logger.info(f"  Obteniendo partidos...")
    partidos = obtener_partidos_temporada(cliente, liga_id, sofascore_season_id, verbose)
    
    if not partidos:
        logger.warning(f"  ⚠️ No se encontraron partidos")
        return resultado
    
    logger.info(f"  📊 {len(partidos)} partidos encontrados")
    
    # 5. Crear mapa de equipos
    logger.info(f"  Sincronizando equipos...")
    equipos_map = {}
    equipos_procesados = set()
    
    for partido in partidos:
        for team_key in ['homeTeam', 'awayTeam']:
            team = partido.get(team_key, {})
            sf_id = team.get('id')
            if sf_id and sf_id not in equipos_procesados:
                equipo_id = obtener_o_crear_equipo(
                    conn, sf_id,
                    team.get('name', ''),
                    team.get('shortName', ''),
                    competicion_id
                )
                if equipo_id:
                    equipos_map[sf_id] = equipo_id
                equipos_procesados.add(sf_id)
    
    logger.info(f"  ✅ {len(equipos_map)} equipos")
    
    # 6. Insertar partidos
    logger.info(f"  Insertando partidos...")
    for i, partido in enumerate(partidos):
        if verbose and (i + 1) % 20 == 0:
            print(f"\r    Progreso: {i + 1}/{len(partidos)}", end='', flush=True)
        
        exito, fue_insercion = insertar_o_actualizar_partido(
            conn, partido, competicion_id, temporada_id, equipos_map
        )
        
        if exito:
            if fue_insercion:
                resultado['partidos_insertados'] += 1
            else:
                resultado['partidos_actualizados'] += 1
            
            # 7. Obtener estadísticas
            if con_estadisticas:
                estado = partido.get('status', {}).get('type', '')
                if estado == 'finished':
                    sf_id = partido.get('id')
                    stats = obtener_estadisticas_partido(cliente, sf_id)
                    if stats and actualizar_estadisticas_partido(conn, sf_id, stats):
                        resultado['con_estadisticas'] += 1
        else:
            resultado['errores'] += 1
    
    if verbose:
        print()
    
    return resultado


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Carga histórica de fútbol desde Sofascore (v3 - corregida)'
    )
    parser.add_argument('--liga', required=True, 
                       help=f"Código de liga: {', '.join(LIGAS_SOFASCORE.keys())}, o 'todas'")
    parser.add_argument('--temporadas', required=True,
                       help='Temporadas separadas por coma (ej: 2024-25,2023-24)')
    parser.add_argument('--sin-estadisticas', action='store_true',
                       help='No obtener estadísticas detalladas (más rápido)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    parser.add_argument('--dry-run', action='store_true',
                       help='Solo mostrar qué se haría')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print()
    print("=" * 70)
    print("CARGA HISTÓRICA DE FÚTBOL - SOFASCORE (v3)")
    print("=" * 70)
    print()
    
    # Parsear ligas
    if args.liga.lower() == 'todas':
        ligas = ['laliga', 'premier', 'bundesliga', 'seriea', 'ligue1']
    else:
        ligas = [l.strip().lower() for l in args.liga.split(',')]
    
    for liga in ligas:
        if liga not in LIGAS_SOFASCORE:
            print(f"❌ Liga desconocida: {liga}")
            print(f"   Opciones: {', '.join(LIGAS_SOFASCORE.keys())}")
            sys.exit(1)
    
    temporadas = [t.strip() for t in args.temporadas.split(',')]
    
    print(f"📋 Ligas: {ligas}")
    print(f"📅 Temporadas: {temporadas}")
    print(f"📊 Con estadísticas: {'No' if args.sin_estadisticas else 'Sí'}")
    print()
    
    if args.dry_run:
        print("🔵 MODO DRY-RUN - No se harán cambios")
        sys.exit(0)
    
    # Conectar
    conn = obtener_conexion()
    print("✅ Conexión a BD establecida")
    
    # Verificar y migrar esquema
    if not verificar_y_migrar_esquema(conn):
        print("❌ Error en migración de esquema")
        conn.close()
        sys.exit(1)
    
    cliente = SofascoreClientSimple()
    print()
    
    total = {
        'insertados': 0,
        'actualizados': 0,
        'con_stats': 0,
        'errores': 0
    }
    
    inicio = datetime.now()
    
    try:
        for liga in ligas:
            liga_id = LIGAS_SOFASCORE[liga]
            
            print(f"\n{'='*60}")
            print(f"📌 {liga.upper()} (Sofascore ID: {liga_id})")
            print(f"{'='*60}")
            
            competicion = verificar_competicion(conn, liga_id)
            if not competicion:
                print(f"❌ Competición no encontrada en BD (sofascore_id={liga_id})")
                print(f"   Ejecuta: python actualizar_ids_sofascore.py")
                total['errores'] += 1
                continue
            
            print(f"✅ Competición: {competicion['nombre']}")
            
            for temp_nombre in temporadas:
                print(f"\n  --- Temporada: {temp_nombre} ---")
                
                resultado = cargar_temporada(
                    conn, cliente, liga_id, temp_nombre,
                    competicion,
                    con_estadisticas=not args.sin_estadisticas,
                    verbose=args.verbose
                )
                
                total['insertados'] += resultado['partidos_insertados']
                total['actualizados'] += resultado['partidos_actualizados']
                total['con_stats'] += resultado['con_estadisticas']
                total['errores'] += resultado['errores']
                
                print(f"  ✅ {resultado['partidos_insertados']} nuevos, "
                      f"{resultado['partidos_actualizados']} actualizados, "
                      f"{resultado['con_estadisticas']} con stats")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrumpido por usuario")
    
    finally:
        cliente.cerrar()
        conn.close()
    
    duracion = (datetime.now() - inicio).total_seconds() / 60
    
    print()
    print("=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"⏱️  Duración: {duracion:.1f} minutos")
    print(f"✅ Partidos insertados: {total['insertados']}")
    print(f"🔄 Partidos actualizados: {total['actualizados']}")
    print(f"📊 Con estadísticas: {total['con_stats']}")
    print(f"❌ Errores: {total['errores']}")
    print("=" * 70)
    
    return 0 if total['errores'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())