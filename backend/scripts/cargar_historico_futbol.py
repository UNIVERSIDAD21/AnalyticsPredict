#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de carga histórica de datos de fútbol desde Sofascore.

VERSIÓN 4 - CON MANEJO INTELIGENTE DE RATE LIMITING:
- Detecta bloqueos 403 y hace pausas automáticas
- Intervalo configurable entre peticiones
- Guarda progreso para poder continuar
- Modo sin estadísticas para carga rápida inicial

Uso:
    # Carga normal (2 seg entre peticiones)
    python cargar_historico_futbol.py --liga laliga --temporadas 2024-25

    # Carga rápida sin estadísticas
    python cargar_historico_futbol.py --liga laliga --temporadas 2024-25 --sin-estadisticas

    # Carga lenta (si hay bloqueos)
    python cargar_historico_futbol.py --liga laliga --temporadas 2024-25 --intervalo 3

Requisitos:
    pip install psycopg[binary] python-dotenv curl_cffi
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import json
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
    'laliga': 8,  #ya
    'premier': 17, #ya
    'bundesliga': 35, #ya
    'seriea': 23, #ya
    'ligue1': 34,
    'champions': 7,
    'europa': 679,
    'conference': 17015,
    'copa_rey': 329, #ya
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
# CLIENTE HTTP CON MANEJO INTELIGENTE DE RATE LIMITING
# ============================================================================

class SofascoreClientInteligente:
    """Cliente HTTP para Sofascore con detección de bloqueos y pausas automáticas."""
    
    def __init__(self, min_intervalo: float = 2.0):
        self.min_intervalo = min_intervalo
        self.ultima_peticion = 0
        self.session = None
        self.usar_curl_cffi = False
        
        # Contadores de bloqueos
        self.bloqueos_consecutivos = 0
        self.total_bloqueos = 0
        self.total_peticiones = 0
        
        # Inicializar sesión
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
            logger.warning("⚠️ curl_cffi no instalado. Riesgo alto de bloqueos.")
    
    def _rate_limit(self):
        """Aplica rate limiting."""
        ahora = time.time()
        transcurrido = ahora - self.ultima_peticion
        if transcurrido < self.min_intervalo:
            time.sleep(self.min_intervalo - transcurrido)
        self.ultima_peticion = time.time()
    
    def _manejar_bloqueo(self):
        """Maneja un bloqueo 403 con pausas progresivas."""
        self.bloqueos_consecutivos += 1
        self.total_bloqueos += 1
        
        if self.bloqueos_consecutivos >= 5:
            # Bloqueo severo - pausa larga
            pausa = 60 * self.bloqueos_consecutivos  # 5 min, 6 min, 7 min...
            logger.warning(f"🔴 Bloqueo severo detectado. Pausando {pausa//60} minutos...")
            logger.warning(f"   (Puedes cancelar con Ctrl+C y continuar más tarde)")
            time.sleep(pausa)
        elif self.bloqueos_consecutivos >= 3:
            # Bloqueo moderado
            pausa = 30
            logger.warning(f"🟡 Múltiples 403. Pausando {pausa} segundos...")
            time.sleep(pausa)
    
    def _reiniciar_contadores(self):
        """Reinicia contadores después de éxito."""
        self.bloqueos_consecutivos = 0
    
    def get(self, endpoint: str, reintentos: int = 3, critico: bool = False) -> Optional[Dict]:
        """
        Hace una petición GET con manejo inteligente de errores.
        
        Args:
            endpoint: Endpoint de la API
            reintentos: Número de reintentos
            critico: Si True, hace pausa larga en caso de 403
        """
        url = f"{SOFASCORE_API_BASE}{endpoint}"
        self.total_peticiones += 1
        
        for intento in range(reintentos):
            self._rate_limit()
            
            try:
                if self.usar_curl_cffi:
                    response = self.session.get(url)
                else:
                    response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    self._reiniciar_contadores()
                    return response.json()
                    
                elif response.status_code == 403:
                    if intento == 0:  # Solo logear en primer intento
                        logger.warning(f"  ⚠️ 403 en {endpoint}")
                    
                    self._manejar_bloqueo()
                    
                    # Backoff exponencial
                    time.sleep(2 ** intento)
                    
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"  HTTP {response.status_code} en {endpoint}")
                    
            except Exception as e:
                logger.error(f"  Error en {endpoint}: {e}")
                time.sleep(2)
        
        # Si es endpoint crítico y falló, hacer pausa más larga
        if critico and self.bloqueos_consecutivos >= 3:
            logger.error(f"🔴 Endpoint crítico bloqueado. El servidor está bloqueando peticiones.")
            logger.error(f"   Espera 1-2 horas antes de continuar.")
            return None
        
        return None
    
    def verificar_acceso(self) -> bool:
        """Verifica si tenemos acceso a Sofascore."""
        logger.info("🔍 Verificando acceso a Sofascore...")
        datos = self.get('/unique-tournament/8/seasons', critico=True)
        if datos:
            logger.info("✅ Acceso a Sofascore OK")
            return True
        else:
            logger.error("❌ Sin acceso a Sofascore (bloqueado)")
            return False
    
    def estadisticas(self) -> Dict:
        """Retorna estadísticas del cliente."""
        return {
            'total_peticiones': self.total_peticiones,
            'total_bloqueos': self.total_bloqueos,
            'tasa_bloqueo': f"{(self.total_bloqueos/max(1,self.total_peticiones))*100:.1f}%"
        }
    
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
    """Verifica y agrega columnas faltantes."""
    
    logger.info("🔍 Verificando esquema de BD...")
    
    migraciones = []
    
    with conn.cursor() as cur:
        # Verificar columnas necesarias
        columnas = [
            ('temporadas_futbol', 'sofascore_season_id', 'INTEGER'),
            ('equipos_futbol', 'nombre_comun', 'VARCHAR(50)'),
            ('partidos_futbol', 'sofascore_match_id', 'INTEGER'),
            ('partidos_futbol', 'fuente_datos', "VARCHAR(50) DEFAULT 'SOFASCORE'"),
        ]
        
        for tabla, columna, tipo in columnas:
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, (tabla, columna))
            if not cur.fetchone():
                migraciones.append((tabla, columna, tipo))
    
    if migraciones:
        logger.info(f"📝 Aplicando {len(migraciones)} migraciones...")
        for tabla, columna, tipo in migraciones:
            try:
                with conn.cursor() as cur:
                    cur.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
                conn.commit()
                logger.info(f"   ✅ {tabla}.{columna}")
            except Exception as e:
                conn.rollback()
                logger.warning(f"   ⚠️ {tabla}.{columna}: {e}")
    else:
        logger.info("   ✅ Esquema OK")
    
    return True


