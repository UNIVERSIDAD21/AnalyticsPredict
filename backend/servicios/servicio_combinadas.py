# -*- coding: utf-8 -*-
"""
servicio_combinadas.py — Lógica de negocio para combinadas.
"""

from __future__ import annotations

import json
from math import ceil
from typing import List, Optional
from uuid import UUID

from psycopg.rows import dict_row

from db import obtener_pool
from esquemas.combinadas import Combinada, PeticionCrearCombinada, SeleccionCombinada
from motor.calculador_correlacion import calcular_correlacion_combinada

try:
    from psycopg.types.json import Jsonb  # type: ignore
except ImportError:
    Jsonb = None  # type: ignore


def _serializar_jsonb(valor: object | None) -> object | None:
    if valor is None:
        return None
    if Jsonb is not None:
        return Jsonb(valor)
    return json.dumps(valor)


def _calcular_confianza(selecciones: List[dict]) -> str:
    niveles = {str(sel.get("confianza_sistema") or "") for sel in selecciones}
    if "BAJA" in niveles:
        return "BAJA"
    if "MEDIA" in niveles:
        return "MEDIA"
    if "ALTA" in niveles:
        return "ALTA"
    return "MEDIA"


def _calcular_probabilidad_independiente(selecciones: List[dict]) -> float:
    prob = 1.0
    for seleccion in selecciones:
        prob *= float(seleccion.get("probabilidad_sistema") or 0.0)
    return prob


def _calcular_valor_esperado(probabilidad: float, cuota_total: float, stake: float) -> float:
    return stake * ((probabilidad * (cuota_total - 1)) - (1 - probabilidad))


def _mapear_combinada(fila: dict, selecciones: Optional[List[dict]] = None) -> Combinada:
    return Combinada(
        id=fila["id"],
        usuario_id=fila["usuario_id"],
        stake=float(fila["stake"]),
        cuota_total=float(fila["cuota_total"]),
        n_selecciones=int(fila["n_selecciones"]),
        probabilidad_independiente=float(fila["probabilidad_independiente"]),
        factor_correlacion=float(fila["factor_correlacion"]),
        probabilidad_ajustada=float(fila["probabilidad_ajustada"]),
        cuota_justa_sistema=float(fila["cuota_justa_sistema"]) if fila.get("cuota_justa_sistema") is not None else None,
        edge_combinada=float(fila["edge_combinada"]) if fila.get("edge_combinada") is not None else None,
        valor_esperado=float(fila["valor_esperado"]) if fila.get("valor_esperado") is not None else None,
        confianza_sistema=fila.get("confianza_sistema"),
        tiene_mismo_partido=bool(fila.get("tiene_mismo_partido")),
        n_partidos_unicos=int(fila.get("n_partidos_unicos") or 0),
        advertencias=fila.get("advertencias"),
        correlaciones_detectadas=fila.get("correlaciones_detectadas"),
        resultado=fila.get("resultado"),
        ganancia=float(fila.get("ganancia") or 0.0),
        selecciones_ganadas=int(fila.get("selecciones_ganadas") or 0),
        selecciones_perdidas=int(fila.get("selecciones_perdidas") or 0),
        selecciones_push=int(fila.get("selecciones_push") or 0),
        selecciones_pendientes=int(fila.get("selecciones_pendientes") or 0),
        fecha_resolucion=fila.get("fecha_resolucion").isoformat() if fila.get("fecha_resolucion") else None,
        notas=fila.get("notas"),
        etiquetas=fila.get("etiquetas"),
        creado_en=fila.get("creado_en").isoformat() if fila.get("creado_en") else None,  # ← AÑADIR .isoformat()
        actualizado_en=fila.get("actualizado_en").isoformat() if fila.get("actualizado_en") else None,  # ← AÑADIR .isoformat()
        selecciones=selecciones,
    )

