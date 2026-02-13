#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de sincronización continua de datos de fútbol desde Sofascore.

VERSIÓN CORREGIDA con:
- Cliente inteligente anti-bot (curl_cffi)
- Manejo correcto de rate limiting
- Corrección de errores de base de datos
- Sincronización de partidos pasados y futuros

Uso:
    # Sincronizar últimos 7 días + próximos 14 días
    python sincronizar_futbol.py --liga laliga --dias 7 --incluir-futuros
    
    # Solo últimos 3 días (sin futuros)
    python sincronizar_futbol.py --liga laliga --dias 3 --no-futuros
    
    # Todas las ligas con estadísticas completas
    python sincronizar_futbol.py --liga todas --dias 7 --incluir-futuros
    
    # Modo rápido (sin estadísticas detalladas)
    python sincronizar_futbol.py --liga premier --dias 15 --solo-resultados

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
from datetime import datetime, timedelta
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
# CLIENTE HTTP CON MANEJO INTELIGENTE ANTI-BOT
# ============================================================================

class SofascoreClientInteligente:
    """Cliente HTTP para Sofascore con bypass de protecciones anti-bot."""
    
    def __init__(self, min_intervalo: float = 2.0):
        self.min_intervalo = min_intervalo
        self.ultima_peticion = 0
        self.session = None
        self.usar_curl_cffi = False
        
        # Contadores
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
            logger.warning("⚠️ curl_cffi no instalado. Instalar con: pip install curl_cffi")
    
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
            pausa = 60 * self.bloqueos_consecutivos
            logger.warning(f"🔴 Bloqueo severo. Pausando {pausa//60} minutos...")
            time.sleep(pausa)
        elif self.bloqueos_consecutivos >= 3:
            pausa = 30
            logger.warning(f"🟡 Múltiples 403. Pausando {pausa} segundos...")
            time.sleep(pausa)
    
    def _reiniciar_contadores(self):
        """Reinicia contadores después de éxito."""
        self.bloqueos_consecutivos = 0
    
    def get(self, endpoint: str, reintentos: int = 3) -> Optional[Dict]:
        """Hace una petición GET con manejo inteligente de errores."""
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
                    if intento == 0:
                        logger.warning(f"⚠️ 403 en {endpoint}")
                    self._manejar_bloqueo()
                    time.sleep(2 ** intento)
                    
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code} en {endpoint}")
                    
            except Exception as e:
                logger.error(f"Error en {endpoint}: {e}")
                time.sleep(2)
        
        return None
    
    def verificar_acceso(self) -> bool:
        """Verifica si tenemos acceso a Sofascore."""
        logger.info("🔍 Verificando acceso a Sofascore...")
        datos = self.get('/unique-tournament/8/seasons')
        if datos:
            logger.info("✅ Acceso a Sofascore OK")
            return True
        else:
            logger.error("❌ Sin acceso a Sofascore (bloqueado)")
            return False
    
    def cerrar(self):
        """Cierra la sesión."""
        if self.session:
            self.session.close()

# ============================================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================================

def obtener_conexion():
    """Obtiene una conexión a la base de datos."""
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


def obtener_competicion_id(conn, liga_sofascore_id: int) -> Optional[int]:
    """Obtiene el ID de la competición desde la BD."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM competiciones_futbol 
            WHERE sofascore_id = %s AND activo = TRUE
        """, (liga_sofascore_id,))
        row = cur.fetchone()
        return row[0] if row else None


def obtener_temporada_activa(conn, competicion_id: int) -> Optional[Dict]:
    """Obtiene la temporada activa de una competición."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, nombre, sofascore_season_id
            FROM temporadas_futbol
            WHERE competicion_id = %s
            ORDER BY fecha_inicio DESC
            LIMIT 1
        """, (competicion_id,))
        
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'nombre': row[1],
                'sofascore_season_id': row[2]
            }
        return None


