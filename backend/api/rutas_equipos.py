# -*- coding: utf-8 -*-
"""rutas_equipos.py — Endpoint de equipos con tiebreakers correctos de la NBA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import APIRouter, Query, HTTPException
from psycopg.rows import dict_row

from configuracion import CONFIGURACION
from db import obtener_pool
from motor_autoentrenamiento import obtener_modelo
from motor.utilidades import resolver_nombre_en_modelo
from .modelos_respuesta import (
    RespuestaEquipos,
    RespuestaEstadisticasEquipos,
    RespuestaHistorialEquipo,
)
from motor.tipos import InfoEquipo

router = APIRouter(prefix="/api", tags=["Equipos"])


def filtrar_equipos_por_modelo(equipos: List[InfoEquipo]) -> List[InfoEquipo]:
    """Filtra equipos usando el modelo auto-entrenado desde BD."""
    try:
        modelo = obtener_modelo()
        if modelo is None:
            return equipos
        return [
            equipo
            for equipo in equipos
            if resolver_nombre_en_modelo(equipo.nombre, modelo.entidad_a_indice) is not None
        ]
    except Exception:
        return equipos


def cargar_equipos() -> List[InfoEquipo]:
    """Carga equipos desde PostgreSQL."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, nombre, nombre_corto, abreviatura, conferencia, division
                FROM equipos
                WHERE activo = true
                ORDER BY nombre
                """
            )
            filas = cursor.fetchall()
    return [InfoEquipo(**fila) for fila in filas]


def cargar_estadisticas_equipos() -> dict:
    """Carga estadísticas de equipos desde el archivo JSON de datos."""
    ruta = Path(CONFIGURACION.ruta_estadisticas_equipos)
    if not ruta.exists():
        return {
            "fecha_actualizacion": None,
            "equipos": [],
        }
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


@router.get(
    "/equipos",
    summary="Listar equipos",
    response_model=RespuestaEquipos,
)
async def listar_equipos() -> RespuestaEquipos:
    """Retorna la lista de equipos disponibles."""
    equipos = filtrar_equipos_por_modelo(cargar_equipos())
    equipos_ordenados = sorted(equipos, key=lambda e: e.nombre)
    return RespuestaEquipos(
        exito=True,
        total=len(equipos_ordenados),
        equipos=[equipo.__dict__ for equipo in equipos_ordenados],
    )


@router.get(
    "/equipos/busqueda",
    summary="Buscar equipos en catálogo",
    response_model=RespuestaEquipos,
)
async def buscar_equipos(
    conferencia: Optional[str] = Query(None, description="Filtrar por conferencia"),
    division: Optional[str] = Query(None, description="Filtrar por división"),
    busqueda: Optional[str] = Query(None, description="Texto de búsqueda"),
) -> RespuestaEquipos:
    """Busca equipos en la base de datos con filtros opcionales."""
    condiciones = ["activo = true"]
    parametros: List[object] = []
    if conferencia:
        condiciones.append("conferencia = %s")
        parametros.append(conferencia)
    if division:
        condiciones.append("division = %s")
        parametros.append(division)
    if busqueda:
        condiciones.append(
            "(nombre ILIKE %s OR nombre_corto ILIKE %s OR abreviatura ILIKE %s)"
        )
        term = f"%{busqueda}%"
        parametros.extend([term, term, term])

    where_sql = " AND ".join(condiciones)

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"""
                SELECT id, nombre, nombre_corto, abreviatura, conferencia, division
                FROM equipos
                WHERE {where_sql}
                ORDER BY nombre
                """,
                parametros,
            )
            filas = cursor.fetchall()

    equipos_filtrados = filtrar_equipos_por_modelo([InfoEquipo(**fila) for fila in filas])

    return RespuestaEquipos(
        exito=True,
        total=len(equipos_filtrados),
        equipos=[equipo.__dict__ for equipo in equipos_filtrados],
    )


def obtener_temporadas_disponibles() -> list:
    """Obtiene las temporadas disponibles con partidos."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT DISTINCT t.id, t.nombre
                FROM temporadas t
                JOIN partidos p ON p.temporada_id = t.id
                WHERE p.local_q1 IS NOT NULL
                ORDER BY t.nombre DESC
                """
            )
            return cursor.fetchall()


def calcular_estadisticas_desde_bd(temporada_id: Optional[str] = None) -> dict:
    """
    Calcula estadísticas de equipos desde la base de datos.
    CORREGIDO v4: Implementa cálculos exactos según lógica oficial de la NBA.
    """
    from datetime import datetime
    from collections import defaultdict

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            # Obtener temporada actual si no se especifica
            temporada_filtro = temporada_id
            if not temporada_filtro:
                cursor.execute(
                    """
                    SELECT id FROM temporadas
                    ORDER BY nombre DESC
                    LIMIT 1
                    """
                )
                temp = cursor.fetchone()
                temporada_filtro = str(temp["id"]) if temp else None

            # Obtener todos los equipos activos
            cursor.execute(
                """
                SELECT id, nombre, nombre_corto, abreviatura, conferencia, division
                FROM equipos
                WHERE activo = true
                ORDER BY nombre
                """
            )
            equipos_base = cursor.fetchall()

            # Estructuras para tiebreakers
            map_conferencia: Dict[str, str] = {}
            map_division: Dict[str, str] = {}
            for e in equipos_base:
                map_conferencia[str(e["id"])] = (e.get("conferencia") or "")
                map_division[str(e["id"])] = (e.get("division") or "")
            
            # Conteos para tiebreakers
            head_to_head_wins: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            head_to_head_games: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
            conference_wins_count: Dict[str, int] = defaultdict(int)
            conference_games_count: Dict[str, int] = defaultdict(int)
            division_wins_count: Dict[str, int] = defaultdict(int)
            division_games_count: Dict[str, int] = defaultdict(int)

            estadisticas = []
            for equipo in equipos_base:
                equipo_id = equipo["id"]

                # Query para obtener partidos del equipo en la temporada
                # ✅ CRÍTICO: Solo contar partidos con resultado definitivo (ganador_id presente)
                condiciones = [
                    "(p.equipo_local_id = %s OR p.equipo_visitante_id = %s)",
                    "p.local_q1 IS NOT NULL",
                    "p.tipo_partido = 'REG'",
                    "p.valido = true",
                    "p.ganador_id IS NOT NULL",  # ✅ Solo partidos con ganador confirmado
                ]
                parametros: list = [equipo_id, equipo_id]

                if temporada_filtro:
                    condiciones.append("p.temporada_id = %s")
                    parametros.append(temporada_filtro)

                where_sql = " AND ".join(condiciones)

                cursor.execute(
                    f"""
                    SELECT
                        p.equipo_local_id,
                        p.equipo_visitante_id,
                        p.local_q1, p.local_q2, p.local_q3, p.local_q4, p.local_ot, p.local_total,
                        p.visitante_q1, p.visitante_q2, p.visitante_q3, p.visitante_q4, p.visitante_ot, p.visitante_total,
                        p.fecha_partido,
                        p.ganador_id
                    FROM partidos p
                    WHERE {where_sql}
                    ORDER BY p.fecha_partido DESC
                    """,
                    parametros,
                )
                partidos = cursor.fetchall()

                if not partidos:
                    continue

                # Calcular estadísticas
                victorias = 0
                derrotas = 0
                victorias_local = 0
                derrotas_local = 0
                victorias_visitante = 0
                derrotas_visitante = 0
                puntos_local = []
                puntos_visitante = []
                anotados_q1, anotados_q2, anotados_q3, anotados_q4, anotados_total = [], [], [], [], []
                recibidos_q1, recibidos_q2, recibidos_q3, recibidos_q4, recibidos_total = [], [], [], [], []
                totales_q1, totales_q2, totales_q3, totales_q4, totales_partido = [], [], [], [], []
                racha = []
                diferencia_puntos_total = 0

                for partido in partidos:
                    es_local = str(partido["equipo_local_id"]) == str(equipo_id)
                    
                    # Obtener puntos del equipo y rival
                    if es_local:
                        pts_equipo = partido["local_total"]
                        pts_rival = partido["visitante_total"]
                        q1_e, q2_e, q3_e, q4_e = partido["local_q1"], partido["local_q2"], partido["local_q3"], partido["local_q4"]
                        q1_r, q2_r, q3_r, q4_r = partido["visitante_q1"], partido["visitante_q2"], partido["visitante_q3"], partido["visitante_q4"]
                    else:
                        pts_equipo = partido["visitante_total"]
                        pts_rival = partido["local_total"]
                        q1_e, q2_e, q3_e, q4_e = partido["visitante_q1"], partido["visitante_q2"], partido["visitante_q3"], partido["visitante_q4"]
                        q1_r, q2_r, q3_r, q4_r = partido["local_q1"], partido["local_q2"], partido["local_q3"], partido["local_q4"]

                    # ✅ Validación de datos
                    if pts_equipo is None or pts_rival is None:
                        continue

                    # ID del rival
                    opponent_id = str(partido["equipo_visitante_id"]) if es_local else str(partido["equipo_local_id"])
                    
                    # ✅ CORRECCIÓN CRÍTICA: Usar ganador_id directamente (ya validamos que existe)
                    ganador_id_str = str(partido["ganador_id"])
                    gano = (ganador_id_str == str(equipo_id))
                    
                    # Actualizar récord general
                    if gano:
                        victorias += 1
                        if es_local:
                            victorias_local += 1
                        else:
                            victorias_visitante += 1
                        if len(racha) < 5:
                            racha.append("W")
                    else:
                        derrotas += 1
                        if es_local:
                            derrotas_local += 1
                        else:
                            derrotas_visitante += 1
                        if len(racha) < 5:
                            racha.append("L")
                    
                    # ✅ Conference record (solo contra equipos de la misma conferencia)
                    if map_conferencia.get(str(equipo_id)) and map_conferencia.get(str(equipo_id)) == map_conferencia.get(opponent_id):
                        conference_games_count[str(equipo_id)] += 1
                        if gano:
                            conference_wins_count[str(equipo_id)] += 1
                    
                    # Division record (solo contra equipos de la misma división)
                    if map_division.get(str(equipo_id)) and map_division.get(str(equipo_id)) == map_division.get(opponent_id):
                        division_games_count[str(equipo_id)] += 1
                        if gano:
                            division_wins_count[str(equipo_id)] += 1
                    
                    # Head-to-head para tiebreakers
                    head_to_head_games[str(equipo_id)][opponent_id] += 1
                    if gano:
                        head_to_head_wins[str(equipo_id)][opponent_id] += 1
                    
                    # Puntos para estadísticas
                    if es_local:
                        puntos_local.append(pts_equipo)
                    else:
                        puntos_visitante.append(pts_equipo)
                    
                    # Estadísticas por cuarto
                    anotados_q1.append(q1_e)
                    anotados_q2.append(q2_e)
                    anotados_q3.append(q3_e)
                    anotados_q4.append(q4_e)
                    anotados_total.append(pts_equipo)

                    recibidos_q1.append(q1_r)
                    recibidos_q2.append(q2_r)
                    recibidos_q3.append(q3_r)
                    recibidos_q4.append(q4_r)
                    recibidos_total.append(pts_rival)

                    totales_q1.append(q1_e + q1_r)
                    totales_q2.append(q2_e + q2_r)
                    totales_q3.append(q3_e + q3_r)
                    totales_q4.append(q4_e + q4_r)
                    totales_partido.append(pts_equipo + pts_rival)

                    diferencia_puntos_total += (pts_equipo - pts_rival)

                # Calcular promedios
                n = len(partidos)
                linea_promedio = sum(totales_partido) / n if n else 0
                linea_q1 = sum(totales_q1) / n if n else 0
                linea_q2 = sum(totales_q2) / n if n else 0
                linea_q3 = sum(totales_q3) / n if n else 0
                linea_q4 = sum(totales_q4) / n if n else 0

                tendencias_over = {
                    "q1": sum(1 for t in totales_q1 if t > linea_q1) / n if n else 0,
                    "q2": sum(1 for t in totales_q2 if t > linea_q2) / n if n else 0,
                    "q3": sum(1 for t in totales_q3 if t > linea_q3) / n if n else 0,
                    "q4": sum(1 for t in totales_q4 if t > linea_q4) / n if n else 0,
                    "total": sum(1 for t in totales_partido if t > linea_promedio) / n if n else 0,
                }

                n_local = len(puntos_local) or 1
                n_visitante = len(puntos_visitante) or 1

                # Calcular ratios para tiebreakers
                total_partidos = victorias + derrotas
                
                # ✅ Récord de conferencia (solo partidos contra equipos de la misma conferencia)
                conf_games = conference_games_count.get(str(equipo_id), 0)
                conf_wins = conference_wins_count.get(str(equipo_id), 0)
                conf_losses = conf_games - conf_wins
                conference_record_ratio = (conf_wins / conf_games) if conf_games > 0 else 0.0
                
                # Récord de división
                div_games = division_games_count.get(str(equipo_id), 0)
                div_wins = division_wins_count.get(str(equipo_id), 0)
                division_record_ratio = (div_wins / div_games) if div_games > 0 else 0.0

                # ✅ Porcentaje de victorias (PCT) según la NBA
                pct = victorias / total_partidos if total_partidos > 0 else 0.0

                estadisticas.append({
                    "nombre": equipo["nombre"],
                    "abreviatura": equipo["abreviatura"],
                    "conferencia": equipo["conferencia"] or "",
                    "division": equipo["division"] or "",
                    "record": {"victorias": victorias, "derrotas": derrotas},
                    "record_conferencia": {"victorias": conf_wins, "derrotas": conf_losses},
                    "pct": pct,  # ✅ PCT calculado correctamente
                    "posicion": 0,
                    "racha": list(reversed(racha)),
                    "promedios": {
                        "anotados": {
                            "q1": sum(anotados_q1) / n if n else 0,
                            "q2": sum(anotados_q2) / n if n else 0,
                            "q3": sum(anotados_q3) / n if n else 0,
                            "q4": sum(anotados_q4) / n if n else 0,
                            "total": sum(anotados_total) / n if n else 0,
                        },
                        "recibidos": {
                            "q1": sum(recibidos_q1) / n if n else 0,
                            "q2": sum(recibidos_q2) / n if n else 0,
                            "q3": sum(recibidos_q3) / n if n else 0,
                            "q4": sum(recibidos_q4) / n if n else 0,
                            "total": sum(recibidos_total) / n if n else 0,
                        },
                    },
                    "local": {
                        "victorias": victorias_local,
                        "derrotas": derrotas_local,
                        "ppg": sum(puntos_local) / n_local if puntos_local else 0,
                    },
                    "visitante": {
                        "victorias": victorias_visitante,
                        "derrotas": derrotas_visitante,
                        "ppg": sum(puntos_visitante) / n_visitante if puntos_visitante else 0,
                    },
                    "tendencias_over": tendencias_over,
                    "linea_promedio": linea_promedio,
                    "diferencia_puntos": diferencia_puntos_total,
                    "equipo_id": str(equipo_id),
                    "conference_record": conference_record_ratio,
                    "division_record": division_record_ratio,
                })

            # ✅ CORRECCIÓN: Aplicar tiebreakers oficiales de la NBA
            for conferencia in ["Este", "Oeste"]:
                equipos_conf = [e for e in estadisticas if e["conferencia"] == conferencia]
                
                # Orden inicial por PCT (porcentaje de victorias)
                equipos_conf.sort(
                    key=lambda e: (
                        e["pct"],  # ✅ Usar PCT pre-calculado
                        e["record"]["victorias"],  # Desempate por número de victorias
                    ),
                    reverse=True,
                )
                
                # Aplicar tiebreakers para equipos con mismo récord
                posicion = 1
                i = 0
                while i < len(equipos_conf):
                    j = i
                    vict = equipos_conf[i]["record"]["victorias"]
                    der = equipos_conf[i]["record"]["derrotas"]
                    
                    # Identificar equipos con mismo récord
                    while j < len(equipos_conf) and \
                          equipos_conf[j]["record"]["victorias"] == vict and \
                          equipos_conf[j]["record"]["derrotas"] == der:
                        j += 1
                    
                    grupo = equipos_conf[i:j]
                    
                    if len(grupo) > 1:
                        # Tiebreaker para 2+ equipos
                        grupo_ids = [g["equipo_id"] for g in grupo]
                        
                        misma_division = len({g.get("division") for g in grupo}) == 1

                        def _head_to_head_ratio(team_dict):
                            """Calcula el porcentaje de victorias head-to-head."""
                            tid = team_dict["equipo_id"]
                            total_games = 0
                            total_wins = 0
                            for oid in grupo_ids:
                                if oid == tid:
                                    continue
                                total_games += head_to_head_games.get(str(tid), {}).get(str(oid), 0)
                                total_wins += head_to_head_wins.get(str(tid), {}).get(str(oid), 0)
                            return (total_wins / total_games) if total_games > 0 else 0.0
                        
                        # Ordenar grupo aplicando todos los criterios de tiebreak
                        grupo.sort(
                            key=lambda e: (
                                _head_to_head_ratio(e),           # 1. Head-to-head
                                e.get("division_record", 0) if misma_division else 0,  # 2. Division record
                                e.get("conference_record", 0),    # 3. Conference record
                                e.get("diferencia_puntos", 0),    # 4. Point differential
                            ),
                            reverse=True,
                        )
                    
                    # Asignar posiciones
                    for g in grupo:
                        g["posicion"] = posicion
                        posicion += 1
                    
                    equipos_conf[i:j] = grupo
                    i = j

            # Limpiar campos internos
            for e in estadisticas:
                e.pop("equipo_id", None)
                e.pop("conference_record", None)
                e.pop("division_record", None)

            orden_conferencias = {"Este": 0, "Oeste": 1}
            equipos_ordenados = sorted(
                estadisticas,
                key=lambda e: (
                    orden_conferencias.get(e["conferencia"], 2),
                    e["posicion"],
                    e["nombre"],
                ),
            )

            return {
                "fecha_actualizacion": datetime.utcnow().isoformat(),
                "equipos": equipos_ordenados,
                "temporada_actual": temporada_filtro,
            }


@router.get(
    "/estadisticas-equipos",
    summary="Estadísticas de equipos",
    response_model=RespuestaEstadisticasEquipos,
)
async def listar_estadisticas_equipos(
    temporada_id: Optional[str] = Query(None, description="Filtrar por temporada específica"),
) -> RespuestaEstadisticasEquipos:
    """Retorna estadísticas agregadas de los equipos calculadas desde la BD."""
    temporadas = obtener_temporadas_disponibles()
    datos = calcular_estadisticas_desde_bd(temporada_id)

    return RespuestaEstadisticasEquipos(
        exito=True,
        fecha_actualizacion=datos["fecha_actualizacion"],
        equipos=datos["equipos"],
        temporadas_disponibles=[
            {"id": str(t["id"]), "nombre": t["nombre"]} for t in temporadas
        ],
        temporada_actual=datos.get("temporada_actual"),
    )


@router.get(
    "/equipos/{equipo_id}/partidos",
    summary="Historial de partidos por equipo",
    response_model=RespuestaHistorialEquipo,
)
async def listar_historial_equipo(
    equipo_id: str,
    temporada_id: Optional[str] = Query(None, description="Filtrar por temporada"),
    como_local: Optional[bool] = Query(
        None, description="True para local, False para visitante"
    ),
    orden: str = Query("desc", description="Orden por fecha: asc o desc"),
) -> RespuestaHistorialEquipo:
    """Retorna el historial completo de partidos de un equipo."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, nombre, abreviatura
                FROM equipos
                WHERE id = %s
                """,
                (equipo_id,),
            )
            equipo = cursor.fetchone()

            if not equipo:
                raise HTTPException(status_code=404, detail="Equipo no encontrado")

            condiciones = [
                "(p.equipo_local_id = %s OR p.equipo_visitante_id = %s)",
                "p.local_q1 IS NOT NULL",
                "p.valido = true",
                "p.ganador_id IS NOT NULL",  # ✅ Solo partidos con ganador confirmado
            ]
            parametros: List[object] = [equipo_id, equipo_id]

            if temporada_id:
                condiciones.append("p.temporada_id = %s")
                parametros.append(temporada_id)
            if como_local is True:
                condiciones.append("p.equipo_local_id = %s")
                parametros.append(equipo_id)
            if como_local is False:
                condiciones.append("p.equipo_visitante_id = %s")
                parametros.append(equipo_id)

            where_sql = " AND ".join(condiciones)
            orden_sql = "ASC" if orden.lower() == "asc" else "DESC"

            cursor.execute(
                f"""
                SELECT
                    p.id,
                    p.fecha_partido,
                    t.nombre as temporada,
                    el.nombre as equipo_local,
                    el.abreviatura as local_abr,
                    ev.nombre as equipo_visitante,
                    ev.abreviatura as visitante_abr,
                    p.local_q1, p.local_q2, p.local_q3, p.local_q4, p.local_ot,
                    p.local_total,
                    p.visitante_q1, p.visitante_q2, p.visitante_q3, p.visitante_q4, p.visitante_ot,
                    p.visitante_total,
                    p.ganador_id,
                    CASE
                        WHEN p.equipo_local_id = %s THEN 'LOCAL'
                        ELSE 'VISITANTE'
                    END as ubicacion_equipo
                FROM partidos p
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                LEFT JOIN temporadas t ON p.temporada_id = t.id
                WHERE {where_sql}
                ORDER BY p.fecha_partido {orden_sql}
                """,
                [equipo_id] + parametros,
            )
            filas = cursor.fetchall()

            cursor.execute(
                """
                SELECT DISTINCT t.id, t.nombre
                FROM temporadas t
                JOIN partidos p ON p.temporada_id = t.id
                WHERE (p.equipo_local_id = %s OR p.equipo_visitante_id = %s)
                ORDER BY t.nombre DESC
                """,
                (equipo_id, equipo_id),
            )
            temporadas = cursor.fetchall()

    partidos = []
    for fila in filas:
        ubicacion = fila["ubicacion_equipo"]
        puntos_equipo = {
            "q1": fila["local_q1"] if ubicacion == "LOCAL" else fila["visitante_q1"],
            "q2": fila["local_q2"] if ubicacion == "LOCAL" else fila["visitante_q2"],
            "q3": fila["local_q3"] if ubicacion == "LOCAL" else fila["visitante_q3"],
            "q4": fila["local_q4"] if ubicacion == "LOCAL" else fila["visitante_q4"],
            "ot": fila["local_ot"] if ubicacion == "LOCAL" else fila["visitante_ot"],
            "total": fila["local_total"] if ubicacion == "LOCAL" else fila["visitante_total"],
        }
        puntos_rival = {
            "q1": fila["visitante_q1"] if ubicacion == "LOCAL" else fila["local_q1"],
            "q2": fila["visitante_q2"] if ubicacion == "LOCAL" else fila["local_q2"],
            "q3": fila["visitante_q3"] if ubicacion == "LOCAL" else fila["local_q3"],
            "q4": fila["visitante_q4"] if ubicacion == "LOCAL" else fila["local_q4"],
            "ot": fila["visitante_ot"] if ubicacion == "LOCAL" else fila["local_ot"],
            "total": fila["visitante_total"] if ubicacion == "LOCAL" else fila["local_total"],
        }

        def ajustar_ot(puntos: dict) -> int:
            base = (puntos["q1"] or 0) + (puntos["q2"] or 0) + (puntos["q3"] or 0) + (puntos["q4"] or 0)
            total = puntos["total"] or 0
            ot = puntos["ot"] or 0
            if ot > 0:
                return ot
            diff = total - base
            return diff if diff > 0 else 0

        puntos_equipo["ot"] = ajustar_ot(puntos_equipo)
        puntos_rival["ot"] = ajustar_ot(puntos_rival)
        
        # ✅ CORRECCIÓN: Usar ganador_id en lugar de comparar totales
        ganador_id_str = str(fila["ganador_id"]) if fila["ganador_id"] else None
        equipo_actual_id = str(equipo_id)
        resultado = "VICTORIA" if ganador_id_str == equipo_actual_id else "DERROTA"
        
        fecha = fila["fecha_partido"]
        partidos.append(
            {
                "id": str(fila["id"]),
                "fecha": fecha.isoformat() if fecha else "",
                "temporada": fila.get("temporada"),
                "equipo_local": fila["equipo_local"],
                "local_abr": fila["local_abr"],
                "equipo_visitante": fila["equipo_visitante"],
                "visitante_abr": fila["visitante_abr"],
                "ubicacion_equipo": ubicacion,
                "puntos_equipo": puntos_equipo,
                "puntos_rival": puntos_rival,
                "resultado": resultado,
            }
        )

    return RespuestaHistorialEquipo(
        exito=True,
        equipo={
            "id": str(equipo["id"]),
            "nombre": equipo["nombre"],
            "abreviatura": equipo["abreviatura"],
            "logo_url": equipo.get("logo_url"),
        },
        total_partidos=len(partidos),
        partidos=partidos,
        filtros_disponibles={
            "temporadas": [
                {"id": str(temporada["id"]), "nombre": temporada["nombre"]}
                for temporada in temporadas
            ]
        },
    )