def _mapear_seleccion(fila: dict) -> SeleccionCombinada:
    return SeleccionCombinada(
        id=fila["id"],
        combinada_id=fila["combinada_id"],
        partido_id=fila.get("partido_id"),
        equipo_local=fila["equipo_local"],
        equipo_visitante=fila["equipo_visitante"],
        fecha_partido=fila.get("fecha_partido"),
        mercado=fila["mercado"],
        lado=fila["lado"],
        linea=float(fila["linea"]),
        cuota=float(fila["cuota"]),
        cuota_over=float(fila["cuota_over"]) if fila.get("cuota_over") is not None else None,
        cuota_under=float(fila["cuota_under"]) if fila.get("cuota_under") is not None else None,
        probabilidad_sistema=float(fila["probabilidad_sistema"]),
        prediccion_media=float(fila["prediccion_media"]) if fila.get("prediccion_media") is not None else None,
        prediccion_desviacion=float(fila["prediccion_desviacion"]) if fila.get("prediccion_desviacion") is not None else None,
        confianza_sistema=fila.get("confianza_sistema"),
        valor_esperado_individual=float(fila["valor_esperado_individual"]) if fila.get("valor_esperado_individual") is not None else None,
        razones=fila.get("razones"),
        grupo_correlacion=fila.get("grupo_correlacion"),
        factor_ajuste_correlacion=float(fila["factor_ajuste_correlacion"]) if fila.get("factor_ajuste_correlacion") is not None else None,
        resultado=fila.get("resultado"),
        puntos_reales=float(fila["puntos_reales"]) if fila.get("puntos_reales") is not None else None,
        fecha_resolucion=fila.get("fecha_resolucion"),
        orden=int(fila.get("orden") or 0),
    )


def crear_combinada_db(peticion: PeticionCrearCombinada, usuario_id: UUID) -> Combinada:
    selecciones_dict = [seleccion.model_dump() for seleccion in peticion.selecciones]
    correlacion = calcular_correlacion_combinada(selecciones_dict)

    prob_independiente = _calcular_probabilidad_independiente(selecciones_dict)
    prob_ajustada = prob_independiente * correlacion.factor_correlacion
    cuota_justa = 1 / prob_ajustada if prob_ajustada > 0 else None
    edge = (peticion.cuota_total / cuota_justa - 1) if cuota_justa else None
    valor_esperado = _calcular_valor_esperado(prob_ajustada, peticion.cuota_total, peticion.stake)

    advertencias = correlacion.advertencias or []
    correlaciones = [detalle.__dict__ for detalle in correlacion.detalles]
    confianza = _calcular_confianza(selecciones_dict)

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            with conexion.transaction():
                cursor.execute(
                    """
                    INSERT INTO apuestas_combinadas (
                        usuario_id,
                        stake,
                        cuota_total,
                        n_selecciones,
                        probabilidad_independiente,
                        factor_correlacion,
                        probabilidad_ajustada,
                        cuota_justa_sistema,
                        edge_combinada,
                        valor_esperado,
                        confianza_sistema,
                        tiene_mismo_partido,
                        n_partidos_unicos,
                        advertencias,
                        correlaciones_detectadas,
                        resultado,
                        ganancia,
                        selecciones_ganadas,
                        selecciones_perdidas,
                        selecciones_push,
                        selecciones_pendientes,
                        notas,
                        etiquetas
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        str(usuario_id),
                        peticion.stake,
                        peticion.cuota_total,
                        len(peticion.selecciones),
                        prob_independiente,
                        correlacion.factor_correlacion,
                        prob_ajustada,
                        cuota_justa,
                        edge,
                        valor_esperado,
                        confianza,
                        correlacion.tiene_mismo_partido,
                        correlacion.n_partidos_unicos,
                        advertencias,
                        _serializar_jsonb(correlaciones),
                        "PENDIENTE",
                        0,
                        0,
                        0,
                        0,
                        len(peticion.selecciones),
                        peticion.notas,
                        _serializar_jsonb(peticion.etiquetas),
                    ),
                )
                combinada = cursor.fetchone()

                for indice, seleccion in enumerate(selecciones_dict, start=1):
                    partido_id = str(seleccion.get("partido_id") or "sin-partido")
                    grupo_correlacion = correlacion.grupos.get(partido_id)
                    factor_ajuste = correlacion.factores_grupo.get(partido_id)

                    cursor.execute(
                        """
                        INSERT INTO selecciones_combinada (
                            combinada_id,
                            apuesta_individual_id,
                            partido_id,
                            equipo_local,
                            equipo_visitante,
                            fecha_partido,
                            mercado,
                            lado,
                            linea,
                            cuota,
                            cuota_over,
                            cuota_under,
                            probabilidad_sistema,
                            prediccion_media,
                            prediccion_desviacion,
                            confianza_sistema,
                            valor_esperado_individual,
                            razones,
                            grupo_correlacion,
                            factor_ajuste_correlacion,
                            resultado,
                            orden
                        )
                        VALUES (
                            %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            combinada["id"],
                            seleccion.get("partido_id"),
                            seleccion.get("equipo_local"),
                            seleccion.get("equipo_visitante"),
                            seleccion.get("fecha_partido"),
                            seleccion.get("mercado"),
                            seleccion.get("lado"),
                            seleccion.get("linea"),
                            seleccion.get("cuota"),
                            seleccion.get("cuota_over"),
                            seleccion.get("cuota_under"),
                            seleccion.get("probabilidad_sistema"),
                            seleccion.get("prediccion_media"),
                            seleccion.get("prediccion_desviacion"),
                            seleccion.get("confianza_sistema"),
                            seleccion.get("valor_esperado_individual"),
                            _serializar_jsonb(seleccion.get("razones")),
                            grupo_correlacion,
                            factor_ajuste,
                            "PENDIENTE",
                            indice,
                        ),
                    )

                cursor.execute(
                    """
                    SELECT * FROM selecciones_combinada
                    WHERE combinada_id = %s
                    ORDER BY orden ASC
                    """,
                    (combinada["id"],),
                )
                selecciones = [_mapear_seleccion(fila) for fila in cursor.fetchall()]

    return _mapear_combinada(combinada, selecciones)


