# -*- coding: utf-8 -*-
"""rutas_equipos.py — Endpoint de equipos con tiebreakers correctos de la NBA."""

from __future__ import annotations

from typing import List, Optional, Dict

from fastapi import APIRouter, Query, HTTPException
from psycopg.rows import dict_row

from db import obtener_pool
from motor_autoentrenamiento import obtener_modelo
from motor.utilidades import resolver_nombre_en_modelo
from .excepciones import ErrorDatos
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


def validar_datos_estadisticas() -> None:
    """Valida que existan partidos válidos para estadísticas."""
    query = """
        SELECT COUNT(*)
        FROM partidos
        WHERE local_q1 IS NOT NULL
          AND local_q2 IS NOT NULL
          AND local_q3 IS NOT NULL
          AND local_q4 IS NOT NULL
          AND visitante_q1 IS NOT NULL
          AND visitante_q2 IS NOT NULL
          AND visitante_q3 IS NOT NULL
          AND visitante_q4 IS NOT NULL
          AND tipo_partido = 'REG'
          AND valido = true
          AND ganador_id IS NOT NULL
    """
    with obtener_pool().connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(query)
            conteo = cursor.fetchone()[0]

    if conteo <= 0:
        raise ErrorDatos(
            "No hay partidos en la base de datos para calcular estadísticas. "
            "Carga datos antes de consultar esta sección."
        )


def validar_partidos_disponibles() -> None:
    """Valida que existan partidos válidos antes de exponer datos."""
    query = """
        SELECT COUNT(*)
        FROM partidos
        WHERE local_q1 IS NOT NULL
          AND local_q2 IS NOT NULL
          AND local_q3 IS NOT NULL
          AND local_q4 IS NOT NULL
          AND visitante_q1 IS NOT NULL
          AND visitante_q2 IS NOT NULL
          AND visitante_q3 IS NOT NULL
          AND visitante_q4 IS NOT NULL
          AND COALESCE(tipo_partido, 'REG') != 'PRE'
    """
    with obtener_pool().connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(query)
            conteo = cursor.fetchone()[0]

    if conteo <= 0:
        raise ErrorDatos(
            "No hay partidos en la base de datos. "
            "No se pueden listar equipos ni historial hasta que haya datos."
        )