def obtener_o_crear_equipo(conn, sofascore_id: int, nombre: str, nombre_corto: str, competicion_id: int) -> Optional[str]:
    """Obtiene o crea un equipo en la BD."""
    with conn.cursor() as cur:
        # Buscar equipo existente
        cur.execute(
            "SELECT id FROM equipos_futbol WHERE sofascore_id = %s",
            (sofascore_id,)
        )
        row = cur.fetchone()
        
        if row:
            return row[0]
        
        # Crear nuevo equipo
        try:
            cur.execute("""
                INSERT INTO equipos_futbol (
                    nombre, nombre_corto, nombre_comun, 
                    sofascore_id, competicion_principal_id, activo
                )
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (
                nombre[:100], 
                (nombre_corto or nombre[:50])[:50],
                nombre.lower().strip()[:50],
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
                try:
                    cur.execute(
                        "UPDATE equipos_futbol SET sofascore_id = %s WHERE id = %s",
                        (sofascore_id, row[0])
                    )
                    conn.commit()
                    return row[0]
                except:
                    conn.rollback()
                    return row[0]
            logger.error(f"Error creando equipo {nombre}: {e}")
            return None


def insertar_o_actualizar_partido(
    conn, 
    partido_data: Dict,
    competicion_id: int,
    temporada_id: int,
    equipos_map: Dict[int, str],
    obtener_estadisticas: bool = True
) -> Tuple[bool, bool]:
    """
    Inserta o actualiza un partido en la BD.
    
    Returns:
        (exito, fue_insercion)
    """
    try:
        sofascore_id = partido_data.get('id')
        home_team = partido_data.get('homeTeam', {})
        away_team = partido_data.get('awayTeam', {})
        status = partido_data.get('status', {})
        
        home_sofascore_id = home_team.get('id')
        away_sofascore_id = away_team.get('id')
        
        if not all([sofascore_id, home_sofascore_id, away_sofascore_id]):
            return False, False
        
        equipo_local_id = equipos_map.get(home_sofascore_id)
        equipo_visitante_id = equipos_map.get(away_sofascore_id)
        
        if not equipo_local_id or not equipo_visitante_id:
            logger.warning(f"Equipos no encontrados para partido {sofascore_id}")
            return False, False
        
        timestamp = partido_data.get('startTimestamp', 0)
        fecha_partido = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
        home_score = partido_data.get('homeScore', {})
        away_score = partido_data.get('awayScore', {})
        
        local_goles_1t = home_score.get('period1')
        local_goles_2t = home_score.get('period2')
        local_goles_total = home_score.get('current') or home_score.get('normaltime')
        
        visitante_goles_1t = away_score.get('period1')
        visitante_goles_2t = away_score.get('period2')
        visitante_goles_total = away_score.get('current') or away_score.get('normaltime')
        
        estado = MAPEO_ESTADOS.get(status.get('type', 'notstarted').lower(), 'PROGRAMADO')
        jornada = partido_data.get('roundInfo', {}).get('round')
        
        ganador_id = None
        if local_goles_total is not None and visitante_goles_total is not None:
            if local_goles_total > visitante_goles_total:
                ganador_id = equipo_local_id
            elif visitante_goles_total > local_goles_total:
                ganador_id = equipo_visitante_id
        
        with conn.cursor() as cur:
            # Verificar si existe
            cur.execute(
                "SELECT id FROM partidos_futbol WHERE sofascore_match_id = %s",
                (sofascore_id,)
            )
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
                        fecha_partido, fecha_partido_local, 
                        jornada, estado,
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
                    fecha_partido, fecha_partido.date(),
                    jornada, estado,
                    local_goles_1t, local_goles_2t, local_goles_total,
                    visitante_goles_1t, visitante_goles_2t, visitante_goles_total,
                    ganador_id, sofascore_id
                ))
                conn.commit()
                return True, True
                
    except Exception as e:
        conn.rollback()
        logger.error(f"Error insertando/actualizando partido {sofascore_id}: {e}")
        return False, False


def actualizar_estadisticas_partido(conn, sofascore_id: int, stats: Dict) -> bool:
    """Actualiza las estadísticas de un partido."""
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
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error actualizando estadísticas de {sofascore_id}: {e}")
        return False

# ============================================================================
# FUNCIONES DE SCRAPING
# ============================================================================

def obtener_partidos_pasados(
    cliente: SofascoreClientInteligente,
    liga_id: int,
    temporada_id: int,
    dias: int = 7,
    max_paginas: int = 10
) -> List[Dict]:
    """Obtiene partidos de los últimos N días."""
    desde_fecha = datetime.now() - timedelta(days=dias)
    logger.info(f"Obteniendo partidos desde {desde_fecha.strftime('%Y-%m-%d')}...")
    
    partidos = []
    pagina = 0
    
    while pagina < max_paginas:
        endpoint = f"/unique-tournament/{liga_id}/season/{temporada_id}/events/last/{pagina}"
        datos = cliente.get(endpoint)
        
        if not datos or 'events' not in datos:
            break
        
        eventos = datos['events']
        if not eventos:
            break
        
        # Filtrar por fecha
        for evento in eventos:
            timestamp = evento.get('startTimestamp', 0)
            fecha_partido = datetime.fromtimestamp(timestamp)
            
            if fecha_partido >= desde_fecha:
                partidos.append(evento)
        
        pagina += 1
        
        # Si encontramos partidos muy antiguos, parar
        if eventos[-1].get('startTimestamp', 0) < desde_fecha.timestamp():
            break
    
    logger.info(f"✅ {len(partidos)} partidos pasados encontrados")
    return partidos


def obtener_partidos_futuros(
    cliente: SofascoreClientInteligente,
    liga_id: int,
    temporada_id: int,
    dias: int = 5,
    max_paginas: int = 5
) -> List[Dict]:
    """Obtiene partidos futuros."""
    hasta_fecha = datetime.now() + timedelta(days=dias)
    logger.info(f"Obteniendo partidos hasta {hasta_fecha.strftime('%Y-%m-%d')}...")
    
    partidos = []
    pagina = 0
    
    while pagina < max_paginas:
        endpoint = f"/unique-tournament/{liga_id}/season/{temporada_id}/events/next/{pagina}"
        datos = cliente.get(endpoint)
        
        if not datos or 'events' not in datos:
            break
        
        eventos = datos['events']
        if not eventos:
            break
        
        # Filtrar por fecha
        for evento in eventos:
            timestamp = evento.get('startTimestamp', 0)
            fecha_partido = datetime.fromtimestamp(timestamp)
            
            if fecha_partido <= hasta_fecha:
                partidos.append(evento)
        
        pagina += 1
        
        # Si encontramos partidos muy lejanos, parar
        if eventos[-1].get('startTimestamp', 0) > hasta_fecha.timestamp():
            break
    
    logger.info(f"✅ {len(partidos)} partidos futuros encontrados")
    return partidos


def obtener_estadisticas_partido(cliente: SofascoreClientInteligente, partido_id: int) -> Optional[Dict]:
    """Obtiene estadísticas detalladas de un partido."""
    endpoint = f"/event/{partido_id}/statistics"
    datos = cliente.get(endpoint)
    
    if not datos or 'statistics' not in datos:
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
# LÓGICA DE SINCRONIZACIÓN
# ============================================================================

def sincronizar_liga(
    conn,
    cliente: SofascoreClientInteligente,
    codigo_liga: str,
    dias_pasados: int,
    dias_futuros: int,
    incluir_futuros: bool,
    solo_resultados: bool
) -> Dict[str, Any]:
    """Sincroniza una liga completa."""
    liga_id = LIGAS_SOFASCORE[codigo_liga]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"SINCRONIZANDO: {codigo_liga.upper()} (ID: {liga_id})")
    logger.info(f"{'='*60}")
    
    resultado = {
        'procesados': 0,
        'insertados': 0,
        'actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0,
    }
    
    # Obtener competición
    competicion_id = obtener_competicion_id(conn, liga_id)
    if not competicion_id:
        logger.error(f"Competición no encontrada en BD")
        resultado['errores'] += 1
        return resultado
    
    # Obtener temporada activa
    temporada = obtener_temporada_activa(conn, competicion_id)
    if not temporada:
        logger.error(f"No hay temporada activa")
        resultado['errores'] += 1
        return resultado
    
    temporada_id = temporada['id']
    sofascore_season_id = temporada['sofascore_season_id']
    
    logger.info(f"Temporada: {temporada['nombre']} (ID: {sofascore_season_id})")
    
    # Obtener partidos pasados
    partidos_pasados = obtener_partidos_pasados(
        cliente, liga_id, sofascore_season_id, dias_pasados
    )
    
    # Obtener partidos futuros
    partidos_futuros = []
    if incluir_futuros:
        partidos_futuros = obtener_partidos_futuros(
            cliente, liga_id, sofascore_season_id, dias_futuros
        )
    
    todos_partidos = partidos_pasados + partidos_futuros
    logger.info(f"Total: {len(todos_partidos)} partidos a procesar")
    
    if not todos_partidos:
        logger.warning("No se encontraron partidos")
        return resultado
    
    # Sincronizar equipos
    logger.info("Sincronizando equipos...")
    equipos_map = {}
    for partido in todos_partidos:
        for team_key in ['homeTeam', 'awayTeam']:
            team = partido.get(team_key, {})
            sf_id = team.get('id')
            if sf_id and sf_id not in equipos_map:
                equipo_id = obtener_o_crear_equipo(
                    conn, sf_id, team.get('name', ''),
                    team.get('shortName', ''), competicion_id
                )
                if equipo_id:
                    equipos_map[sf_id] = equipo_id
    
    logger.info(f"✅ {len(equipos_map)} equipos sincronizados")
    
    # Procesar partidos
    logger.info("Procesando partidos...")
    
    for i, partido in enumerate(todos_partidos):
        if (i + 1) % 10 == 0:
            print(f"\rProgreso: {i + 1}/{len(todos_partidos)}", end='', flush=True)
        
        exito, fue_insercion = insertar_o_actualizar_partido(
            conn, partido, competicion_id, temporada_id, equipos_map
        )
        
        if exito:
            resultado['procesados'] += 1
            if fue_insercion:
                resultado['insertados'] += 1
            else:
                resultado['actualizados'] += 1
            
            # Obtener estadísticas si el partido está finalizado
            if not solo_resultados:
                estado = partido.get('status', {}).get('type', '').lower()
                if estado == 'finished':
                    sofascore_id = partido.get('id')
                    stats = obtener_estadisticas_partido(cliente, sofascore_id)
                    if stats and actualizar_estadisticas_partido(conn, sofascore_id, stats):
                        resultado['con_estadisticas'] += 1
        else:
            resultado['errores'] += 1
    
    print()  # Nueva línea después del progreso
    
    return resultado

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Sincronización de datos de fútbol desde Sofascore'
    )
    
    parser.add_argument(
        '--liga',
        required=True,
        help=f"Liga: {', '.join(LIGAS_SOFASCORE.keys())}, o 'todas'"
    )
    
    parser.add_argument(
        '--dias',
        type=int,
        default=7,
        help='Días hacia atrás a sincronizar (default: 7)'
    )
    
    parser.add_argument(
        '--dias-futuros',
        type=int,
        default=5,
        help='Días hacia adelante para partidos futuros (default: 5)'
    )
    
    parser.add_argument(
        '--incluir-futuros',
        action='store_true',
        default=False,
        help='Incluir partidos futuros'
    )
    
    parser.add_argument(
        '--no-futuros',
        action='store_true',
        help='No sincronizar partidos futuros (anula --incluir-futuros)'
    )
    
    parser.add_argument(
        '--solo-resultados',
        action='store_true',
        help='Solo actualizar resultados, no estadísticas detalladas'
    )
    
    parser.add_argument(
        '--intervalo',
        type=float,
        default=2.0,
        help='Segundos entre peticiones (default: 2.0)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Información detallada'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print()
    print("=" * 70)
    print("SINCRONIZACIÓN DE FÚTBOL - SOFASCORE")
    print("=" * 70)
    print()
    
    # Determinar ligas
    if args.liga.lower() == 'todas':
        ligas = list(LIGAS_SOFASCORE.keys())
    else:
        ligas = [l.strip().lower() for l in args.liga.split(',')]
    
    for liga in ligas:
        if liga not in LIGAS_SOFASCORE:
            print(f"❌ Liga desconocida: {liga}")
            print(f"   Opciones: {', '.join(LIGAS_SOFASCORE.keys())}")
            sys.exit(1)
    
    # Determinar si incluir futuros
    incluir_futuros = args.incluir_futuros and not args.no_futuros
    
    print(f"📋 Ligas: {', '.join(ligas)}")
    print(f"📅 Días hacia atrás: {args.dias}")
    if incluir_futuros:
        print(f"📅 Días hacia adelante: {args.dias_futuros}")
    print(f"📊 Con estadísticas: {'No' if args.solo_resultados else 'Sí'}")
    print(f"⏱️  Intervalo: {args.intervalo}s entre peticiones")
    print()
    
    # Conectar a BD
    try:
        conn = obtener_conexion()
        print("✅ Conexión a BD establecida")
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        sys.exit(1)
    
    # Crear cliente
    cliente = SofascoreClientInteligente(min_intervalo=args.intervalo)
    
    # Verificar acceso
    if not cliente.verificar_acceso():
        print()
        print("🔴 SOFASCORE ESTÁ BLOQUEANDO TUS PETICIONES")
        print()
        print("   SOLUCIONES:")
        print("   1. Instala curl_cffi: pip install curl_cffi")
        print("   2. Espera 1-2 horas e intenta de nuevo")
        print("   3. Usa una VPN para cambiar tu IP")
        print()
        cliente.cerrar()
        conn.close()
        sys.exit(1)
    
    print()
    
    # Sincronizar
    total = {
        'procesados': 0,
        'insertados': 0,
        'actualizados': 0,
        'con_estadisticas': 0,
        'errores': 0,
    }
    
    inicio = datetime.now()
    
    try:
        for codigo_liga in ligas:
            resultado = sincronizar_liga(
                conn, cliente, codigo_liga,
                args.dias, args.dias_futuros,
                incluir_futuros, args.solo_resultados
            )
            
            total['procesados'] += resultado['procesados']
            total['insertados'] += resultado['insertados']
            total['actualizados'] += resultado['actualizados']
            total['con_estadisticas'] += resultado['con_estadisticas']
            total['errores'] += resultado['errores']
            
            logger.info(
                f"Resultados: +{resultado['insertados']} nuevos, "
                f"~{resultado['actualizados']} actualizados, "
                f"📊 {resultado['con_estadisticas']} con stats"
            )
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrumpido por usuario")
    
    finally:
        cliente.cerrar()
        conn.close()
    
    # Resumen
    duracion = (datetime.now() - inicio).total_seconds()
    
    print()
    print("=" * 70)
    print("RESUMEN DE SINCRONIZACIÓN")
    print("=" * 70)
    print(f"Duración: {duracion:.1f} segundos")
    print(f"Ligas procesadas: {len(ligas)}")
    print(f"Partidos procesados: {total['procesados']}")
    print(f"Insertados: {total['insertados']}")
    print(f"Actualizados: {total['actualizados']}")
    print(f"Con estadísticas: {total['con_estadisticas']}")
    print(f"Errores: {total['errores']}")
    print()
    print(f"📡 Peticiones totales: {cliente.total_peticiones}")
    print(f"🔴 Bloqueos 403: {cliente.total_bloqueos}")
    print("=" * 70)
    
    return 0 if total['errores'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())