def listar_combinadas_db(
    *,
    usuario_id: UUID,
    pagina: int,
    tamano: int,
    resultado: Optional[str] = None,
) -> tuple[int, int, List[Combinada]]:
    offset = (pagina - 1) * tamano

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            condiciones = ["usuario_id = %s"]
            parametros: List[object] = [str(usuario_id)]

            if resultado:
                condiciones.append("resultado = %s")
                parametros.append(resultado)

            where_sql = " AND ".join(condiciones)

            cursor.execute(
                f"SELECT COUNT(*) as total FROM apuestas_combinadas WHERE {where_sql}",
                parametros,
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT * FROM apuestas_combinadas
                WHERE {where_sql}
                ORDER BY creado_en DESC
                LIMIT %s OFFSET %s
                """,
                parametros + [tamano, offset],
            )
            combinadas = cursor.fetchall()

            combinada_ids = [fila["id"] for fila in combinadas]
            selecciones_por_combinada: dict = {}
            if combinada_ids:
                cursor.execute(
                    """
                    SELECT * FROM selecciones_combinada
                    WHERE combinada_id = ANY(%s)
                    ORDER BY combinada_id, orden ASC
                    """,
                    (combinada_ids,),
                )
                for fila in cursor.fetchall():
                    selecciones_por_combinada.setdefault(fila["combinada_id"], []).append(
                        _mapear_seleccion(fila)
                    )

            resultado_combinadas = [
                _mapear_combinada(fila, selecciones_por_combinada.get(fila["id"], []))
                for fila in combinadas
            ]

    total_paginas = ceil(total / tamano) if tamano else 1
    return total, total_paginas, resultado_combinadas


def obtener_combinada_db(combinada_id: UUID, usuario_id: UUID) -> Combinada:
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT * FROM apuestas_combinadas
                WHERE id = %s AND usuario_id = %s
                """,
                (str(combinada_id), str(usuario_id)),
            )
            combinada = cursor.fetchone()
            if not combinada:
                raise ValueError("Combinada no encontrada")

            cursor.execute(
                """
                SELECT * FROM selecciones_combinada
                WHERE combinada_id = %s
                ORDER BY orden ASC
                """,
                (str(combinada_id),),
            )
            selecciones = [_mapear_seleccion(fila) for fila in cursor.fetchall()]

    return _mapear_combinada(combinada, selecciones)


def eliminar_combinada_db(combinada_id: UUID, usuario_id: UUID) -> None:
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT resultado FROM apuestas_combinadas
                WHERE id = %s AND usuario_id = %s
                """,
                (str(combinada_id), str(usuario_id)),
            )
            combinada = cursor.fetchone()
            if not combinada:
                raise ValueError("Combinada no encontrada")

            if combinada["resultado"] != "PENDIENTE":
                raise ValueError("Solo puedes eliminar combinadas pendientes.")

            with conexion.transaction():
                cursor.execute(
                    "DELETE FROM selecciones_combinada WHERE combinada_id = %s",
                    (str(combinada_id),),
                )
                cursor.execute(
                    "DELETE FROM apuestas_combinadas WHERE id = %s",
                    (str(combinada_id),),
                )