# ============================================================================
# FUNCIONES DE BD (igual que v3)
# ============================================================================

def verificar_competicion(conn, sofascore_id: int) -> Optional[Dict]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, codigo, nombre, sofascore_id 
            FROM competiciones_futbol 
            WHERE sofascore_id = %s AND activo = TRUE
        """, (sofascore_id,))
        row = cur.fetchone()
        if row:
            return {'id': row[0], 'codigo': row[1], 'nombre': row[2], 'sofascore_id': row[3]}
    return None


def obtener_o_crear_temporada(conn, competicion_id, nombre: str, sofascore_season_id: int) -> Optional[str]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM temporadas_futbol
            WHERE competicion_id = %s AND nombre = %s
        """, (competicion_id, nombre))
        row = cur.fetchone()
        
        if row:
            cur.execute("UPDATE temporadas_futbol SET sofascore_season_id = %s WHERE id = %s", 
                       (sofascore_season_id, row[0]))
            conn.commit()
            return row[0]
        
        cur.execute("""
            SELECT id FROM temporadas_futbol
            WHERE competicion_id = %s AND sofascore_season_id = %s
        """, (competicion_id, sofascore_season_id))
        row = cur.fetchone()
        if row:
            return row[0]
        
        try:
            partes = nombre.replace('/', '-').split('-')
            anio_inicio = int(partes[0]) if len(partes[0]) == 4 else int(f"20{partes[0]}")
            anio_fin = int(partes[1]) if len(partes) > 1 and len(partes[1]) == 4 else int(f"20{partes[1]}") if len(partes) > 1 else anio_inicio + 1
            
            cur.execute("""
                INSERT INTO temporadas_futbol (
                    competicion_id, nombre, anio_inicio, anio_fin,
                    fecha_inicio, fecha_fin, sofascore_season_id, activa
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (competicion_id, nombre, anio_inicio, anio_fin,
                  f"{anio_inicio}-08-01", f"{anio_fin}-06-30", sofascore_season_id))
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"    ✅ Temporada creada: {nombre}")
            return nuevo_id
        except Exception as e:
            conn.rollback()
            logger.error(f"    ❌ Error creando temporada: {e}")
            return None


def obtener_o_crear_equipo(conn, sofascore_id: int, nombre: str, nombre_corto: str, competicion_id) -> Optional[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM equipos_futbol WHERE sofascore_id = %s", (sofascore_id,))
        row = cur.fetchone()
        if row:
            return row[0]
        
        try:
            cur.execute("""
                INSERT INTO equipos_futbol (nombre, nombre_corto, nombre_comun, sofascore_id, competicion_principal_id, activo)
                VALUES (%s, %s, %s, %s, %s, TRUE) RETURNING id
            """, (nombre[:100], (nombre_corto or nombre[:50])[:50], nombre.lower().strip()[:50], sofascore_id, competicion_id))
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            return nuevo_id
        except:
            conn.rollback()
            cur.execute("SELECT id FROM equipos_futbol WHERE nombre = %s OR nombre_corto = %s LIMIT 1", (nombre, nombre_corto))
            row = cur.fetchone()
            if row:
                try:
                    cur.execute("UPDATE equipos_futbol SET sofascore_id = %s WHERE id = %s", (sofascore_id, row[0]))
                    conn.commit()
                except:
                    conn.rollback()
                return row[0]
            return None


def insertar_o_actualizar_partido(conn, datos: Dict, competicion_id, temporada_id, equipos_map: Dict) -> Tuple[bool, bool]:
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
        
        estado = MAPEO_ESTADOS.get(datos.get('status', {}).get('type', 'notstarted').lower(), 'PROGRAMADO')
        jornada = datos.get('roundInfo', {}).get('round')
        
        ganador_id = None
        if local_goles_total is not None and visitante_goles_total is not None:
            if local_goles_total > visitante_goles_total:
                ganador_id = equipo_local_id
            elif visitante_goles_total > local_goles_total:
                ganador_id = equipo_visitante_id
        
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM partidos_futbol WHERE sofascore_match_id = %s", (sofascore_id,))
            existente = cur.fetchone()
            
            if existente:
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
                """, (local_goles_1t, local_goles_2t, local_goles_total,
                      visitante_goles_1t, visitante_goles_2t, visitante_goles_total,
                      estado, ganador_id, sofascore_id))
                conn.commit()
                return True, False
            else:
                cur.execute("""
                    INSERT INTO partidos_futbol (
                        competicion_id, temporada_id, equipo_local_id, equipo_visitante_id,
                        fecha_partido, fecha_partido_local, jornada, estado,
                        local_goles_1t, local_goles_2t, local_goles_total,
                        visitante_goles_1t, visitante_goles_2t, visitante_goles_total,
                        ganador_id, sofascore_match_id, fuente_datos
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::estado_partido_futbol,
                              %s, %s, %s, %s, %s, %s, %s, %s, 'SOFASCORE')
                """, (competicion_id, temporada_id, equipo_local_id, equipo_visitante_id,
                      fecha_partido, fecha_partido.date(), jornada, estado,
                      local_goles_1t, local_goles_2t, local_goles_total,
                      visitante_goles_1t, visitante_goles_2t, visitante_goles_total,
                      ganador_id, sofascore_id))
                conn.commit()
                return True, True
    except Exception as e:
        conn.rollback()
        return False, False