@router.get(
    "/equipos",
    summary="Listar equipos",
    response_model=RespuestaEquipos,
)
async def listar_equipos() -> RespuestaEquipos:
    """Retorna la lista de equipos disponibles."""
    validar_partidos_disponibles()
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
    validar_partidos_disponibles()
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

    OPTIMIZADO v4:
    - Elimina el patrón N+1 (una consulta por equipo) que provocaba timeouts en Neon.
    - Carga los partidos de la temporada en UNA sola consulta y calcula todo en memoria.
    - Mantiene el ordenamiento con tiebreakers (head-to-head, división, conferencia, diferencial).
    """
    from datetime import datetime
    from collections import defaultdict

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            # 1) Temporada filtro (por defecto: la más reciente por nombre)
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

            # 2) Equipos activos
            cursor.execute(
                """
                SELECT id, nombre, nombre_corto, abreviatura, conferencia, division
                FROM equipos
                WHERE activo = true
                ORDER BY nombre
                """
            )
            equipos_base = cursor.fetchall()
            if not equipos_base:
                return {
                    "fecha_actualizacion": datetime.utcnow().isoformat(),
                    "equipos": [],
                    "temporada_actual": temporada_filtro,
                }

            # Mapas de conferencia/división
            map_conferencia: Dict[str, str] = {}
            map_division: Dict[str, str] = {}
            for e in equipos_base:
                map_conferencia[str(e["id"])] = (e.get("conferencia") or "")
                map_division[str(e["id"])] = (e.get("division") or "")

            # 3) Cargar partidos (UNA consulta)
            params = []
            where_parts = [
                "p.local_q1 IS NOT NULL",
                "p.tipo_partido = 'REG'",
                "p.valido = true",
                "p.ganador_id IS NOT NULL",
            ]
            if temporada_filtro:
                where_parts.append("p.temporada_id = %s")
                params.append(temporada_filtro)

            where_sql = " AND ".join(where_parts)

            cursor.execute(
                f"""
                SELECT
                    p.equipo_local_id,
                    p.equipo_visitante_id,
                    p.local_q1, p.local_q2, p.local_q3, p.local_q4, COALESCE(p.local_ot, 0) AS local_ot, p.local_total,
                    p.visitante_q1, p.visitante_q2, p.visitante_q3, p.visitante_q4, COALESCE(p.visitante_ot, 0) AS visitante_ot, p.visitante_total,
                    p.fecha_partido,
                    p.ganador_id
                FROM partidos p
                WHERE {where_sql}
                ORDER BY p.fecha_partido DESC
                """,
                params,
            )
            partidos = cursor.fetchall()

    # Si no hay partidos válidos, no hay stats (mantenemos el comportamiento previo)
    if not partidos:
        return {
            "fecha_actualizacion": datetime.utcnow().isoformat(),
            "equipos": [],
            "temporada_actual": temporada_filtro,
        }

    # 4) Estructuras de acumulación (por equipo)
    # Stats básicos
    games = defaultdict(int)
    wins = defaultdict(int)
    losses = defaultdict(int)

    wins_home = defaultdict(int)
    losses_home = defaultdict(int)
    wins_away = defaultdict(int)
    losses_away = defaultdict(int)

    # Sumas de puntos anotados / recibidos por cuarto y total
    anot_q1 = defaultdict(float); anot_q2 = defaultdict(float); anot_q3 = defaultdict(float); anot_q4 = defaultdict(float); anot_total = defaultdict(float)
    rec_q1 = defaultdict(float);  rec_q2 = defaultdict(float);  rec_q3 = defaultdict(float);  rec_q4 = defaultdict(float);  rec_total = defaultdict(float)

    # Para ppg local/visitante
    sum_home_pts = defaultdict(float); cnt_home = defaultdict(int)
    sum_away_pts = defaultdict(float); cnt_away = defaultdict(int)

    # Para over-tendencias (listas por equipo, tamaño ~82)
    totales_q1 = defaultdict(list)
    totales_q2 = defaultdict(list)
    totales_q3 = defaultdict(list)
    totales_q4 = defaultdict(list)
    totales_partido = defaultdict(list)

    # Racha (últimos 5, en orden DESC por fecha)
    racha = defaultdict(list)

    # Diferencial acumulado
    diff_pts = defaultdict(float)

    # Conteos para tiebreakers
    head_to_head_wins: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    head_to_head_games: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    conference_wins_count: Dict[str, int] = defaultdict(int)
    conference_games_count: Dict[str, int] = defaultdict(int)
    division_wins_count: Dict[str, int] = defaultdict(int)
    division_games_count: Dict[str, int] = defaultdict(int)

    # 5) Recorrer partidos UNA vez (ya vienen por fecha DESC)
    for p in partidos:
        home = str(p["equipo_local_id"])
        away = str(p["equipo_visitante_id"])

        # Puntos por cuarto (anotados)
        hq1 = float(p.get("local_q1") or 0); hq2 = float(p.get("local_q2") or 0); hq3 = float(p.get("local_q3") or 0); hq4 = float(p.get("local_q4") or 0)
        aq1 = float(p.get("visitante_q1") or 0); aq2 = float(p.get("visitante_q2") or 0); aq3 = float(p.get("visitante_q3") or 0); aq4 = float(p.get("visitante_q4") or 0)

        htot = float(p.get("local_total") or (hq1 + hq2 + hq3 + hq4 + float(p.get("local_ot") or 0)))
        atot = float(p.get("visitante_total") or (aq1 + aq2 + aq3 + aq4 + float(p.get("visitante_ot") or 0)))

        ganador = str(p["ganador_id"]) if p.get("ganador_id") else None

        # Contar juego para ambos
        games[home] += 1
        games[away] += 1

        # Acumular anotados/recibidos
        anot_q1[home] += hq1; anot_q2[home] += hq2; anot_q3[home] += hq3; anot_q4[home] += hq4; anot_total[home] += htot
        rec_q1[home]  += aq1; rec_q2[home]  += aq2; rec_q3[home]  += aq3; rec_q4[home]  += aq4; rec_total[home]  += atot

        anot_q1[away] += aq1; anot_q2[away] += aq2; anot_q3[away] += aq3; anot_q4[away] += aq4; anot_total[away] += atot
        rec_q1[away]  += hq1; rec_q2[away]  += hq2; rec_q3[away]  += hq3; rec_q4[away]  += hq4; rec_total[away]  += htot

        # PPG local/visitante
        sum_home_pts[home] += htot; cnt_home[home] += 1
        sum_away_pts[away] += atot; cnt_away[away] += 1

        # Totales del partido para over-tendencias (se asocian a ambos equipos porque dependen de sus juegos)
        tq1 = hq1 + aq1; tq2 = hq2 + aq2; tq3 = hq3 + aq3; tq4 = hq4 + aq4; ttot = htot + atot
        totales_q1[home].append(tq1); totales_q2[home].append(tq2); totales_q3[home].append(tq3); totales_q4[home].append(tq4); totales_partido[home].append(ttot)
        totales_q1[away].append(tq1); totales_q2[away].append(tq2); totales_q3[away].append(tq3); totales_q4[away].append(tq4); totales_partido[away].append(ttot)

        # Diferencial
        diff_pts[home] += (htot - atot)
        diff_pts[away] += (atot - htot)

        # Head-to-head
        head_to_head_games[home][away] += 1
        head_to_head_games[away][home] += 1
        if ganador:
            if ganador == home:
                head_to_head_wins[home][away] += 1
            elif ganador == away:
                head_to_head_wins[away][home] += 1

        # W/L + racha (solo primeros 5 por equipo por el orden DESC global)
        if ganador == home:
            wins[home] += 1; losses[away] += 1
            wins_home[home] += 1; losses_away[away] += 1
            if len(racha[home]) < 5: racha[home].append("W")
            if len(racha[away]) < 5: racha[away].append("L")
        elif ganador == away:
            wins[away] += 1; losses[home] += 1
            wins_away[away] += 1; losses_home[home] += 1
            if len(racha[away]) < 5: racha[away].append("W")
            if len(racha[home]) < 5: racha[home].append("L")

        # Conference / Division record (solo cuenta juegos vs equipos de misma conf/div)
        conf_home = map_conferencia.get(home, "")
        conf_away = map_conferencia.get(away, "")
        if conf_home and conf_home == conf_away:
            conference_games_count[home] += 1
            conference_games_count[away] += 1
            if ganador == home:
                conference_wins_count[home] += 1
            elif ganador == away:
                conference_wins_count[away] += 1

        div_home = map_division.get(home, "")
        div_away = map_division.get(away, "")
        if div_home and div_home == div_away:
            division_games_count[home] += 1
            division_games_count[away] += 1
            if ganador == home:
                division_wins_count[home] += 1
            elif ganador == away:
                division_wins_count[away] += 1

    # 6) Construir salida por equipo (manteniendo estructura previa)
    estadisticas = []
    for e in equipos_base:
        equipo_id = str(e["id"])
        n = games[equipo_id]
        if n <= 0:
            n = 0

        # Promedios (puntos anotados y recibidos)
        puntos_anotados = {
            "q1": (anot_q1[equipo_id] / n) if n else 0,
            "q2": (anot_q2[equipo_id] / n) if n else 0,
            "q3": (anot_q3[equipo_id] / n) if n else 0,
            "q4": (anot_q4[equipo_id] / n) if n else 0,
            "total": (anot_total[equipo_id] / n) if n else 0,
        }
        puntos_recibidos = {
            "q1": (rec_q1[equipo_id] / n) if n else 0,
            "q2": (rec_q2[equipo_id] / n) if n else 0,
            "q3": (rec_q3[equipo_id] / n) if n else 0,
            "q4": (rec_q4[equipo_id] / n) if n else 0,
            "total": (rec_total[equipo_id] / n) if n else 0,
        }

        # Tendencias over (comparado contra la línea promedio de sus juegos)
        lp = sum(totales_partido[equipo_id]) / n if n else 0
        lq1 = sum(totales_q1[equipo_id]) / n if n else 0
        lq2 = sum(totales_q2[equipo_id]) / n if n else 0
        lq3 = sum(totales_q3[equipo_id]) / n if n else 0
        lq4 = sum(totales_q4[equipo_id]) / n if n else 0

        tendencias_over = {
            "q1": (sum(1 for t in totales_q1[equipo_id] if t > lq1) / n) if n else 0,
            "q2": (sum(1 for t in totales_q2[equipo_id] if t > lq2) / n) if n else 0,
            "q3": (sum(1 for t in totales_q3[equipo_id] if t > lq3) / n) if n else 0,
            "q4": (sum(1 for t in totales_q4[equipo_id] if t > lq4) / n) if n else 0,
            "total": (sum(1 for t in totales_partido[equipo_id] if t > lp) / n) if n else 0,
        }

        # Records para tiebreakers
        conf_games = conference_games_count[equipo_id]
        div_games = division_games_count[equipo_id]
        conference_record_ratio = (conference_wins_count[equipo_id] / conf_games) if conf_games > 0 else 0.0
        division_record_ratio = (division_wins_count[equipo_id] / div_games) if div_games > 0 else 0.0

        # PPG local/visitante
        n_local = cnt_home[equipo_id]
        n_visit = cnt_away[equipo_id]

        estadisticas.append({
            "nombre": e["nombre"],
            "nombre_corto": e.get("nombre_corto") or e["nombre"],
            "abreviatura": e.get("abreviatura") or "",
            "conferencia": e.get("conferencia") or "",
            "division": e.get("division") or "",
            "record": {
                "victorias": wins[equipo_id],
                "derrotas": losses[equipo_id],
            },
            "record_conferencia": {
                "victorias": conference_wins_count[equipo_id],
                "derrotas": conference_games_count[equipo_id] - conference_wins_count[equipo_id],
            },
            "racha": racha[equipo_id],
            "promedios": {
                "anotados": puntos_anotados,
                "recibidos": puntos_recibidos,
            },
            "local": {
                "victorias": wins_home[equipo_id],
                "derrotas": losses_home[equipo_id],
                "ppg": (sum_home_pts[equipo_id] / n_local) if n_local else 0,
            },
            "visitante": {
                "victorias": wins_away[equipo_id],
                "derrotas": losses_away[equipo_id],
                "ppg": (sum_away_pts[equipo_id] / n_visit) if n_visit else 0,
            },
            "tendencias_over": tendencias_over,
            "linea_promedio": lp,
            "diferencia_puntos": diff_pts[equipo_id],
            # Campos internos para tiebreakers (se limpian después)
            "equipo_id": equipo_id,
            "conference_record": conference_record_ratio,
            "division_record": division_record_ratio,
        })

    # 7) Aplicar tiebreakers (misma lógica previa)
    # Ordenar por conferencia con desempates
    for conferencia in ["Este", "Oeste"]:
        equipos_conf = [e for e in estadisticas if e["conferencia"] == conferencia]

        equipos_conf.sort(
            key=lambda e: (
                e["record"]["victorias"] / max(1, e["record"]["victorias"] + e["record"]["derrotas"]),
                e["record"]["victorias"],
            ),
            reverse=True,
        )

        posicion = 1
        i = 0
        while i < len(equipos_conf):
            j = i + 1
            while j < len(equipos_conf) and equipos_conf[j]["record"] == equipos_conf[i]["record"]:
                j += 1

            if j - i > 1:
                grupo = equipos_conf[i:j]
                mismo_division = len({g.get("division") for g in grupo}) == 1

                def _head_to_head_ratio(e):
                    eid = e.get("equipo_id")
                    total_wins = 0
                    total_games = 0
                    for other in grupo:
                        oid = other.get("equipo_id")
                        if oid == eid:
                            continue
                        total_wins += head_to_head_wins[str(eid)][str(oid)]
                        total_games += head_to_head_games[str(eid)][str(oid)]
                    return (total_wins / total_games) if total_games > 0 else 0.0

                grupo.sort(
                    key=lambda e: (
                        _head_to_head_ratio(e),
                        e.get("division_record", 0) if mismo_division else 0,
                        e.get("conference_record", 0),
                        e.get("diferencia_puntos", 0),
                    ),
                    reverse=True,
                )

                for g in grupo:
                    g["posicion"] = posicion
                    posicion += 1

                equipos_conf[i:j] = grupo
                i = j
            else:
                equipos_conf[i]["posicion"] = posicion
                posicion += 1
                i += 1

    # Limpiar campos internos
    for e in estadisticas:
        e.pop("equipo_id", None)
        e.pop("conference_record", None)
        e.pop("division_record", None)

    # Orden final: Este primero, luego Oeste; y por posición
    orden_conferencias = {"Este": 0, "Oeste": 1}
    equipos_ordenados = sorted(
        estadisticas,
        key=lambda e: (orden_conferencias.get(e.get("conferencia"), 99), e.get("posicion", 999)),
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
    validar_datos_estadisticas()
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
    validar_partidos_disponibles()
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
                "p.ganador_id IS NOT NULL",
            ]
            parametros: List[object] = [equipo_id, equipo_id, equipo_id]

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
                parametros,
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