def actualizar_estadisticas_partido(conn, sofascore_id: int, stats: Dict) -> bool:
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
                    actualizado_en = NOW()
                WHERE sofascore_match_id = %s
            """, (stats.get('corners_local_1t'), stats.get('corners_local_2t'), stats.get('corners_local_total'),
                  stats.get('corners_visitante_1t'), stats.get('corners_visitante_2t'), stats.get('corners_visitante_total'),
                  stats.get('disparos_local_total'), stats.get('disparos_local_arco'),
                  stats.get('disparos_visitante_total'), stats.get('disparos_visitante_arco'),
                  stats.get('posesion_local'), stats.get('posesion_visitante'),
                  stats.get('xg_local'), stats.get('xg_visitante'), sofascore_id))
            conn.commit()
            return cur.rowcount > 0
    except:
        conn.rollback()
        return False


# ============================================================================
# FUNCIONES DE SOFASCORE
# ============================================================================

def obtener_temporadas_sofascore(cliente, liga_id: int) -> List[Dict]:
    datos = cliente.get(f'/unique-tournament/{liga_id}/seasons', critico=True)
    return datos.get('seasons', []) if datos else []


def buscar_temporada_sofascore(temporadas: List[Dict], nombre_buscado: str) -> Optional[Dict]:
    nombre_buscado = nombre_buscado.lower().replace(' ', '').replace('-', '')
    
    for temp in temporadas:
        nombre = temp.get('name', '').lower().replace(' ', '').replace('-', '').replace('/', '')
        year = str(temp.get('year', ''))
        
        if nombre_buscado in nombre or nombre in nombre_buscado:
            return temp
        if nombre_buscado[-4:] in nombre or nombre_buscado[-2:] in nombre[-2:]:
            return temp
        if year and nombre_buscado.endswith(year[-2:]):
            return temp
    
    return None


def obtener_partidos_temporada(cliente, liga_id: int, season_id: int, verbose: bool = False) -> List[Dict]:
    todos = []
    page = 0
    
    while page < 50:
        datos = cliente.get(f'/unique-tournament/{liga_id}/season/{season_id}/events/last/{page}')
        
        if not datos:
            break
        
        events = datos.get('events', [])
        if not events:
            break
        
        todos.extend(events)
        page += 1
        
        if verbose:
            print(f"\r    Obteniendo: página {page}, total {len(todos)}...", end='', flush=True)
    
    if verbose:
        print()
    
    return todos


def obtener_estadisticas_partido(cliente, evento_id: int) -> Optional[Dict]:
    datos = cliente.get(f'/event/{evento_id}/statistics')
    if not datos:
        return None
    
    statistics = datos.get('statistics', [])
    if not statistics:
        return None
    
    resultado = {}
    
    for periodo in statistics:
        period_name = periodo.get('period', 'ALL')
        for group in periodo.get('groups', []):
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
                        resultado['posesion_local'] = float(str(home).replace('%', '')) if home else None
                        resultado['posesion_visitante'] = float(str(away).replace('%', '')) if away else None
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
# CARGA DE TEMPORADA
# ============================================================================

def cargar_temporada(conn, cliente, liga_id: int, temporada_nombre: str,
                     competicion: Dict, con_estadisticas: bool = True,
                     verbose: bool = False) -> Dict[str, int]:
    
    resultado = {'partidos_insertados': 0, 'partidos_actualizados': 0, 'con_estadisticas': 0, 'errores': 0}
    
    competicion_id = competicion['id']
    
    logger.info(f"  Obteniendo temporadas de Sofascore...")
    temporadas = obtener_temporadas_sofascore(cliente, liga_id)
    
    if not temporadas:
        logger.error(f"  ❌ No se pudieron obtener temporadas (posible bloqueo)")
        resultado['errores'] = 1
        return resultado
    
    temporada_sf = buscar_temporada_sofascore(temporadas, temporada_nombre)
    
    if not temporada_sf:
        logger.warning(f"  ⚠️ Temporada '{temporada_nombre}' no encontrada")
        logger.info(f"  Disponibles: {[t.get('name') for t in temporadas[:5]]}")
        resultado['errores'] = 1
        return resultado
    
    sofascore_season_id = temporada_sf.get('id')
    season_name = temporada_sf.get('name', temporada_nombre)
    logger.info(f"  ✅ Temporada: {season_name} (ID: {sofascore_season_id})")
    
    temporada_id = obtener_o_crear_temporada(conn, competicion_id, temporada_nombre, sofascore_season_id)
    if not temporada_id:
        resultado['errores'] = 1
        return resultado
    
    logger.info(f"  Obteniendo partidos...")
    partidos = obtener_partidos_temporada(cliente, liga_id, sofascore_season_id, verbose)
    
    if not partidos:
        logger.warning(f"  ⚠️ No se encontraron partidos")
        return resultado
    
    logger.info(f"  📊 {len(partidos)} partidos encontrados")
    
    # Sincronizar equipos
    logger.info(f"  Sincronizando equipos...")
    equipos_map = {}
    for partido in partidos:
        for team_key in ['homeTeam', 'awayTeam']:
            team = partido.get(team_key, {})
            sf_id = team.get('id')
            if sf_id and sf_id not in equipos_map:
                equipo_id = obtener_o_crear_equipo(conn, sf_id, team.get('name', ''), team.get('shortName', ''), competicion_id)
                if equipo_id:
                    equipos_map[sf_id] = equipo_id
    
    logger.info(f"  ✅ {len(equipos_map)} equipos")
    
    # Insertar partidos
    logger.info(f"  Insertando partidos...")
    stats_fallidos = 0
    
    for i, partido in enumerate(partidos):
        if verbose and (i + 1) % 20 == 0:
            print(f"\r    Progreso: {i + 1}/{len(partidos)} ({stats_fallidos} stats fallidos)", end='', flush=True)
        
        exito, fue_insercion = insertar_o_actualizar_partido(conn, partido, competicion_id, temporada_id, equipos_map)
        
        if exito:
            if fue_insercion:
                resultado['partidos_insertados'] += 1
            else:
                resultado['partidos_actualizados'] += 1
            
            if con_estadisticas and partido.get('status', {}).get('type') == 'finished':
                sf_id = partido.get('id')
                stats = obtener_estadisticas_partido(cliente, sf_id)
                if stats and actualizar_estadisticas_partido(conn, sf_id, stats):
                    resultado['con_estadisticas'] += 1
                else:
                    stats_fallidos += 1
                    
                    # Si hay muchos stats fallidos, dejar de intentar
                    if stats_fallidos >= 10 and cliente.bloqueos_consecutivos >= 3:
                        logger.warning(f"\n  ⚠️ Demasiados bloqueos en estadísticas. Continuando sin stats...")
                        con_estadisticas = False
        else:
            resultado['errores'] += 1
    
    if verbose:
        print()
    
    return resultado


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Carga histórica de fútbol desde Sofascore (v4 - rate limiting inteligente)')
    parser.add_argument('--liga', required=True, help=f"Liga: {', '.join(LIGAS_SOFASCORE.keys())}, o 'todas'")
    parser.add_argument('--temporadas', required=True, help='Temporadas (ej: 2024-25,2023-24)')
    parser.add_argument('--sin-estadisticas', action='store_true', help='No obtener estadísticas (más rápido, evita bloqueos)')
    parser.add_argument('--intervalo', type=float, default=2.0, help='Segundos entre peticiones (default: 2)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Información detallada')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué se haría')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print()
    print("=" * 70)
    print("CARGA HISTÓRICA DE FÚTBOL - SOFASCORE (v4)")
    print("=" * 70)
    print()
    
    if args.liga.lower() == 'todas':
        ligas = ['laliga', 'premier', 'bundesliga', 'seriea', 'ligue1']
    else:
        ligas = [l.strip().lower() for l in args.liga.split(',')]
    
    for liga in ligas:
        if liga not in LIGAS_SOFASCORE:
            print(f"❌ Liga desconocida: {liga}")
            sys.exit(1)
    
    temporadas = [t.strip() for t in args.temporadas.split(',')]
    
    print(f"📋 Ligas: {ligas}")
    print(f"📅 Temporadas: {temporadas}")
    print(f"📊 Con estadísticas: {'No' if args.sin_estadisticas else 'Sí'}")
    print(f"⏱️  Intervalo: {args.intervalo}s entre peticiones")
    print()
    
    if args.dry_run:
        print("🔵 MODO DRY-RUN")
        sys.exit(0)
    
    conn = obtener_conexion()
    print("✅ Conexión a BD establecida")
    
    verificar_y_migrar_esquema(conn)
    
    cliente = SofascoreClientInteligente(min_intervalo=args.intervalo)
    
    # Verificar acceso antes de empezar
    if not cliente.verificar_acceso():
        print()
        print("🔴 SOFASCORE ESTÁ BLOQUEANDO TUS PETICIONES")
        print("   Esto puede deberse a:")
        print("   1. Demasiadas peticiones recientes (rate limiting)")
        print("   2. Tu IP está temporalmente bloqueada")
        print()
        print("   SOLUCIÓN: Espera 1-2 horas e intenta de nuevo")
        print("   O usa una VPN para cambiar tu IP")
        print()
        cliente.cerrar()
        conn.close()
        sys.exit(1)
    
    print()
    
    total = {'insertados': 0, 'actualizados': 0, 'con_stats': 0, 'errores': 0}
    inicio = datetime.now()
    
    try:
        for liga in ligas:
            liga_id = LIGAS_SOFASCORE[liga]
            
            print(f"\n{'='*60}")
            print(f"📌 {liga.upper()} (Sofascore ID: {liga_id})")
            print(f"{'='*60}")
            
            competicion = verificar_competicion(conn, liga_id)
            if not competicion:
                print(f"❌ Competición no encontrada")
                total['errores'] += 1
                continue
            
            print(f"✅ Competición: {competicion['nombre']}")
            
            for temp_nombre in temporadas:
                print(f"\n  --- Temporada: {temp_nombre} ---")
                
                resultado = cargar_temporada(
                    conn, cliente, liga_id, temp_nombre, competicion,
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
        print("\n\n⚠️ Interrumpido")
    
    finally:
        stats_cliente = cliente.estadisticas()
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
    print(f"📡 Peticiones totales: {stats_cliente['total_peticiones']}")
    print(f"🔴 Bloqueos 403: {stats_cliente['total_bloqueos']} ({stats_cliente['tasa_bloqueo']})")
    print("=" * 70)
    
    return 0 if total['errores'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())