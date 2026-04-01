# -*- coding: utf-8 -*-
"""rutas_bitacora.py — Endpoints para la bitácora de apuestas."""

from __future__ import annotations

from datetime import date, datetime
import json
import logging
import os
import time
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator
from psycopg.rows import dict_row

from db import obtener_pool
from motor.resolucion_apuestas import (
    resolver_apuestas,
    obtener_estadisticas_apuestas,
    obtener_apuestas_pendientes_por_mercado,
)
from servicios.apuestas_analizadas import resolver_apuestas_analizadas

# Importar Jsonb para serializar correctamente campos JSON en la base de datos.
try:
    # psycopg 3.x
    from psycopg.types.json import Jsonb  # type: ignore
except ImportError:
    # Fallback para versiones antiguas; si no está disponible, definiremos un wrapper
    Jsonb = None  # type: ignore
from .dependencias import obtener_usuario_id
from .modelos_peticion import PeticionActualizarResultado, PeticionCrearApuesta
from .modelos_respuesta import RespuestaApuesta, RespuestaListaApuestas, RespuestaResumenApuestas


class RegistroBitacoraUnificada(BaseModel):
    """Registro unificado de bitácora (singles + combinadas)."""

    id: UUID
    deporte: Optional[str] = None
    tipo_apuesta: str
    resultado: str
    stake: float
    ganancia: float
    cuota: Optional[float] = None
    cuota_total: Optional[float] = None
    n_selecciones: Optional[int] = None
    selecciones_ganadas: Optional[int] = None
    selecciones_perdidas: Optional[int] = None
    selecciones_push: Optional[int] = None
    selecciones_pendientes: Optional[int] = None
    tiene_mismo_partido: Optional[bool] = None
    advertencias: Optional[List[str]] = None
    equipo_local: Optional[str] = None
    equipo_visitante: Optional[str] = None
    fecha_partido: Optional[date] = None
    mercado: Optional[str] = None
    lado: Optional[str] = None
    linea: Optional[float] = None
    probabilidad_sistema: Optional[float] = None
    confianza_sistema: Optional[str] = None
    valor_esperado: Optional[float] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    selecciones: Optional[List[dict]] = None

    @field_validator("creado_en", "actualizado_en", mode="before")
    @classmethod
    def convertir_datetime(cls, valor: object | None) -> Optional[str]:
        """Convierte datetime/date a string ISO."""
        if valor is None:
            return None
        if isinstance(valor, datetime):
            return valor.isoformat()
        if isinstance(valor, date):
            return valor.isoformat()
        return valor


class RespuestaBitacoraUnificada(BaseModel):
    """Respuesta para la bitácora unificada."""

    exito: bool
    total: int
    pagina: int
    total_paginas: int
    registros: List[RegistroBitacoraUnificada]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bitacora", tags=["Bitácora"])

BITACORA_SUNSET_DATE = os.getenv("BITACORA_LEGACY_SUNSET", "2026-12-31")
BITACORA_AUTO_RESOLVE_INTERVAL_SEC = int(os.getenv("BITACORA_AUTO_RESOLVE_INTERVAL_SEC", "300"))
BITACORA_AUTO_RESOLVE_LIMIT = int(os.getenv("BITACORA_AUTO_RESOLVE_LIMIT", "800"))
_AUTO_RESOLVE_LAST_RUN_BY_USER: dict[str, float] = {}
_AUTO_RESOLVE_LAST_RUN_ANALIZADAS: float = 0.0

BITACORA_USAGE_PATH = Path(
    os.getenv(
        "BITACORA_CONTRACT_USAGE_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "bitacora_contract_usage.json")),
    )
)


def _registrar_uso_contrato(version: str) -> None:
    """Telemetría simple de uso de contrato bitácora (v2 vs legacy)."""
    try:
        BITACORA_USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        today = date.today().isoformat()
        if BITACORA_USAGE_PATH.exists():
            data = json.loads(BITACORA_USAGE_PATH.read_text(encoding="utf-8"))
        else:
            data = {"by_date": {}}

        by_date = data.setdefault("by_date", {})
        row = by_date.setdefault(today, {"legacy": 0, "v2": 0})
        row["legacy" if version == "legacy" else "v2"] += 1

        BITACORA_USAGE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        return


def _leer_uso_contrato() -> dict:
    if not BITACORA_USAGE_PATH.exists():
        return {"by_date": {}}
    try:
        data = json.loads(BITACORA_USAGE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("by_date", {}), dict):
            return data
    except Exception:
        pass
    return {"by_date": {}}


def _aplicar_headers_deprecacion(response: Response, endpoint: str) -> None:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = BITACORA_SUNSET_DATE
    suffix = f"/{endpoint}" if endpoint else ""
    response.headers["Link"] = f'</api/bitacora{suffix}?version=v2>; rel="successor-version"'


def _respuesta_contrato(payload_legacy: dict, version: str, response: Response, endpoint: str) -> dict:
    _registrar_uso_contrato(version)

    if version == "legacy":
        _aplicar_headers_deprecacion(response, endpoint)
        return payload_legacy

    data = dict(payload_legacy)
    data.pop("exito", None)
    return {
        "ok": True,
        "data": data,
        "meta": {
            "contract_version": "v2",
            "legacy_supported": True,
        },
    }


def _auto_resolver_bitacoras(usuario_id: UUID) -> None:
    """Actualiza automáticamente apuestas/analizados ya finalizados con throttling.

    Evita recalcular en cada request de lectura para no degradar UX (timeouts en bitácora).
    """
    global _AUTO_RESOLVE_LAST_RUN_ANALIZADAS

    ahora = time.time()
    usuario_key = str(usuario_id)
    ultimo_usuario = _AUTO_RESOLVE_LAST_RUN_BY_USER.get(usuario_key, 0.0)
    if (ahora - ultimo_usuario) >= BITACORA_AUTO_RESOLVE_INTERVAL_SEC:
        try:
            resolver_apuestas(usuario_id=usuario_key, limite=BITACORA_AUTO_RESOLVE_LIMIT)
            _AUTO_RESOLVE_LAST_RUN_BY_USER[usuario_key] = ahora
        except Exception:
            logger.exception("Auto-resolución de apuestas falló para usuario=%s", usuario_id)

    if (ahora - _AUTO_RESOLVE_LAST_RUN_ANALIZADAS) >= BITACORA_AUTO_RESOLVE_INTERVAL_SEC:
        try:
            resolver_apuestas_analizadas()
            _AUTO_RESOLVE_LAST_RUN_ANALIZADAS = ahora
        except Exception:
            logger.exception("Auto-resolución de análisis falló")


def _serializar_jsonb(valor: object | None) -> object | None:
    if valor is None:
        return None
    if Jsonb is not None:
        return Jsonb(valor)
    return json.dumps(valor)


def _construir_payload_apuesta(peticion: PeticionCrearApuesta, usuario_id: UUID) -> dict:
    cuota_over = peticion.cuota_over
    cuota_under = peticion.cuota_under
    if cuota_over is None and cuota_under is None and peticion.cuota is not None:
        if peticion.lado == "UNDER":
            cuota_under = peticion.cuota
        else:
            cuota_over = peticion.cuota

    devig_metodo = peticion.devig_metodo
    devig_overround = peticion.devig_overround
    if devig_metodo == "exacto" and (cuota_over is None or cuota_under is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="devig_metodo=exacto requiere cuota_over y cuota_under.",
        )

    if peticion.score_total is not None and peticion.score_componentes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="score_total requiere score_componentes para trazabilidad.",
        )

    if peticion.kelly_fraccional is not None:
        if peticion.fraccion_kelly is None or peticion.stake_porcentaje is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="kelly_fraccional requiere fraccion_kelly y stake_porcentaje.",
            )

    return {
        "usuario_id": str(usuario_id),
        "partido_id": peticion.partido_id,
        "equipo_local": peticion.equipo_local,
        "equipo_visitante": peticion.equipo_visitante,
        "fecha_partido": peticion.fecha_partido,
        "mercado": peticion.mercado,
        "lado": peticion.lado,
        "linea": peticion.linea,
        "cuota": peticion.cuota,
        "cuota_over": cuota_over,
        "cuota_under": cuota_under,
        "stake": peticion.stake,
        "probabilidad_sistema": peticion.probabilidad_sistema,
        "confianza_sistema": peticion.confianza_sistema,
        "valor_esperado": peticion.valor_esperado,
        "devig_metodo": devig_metodo,
        "modo_devig": peticion.modo_devig,
        "devig_overround": devig_overround,
        "devig_p_mkt_raw": peticion.devig_p_mkt_raw,
        "devig_p_mkt_fair": peticion.devig_p_mkt_fair,
        "devig_advertencias": peticion.devig_advertencias,
        "edge_real": peticion.edge_real,
        "score_total": peticion.score_total,
        "score_componentes": _serializar_jsonb(peticion.score_componentes),
        "score_explicacion": peticion.score_explicacion,
        "score_penalizaciones": peticion.score_penalizaciones,
        "kelly_full": peticion.kelly_full,
        "kelly_fraccional": peticion.kelly_fraccional,
        "fraccion_kelly": peticion.fraccion_kelly,
        "stake_porcentaje": peticion.stake_porcentaje,
        "bankroll_momento": peticion.bankroll_momento,
        "perfil_riesgo_usado": peticion.perfil_riesgo_usado,
        "sizing_advertencias": peticion.sizing_advertencias,
        "sizing_penalizaciones": _serializar_jsonb(peticion.sizing_penalizaciones),
        "prediccion_media": peticion.prediccion_media,
        "prediccion_desviacion": peticion.prediccion_desviacion,
        "razones": _serializar_jsonb(peticion.razones),
    }


def _construir_where(
    usuario_id: UUID,
    resultado: Optional[str],
    mercado: Optional[str],
    confianza: Optional[str],
    desde: Optional[date],
    hasta: Optional[date],
    busqueda: Optional[str],
) -> tuple[str, List[object]]:
    _ = usuario_id
    # Bitácora compartida: lectura global sin filtro por usuario.
    condiciones: List[str] = []
    parametros: List[object] = []

    if resultado:
        condiciones.append("resultado = %s")
        parametros.append(resultado)
    if mercado:
        condiciones.append("mercado = %s")
        parametros.append(mercado)
    if confianza:
        condiciones.append("confianza_sistema = %s")
        parametros.append(confianza)
    if desde:
        condiciones.append("fecha_partido >= %s")
        parametros.append(desde)
    if hasta:
        condiciones.append("fecha_partido <= %s")
        parametros.append(hasta)
    if busqueda:
        condiciones.append("(equipo_local ILIKE %s OR equipo_visitante ILIKE %s)")
        termino = f"%{busqueda}%"
        parametros.extend([termino, termino])

    where_sql = " AND ".join(condiciones) if condiciones else "TRUE"
    return where_sql, parametros


@router.post("", summary="Guardar apuesta", response_model=RespuestaApuesta)
async def guardar_apuesta(
    peticion: PeticionCrearApuesta,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaApuesta:
    """Crea una apuesta con snapshot del análisis."""
    datos_apuesta = _construir_payload_apuesta(peticion, usuario_id)

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                INSERT INTO apuestas (
                    usuario_id,
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
                    stake,
                    probabilidad_sistema,
                    confianza_sistema,
                    valor_esperado,
                    devig_metodo,
                    modo_devig,
                    devig_overround,
                    devig_p_mkt_raw,
                    devig_p_mkt_fair,
                    devig_advertencias,
                    edge_real,
                    score_total,
                    score_componentes,
                    score_explicacion,
                    score_penalizaciones,
                    kelly_full,
                    kelly_fraccional,
                    fraccion_kelly,
                    stake_porcentaje,
                    bankroll_momento,
                    perfil_riesgo_usado,
                    sizing_advertencias,
                    sizing_penalizaciones,
                    prediccion_media,
                    prediccion_desviacion,
                    razones
                ) VALUES (
                    %(usuario_id)s,
                    %(partido_id)s,
                    %(equipo_local)s,
                    %(equipo_visitante)s,
                    %(fecha_partido)s,
                    %(mercado)s,
                    %(lado)s,
                    %(linea)s,
                    %(cuota)s,
                    %(cuota_over)s,
                    %(cuota_under)s,
                    %(stake)s,
                    %(probabilidad_sistema)s,
                    %(confianza_sistema)s,
                    %(valor_esperado)s,
                    %(devig_metodo)s,
                    %(modo_devig)s,
                    %(devig_overround)s,
                    %(devig_p_mkt_raw)s,
                    %(devig_p_mkt_fair)s,
                    %(devig_advertencias)s,
                    %(edge_real)s,
                    %(score_total)s,
                    %(score_componentes)s,
                    %(score_explicacion)s,
                    %(score_penalizaciones)s,
                    %(kelly_full)s,
                    %(kelly_fraccional)s,
                    %(fraccion_kelly)s,
                    %(stake_porcentaje)s,
                    %(bankroll_momento)s,
                    %(perfil_riesgo_usado)s,
                    %(sizing_advertencias)s,
                    %(sizing_penalizaciones)s,
                    %(prediccion_media)s,
                    %(prediccion_desviacion)s,
                    %(razones)s
                )
                RETURNING *
                """,
                datos_apuesta,
            )
            apuesta = cursor.fetchone()
    return RespuestaApuesta(exito=True, apuesta=apuesta)


@router.get("", summary="Listar apuestas")
async def listar_apuestas(
    response: Response,
    version: str = Query(default="legacy", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
    resultado: Optional[str] = Query(None),
    mercado: Optional[str] = Query(None),
    confianza: Optional[str] = Query(None),
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    busqueda: Optional[str] = Query(None),
    orden: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    tamano: int = Query(10, ge=1, le=50),
) -> RespuestaListaApuestas:
    """Lista apuestas con filtros y paginación."""
    _auto_resolver_bitacoras(usuario_id)

    where_sql, parametros = _construir_where(
        usuario_id=usuario_id,
        resultado=resultado,
        mercado=mercado,
        confianza=confianza,
        desde=desde,
        hasta=hasta,
        busqueda=busqueda,
    )

    if orden == "reciente":
        orden_sql = "fecha_partido DESC NULLS LAST, creado_en DESC"
    elif orden == "antiguo":
        orden_sql = "fecha_partido ASC NULLS LAST, creado_en ASC"
    elif orden == "ganancia":
        orden_sql = "ganancia DESC, creado_en DESC"
    else:
        # Sin orden específico: ordena por fecha de partido más reciente.
        orden_sql = "fecha_partido DESC NULLS LAST, creado_en DESC"

    offset = (pagina - 1) * tamano

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM apuestas WHERE {where_sql}",
                parametros,
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT *
                FROM apuestas
                WHERE {where_sql}
                ORDER BY {orden_sql}
                LIMIT %s OFFSET %s
                """,
                [*parametros, tamano, offset],
            )
            apuestas = cursor.fetchall()

    total_paginas = max(1, (total + tamano - 1) // tamano) if total else 0

    payload_legacy = RespuestaListaApuestas(
        exito=True,
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        apuestas=apuestas,
    ).model_dump(mode="json")
    return _respuesta_contrato(payload_legacy, version, response, "")


@router.get("/resumen", summary="Resumen de apuestas")
async def resumen_apuestas(
    response: Response,
    version: str = Query(default="legacy", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
):
    """Retorna el resumen agregado de apuestas para el usuario (incluye simples y combinadas)."""
    _auto_resolver_bitacoras(usuario_id)

    try:
        with obtener_pool().connection() as conexion:
            with conexion.cursor(row_factory=dict_row) as cursor:
                # Consulta unificada que combina apuestas NBA/base, fútbol y combinadas.
                cursor.execute(
                    """
                    WITH apuestas_unificadas AS (
                        SELECT usuario_id, 'baloncesto'::text AS deporte, mercado, stake, ganancia, resultado
                        FROM apuestas
                        UNION ALL
                        SELECT usuario_id, 'futbol'::text AS deporte, mercado::text AS mercado, stake, ganancia, resultado::text AS resultado
                        FROM apuestas_futbol
                        UNION ALL
                        SELECT usuario_id, 'baloncesto'::text AS deporte, NULL::text AS mercado, stake, ganancia, resultado
                        FROM apuestas_combinadas
                    ),
                    resumen_global AS (
                        SELECT
                            NULL::uuid AS usuario_id,
                            COUNT(*) AS total_apuestas,
                            COUNT(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
                            COUNT(*) FILTER (WHERE resultado <> 'PENDIENTE') AS cerradas,
                            COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                            COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                            COUNT(*) FILTER (WHERE resultado = 'PUSH') AS push,
                            COUNT(*) FILTER (WHERE resultado = 'ANULADA') AS anuladas,
                            COALESCE(SUM(stake), 0) AS stake_total,
                            COALESCE(SUM(ganancia), 0) AS ganancia_total,
                            CASE
                                WHEN COUNT(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')) > 0
                                THEN ROUND(
                                    100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA') /
                                    COUNT(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')),
                                    2
                                )
                                ELSE 0
                            END AS winrate,
                            CASE
                                WHEN COALESCE(SUM(stake) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 0) > 0
                                THEN ROUND(
                                    100.0 * COALESCE(SUM(ganancia) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 0) /
                                    COALESCE(SUM(stake) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 1),
                                    2
                                )
                                ELSE 0
                            END AS roi
                        FROM apuestas_unificadas
                    ),
                    por_deporte AS (
                        SELECT
                            deporte,
                            COUNT(*) AS total,
                            COUNT(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
                            COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                            COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                            COALESCE(SUM(stake), 0) AS stake_total,
                            COALESCE(SUM(ganancia), 0) AS ganancia_total,
                            CASE
                                WHEN COUNT(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')) > 0
                                THEN ROUND(
                                    100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA') /
                                    COUNT(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')),
                                    2
                                )
                                ELSE 0
                            END AS winrate,
                            CASE
                                WHEN COALESCE(SUM(stake) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 0) > 0
                                THEN ROUND(
                                    100.0 * COALESCE(SUM(ganancia) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 0) /
                                    COALESCE(SUM(stake) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 1),
                                    2
                                )
                                ELSE 0
                            END AS roi
                        FROM apuestas_unificadas
                        GROUP BY deporte
                    ),
                    por_mercado AS (
                        SELECT
                            mercado,
                            COUNT(*) AS total,
                            COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                            COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                            COALESCE(SUM(stake), 0) AS stake_total,
                            COALESCE(SUM(ganancia), 0) AS ganancia_total,
                            CASE
                                WHEN COUNT(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')) > 0
                                THEN ROUND(
                                    100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA') /
                                    COUNT(*) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA')),
                                    2
                                )
                                ELSE 0
                            END AS winrate,
                            CASE
                                WHEN COALESCE(SUM(stake) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 0) > 0
                                THEN ROUND(
                                    100.0 * COALESCE(SUM(ganancia) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 0) /
                                    COALESCE(SUM(stake) FILTER (WHERE resultado IN ('GANADA', 'PERDIDA', 'PUSH')), 1),
                                    2
                                )
                                ELSE 0
                            END AS roi
                        FROM apuestas_unificadas
                        WHERE mercado IS NOT NULL
                        GROUP BY mercado
                    )
                    SELECT
                        (SELECT row_to_json(rg) FROM resumen_global rg) AS resumen_global,
                        (SELECT COALESCE(json_agg(pd ORDER BY pd.deporte), '[]'::json) FROM por_deporte pd) AS por_deporte,
                        (SELECT COALESCE(json_agg(pm ORDER BY pm.total DESC), '[]'::json) FROM por_mercado pm) AS por_mercado
                    """,
                    [],
                )
                fila_resumen = cursor.fetchone() or {}
                resumen = fila_resumen.get("resumen_global") or {}
                resumen["por_deporte"] = fila_resumen.get("por_deporte") or []
                resumen["por_mercado"] = fila_resumen.get("por_mercado") or []
    except Exception:
        logger.exception("Fallo resumen de bitácora; devolviendo resumen en cero de contingencia")
        resumen = {
            "usuario_id": None,
            "total_apuestas": 0,
            "pendientes": 0,
            "cerradas": 0,
            "ganadas": 0,
            "perdidas": 0,
            "push": 0,
            "anuladas": 0,
            "stake_total": 0,
            "ganancia_total": 0,
            "winrate": 0,
            "roi": 0,
            "por_deporte": [],
            "por_mercado": [],
        }

    payload_legacy = RespuestaResumenApuestas(exito=True, resumen=resumen).model_dump(mode="json")
    return _respuesta_contrato(payload_legacy, version, response, "resumen")


@router.get("/contract-usage", summary="Métricas de adopción contrato bitácora")
async def contract_usage(days: int = Query(default=7, ge=1, le=90)):
    data = _leer_uso_contrato().get("by_date", {})
    fechas = sorted(data.keys(), reverse=True)[:days]

    rows = []
    total_v2 = 0
    total_legacy = 0

    for fecha in fechas:
        row = data.get(fecha, {})
        v2 = int(row.get("v2", 0) or 0)
        legacy = int(row.get("legacy", 0) or 0)
        total = v2 + legacy
        legacy_ratio = (legacy / total) if total > 0 else 0.0

        total_v2 += v2
        total_legacy += legacy
        rows.append(
            {
                "date": fecha,
                "v2": v2,
                "legacy": legacy,
                "total": total,
                "legacy_ratio": round(legacy_ratio, 4),
            }
        )

    total_calls = total_v2 + total_legacy
    ratio_global = (total_legacy / total_calls) if total_calls > 0 else 0.0

    return {
        "ok": True,
        "data": {
            "days": days,
            "rows": rows,
            "summary": {
                "v2": total_v2,
                "legacy": total_legacy,
                "total": total_calls,
                "legacy_ratio": round(ratio_global, 4),
            },
        },
        "meta": {
            "contract_version": "v2",
            "sunset": BITACORA_SUNSET_DATE,
        },
    }


@router.get("/unificada", summary="Bitácora unificada")
async def listar_bitacora_unificada(
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
    resultado: Optional[str] = Query(None),
    deporte: Optional[str] = Query(None),
    tipo_apuesta: Optional[str] = Query(None),
    mercado: Optional[str] = Query(None),
    confianza: Optional[str] = Query(None),
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    busqueda: Optional[str] = Query(None),
    orden: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=50),
):
    """Lista la bitácora unificada de apuestas simples y combinadas."""
    _auto_resolver_bitacoras(usuario_id)

    condiciones: List[str] = []
    parametros: List[object] = []

    if resultado:
        condiciones.append("resultado = %s")
        parametros.append(resultado)
    if deporte:
        condiciones.append("deporte = %s")
        parametros.append(deporte.lower())
    if tipo_apuesta:
        condiciones.append("tipo_apuesta = %s")
        parametros.append(tipo_apuesta.upper())
    if mercado:
        condiciones.append("mercado = %s")
        parametros.append(mercado)
    if confianza:
        condiciones.append("confianza_sistema = %s")
        parametros.append(confianza)
    if desde:
        condiciones.append("COALESCE(fecha_partido, creado_en::date) >= %s")
        parametros.append(desde)
    if hasta:
        condiciones.append("COALESCE(fecha_partido, creado_en::date) <= %s")
        parametros.append(hasta)
    if busqueda:
        condiciones.append("(COALESCE(equipo_local,'') ILIKE %s OR COALESCE(equipo_visitante,'') ILIKE %s)")
        termino = f"%{busqueda}%"
        parametros.extend([termino, termino])

    where_sql = " AND ".join(condiciones) if condiciones else "TRUE"

    if orden == "antiguo":
        orden_sql = "COALESCE(fecha_partido, creado_en::date) ASC, creado_en ASC"
    else:
        orden_sql = "COALESCE(fecha_partido, creado_en::date) DESC, creado_en DESC"

    offset = (pagina - 1) * tamano

    bitacora_cte = """
        WITH bitacora_global AS (
            SELECT
                a.id,
                'baloncesto'::text AS deporte,
                'SIMPLE'::text AS tipo_apuesta,
                a.resultado,
                a.stake,
                a.ganancia,
                a.cuota,
                NULL::numeric AS cuota_total,
                NULL::int AS n_selecciones,
                NULL::int AS selecciones_ganadas,
                NULL::int AS selecciones_perdidas,
                NULL::int AS selecciones_push,
                NULL::int AS selecciones_pendientes,
                NULL::boolean AS tiene_mismo_partido,
                NULL::jsonb AS advertencias,
                a.equipo_local,
                a.equipo_visitante,
                a.fecha_partido,
                a.mercado,
                a.lado,
                a.linea,
                a.probabilidad_sistema,
                a.confianza_sistema,
                a.valor_esperado,
                a.creado_en,
                a.actualizado_en,
                a.usuario_id
            FROM apuestas a
            UNION ALL
            SELECT
                f.id,
                'futbol'::text AS deporte,
                'SIMPLE'::text AS tipo_apuesta,
                f.resultado::text AS resultado,
                f.stake,
                f.ganancia,
                f.cuota,
                NULL::numeric AS cuota_total,
                NULL::int AS n_selecciones,
                NULL::int AS selecciones_ganadas,
                NULL::int AS selecciones_perdidas,
                NULL::int AS selecciones_push,
                NULL::int AS selecciones_pendientes,
                NULL::boolean AS tiene_mismo_partido,
                NULL::jsonb AS advertencias,
                f.equipo_local,
                f.equipo_visitante,
                f.fecha_partido,
                f.mercado::text AS mercado,
                f.lado,
                f.linea,
                f.probabilidad_sistema,
                f.confianza_sistema::text AS confianza_sistema,
                f.valor_esperado,
                f.creado_en,
                f.actualizado_en,
                f.usuario_id
            FROM apuestas_futbol f
            UNION ALL
            SELECT
                c.id,
                'baloncesto'::text AS deporte,
                'COMBINADA'::text AS tipo_apuesta,
                c.resultado,
                c.stake,
                c.ganancia,
                NULL::numeric AS cuota,
                c.cuota_total,
                c.n_selecciones,
                c.selecciones_ganadas,
                c.selecciones_perdidas,
                c.selecciones_push,
                c.selecciones_pendientes,
                c.tiene_mismo_partido,
                to_jsonb(c.advertencias) AS advertencias,
                NULL::text AS equipo_local,
                NULL::text AS equipo_visitante,
                NULL::date AS fecha_partido,
                NULL::text AS mercado,
                NULL::text AS lado,
                NULL::numeric AS linea,
                c.probabilidad_ajustada AS probabilidad_sistema,
                c.confianza_sistema,
                c.valor_esperado,
                c.creado_en,
                c.actualizado_en,
                c.usuario_id
            FROM apuestas_combinadas c
        )
    """

    try:
        with obtener_pool().connection() as conexion:
            with conexion.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    f"""
                    {bitacora_cte}
                    SELECT COUNT(*) AS total
                    FROM bitacora_global
                    WHERE {where_sql}
                    """,
                    parametros,
                )
                total = cursor.fetchone()["total"]

                cursor.execute(
                    f"""
                    {bitacora_cte}
                    SELECT *
                    FROM bitacora_global
                    WHERE {where_sql}
                    ORDER BY {orden_sql}
                    LIMIT %s OFFSET %s
                    """,
                    [*parametros, tamano, offset],
                )
                registros = cursor.fetchall()

                combinada_ids = [registro["id"] for registro in registros if registro["tipo_apuesta"] == "COMBINADA"]
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
                        selecciones_por_combinada.setdefault(fila["combinada_id"], []).append(fila)
    except Exception:
        logger.exception("Fallo bitácora unificada; devolviendo respuesta vacía de contingencia")
        total = 0
        registros = []
        selecciones_por_combinada = {}

    total_paginas = max(1, (total + tamano - 1) // tamano) if total else 0

    registros_final = []
    for registro in registros:
        if registro["tipo_apuesta"] == "COMBINADA":
            registro["selecciones"] = selecciones_por_combinada.get(registro["id"], [])
        registros_final.append(registro)

    payload_legacy = RespuestaBitacoraUnificada(
        exito=True,
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        registros=registros_final,
    ).model_dump(mode="json")
    return _respuesta_contrato(payload_legacy, version, response, "unificada")


@router.get('/apuestas-analizadas', summary='Listar apuestas analizadas automáticas')
async def listar_apuestas_analizadas(
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    limite: int = 200,
    offset: int = 0,
):
    """Lista apuestas analizadas automáticas (bitácora de análisis del sistema)."""
    from servicios.apuestas_analizadas import asegurar_tabla_apuestas_analizadas, resolver_apuestas_analizadas
    from psycopg.rows import dict_row
    resolver_apuestas_analizadas()
    pool = obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, deporte, partido_id, mercado, lado, linea,
                       probabilidad_sistema, confianza, estado, resultado_outcome,
                       valor_real, resultado_resumen, creado_en, actualizado_en
                FROM apuestas_analizadas
                ORDER BY actualizado_en DESC
                LIMIT %s OFFSET %s
                """,
                [max(1, min(limite, 1000)), max(0, offset)],
            )
            filas = cur.fetchall() or []
    payload_legacy = {"exito": True, "total": len(filas), "items": filas}
    return _respuesta_contrato(payload_legacy, version, response, "apuestas-analizadas")


@router.get("/{apuesta_id}", summary="Detalle de apuesta")
async def obtener_apuesta(
    apuesta_id: UUID,
    response: Response,
    version: str = Query(default="legacy", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
):
    """Obtiene una apuesta por ID validando pertenencia."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT * FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )
            apuesta = cursor.fetchone()

    if not apuesta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada.")

    payload_legacy = RespuestaApuesta(exito=True, apuesta=apuesta).model_dump(mode="json")
    return _respuesta_contrato(payload_legacy, version, response, str(apuesta_id))


@router.patch("/{apuesta_id}/resultado", summary="Actualizar resultado")
async def actualizar_resultado(
    apuesta_id: UUID,
    peticion: PeticionActualizarResultado,
    response: Response,
    version: str = Query(default="legacy", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
):
    """Actualiza el resultado de una apuesta pendiente."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT resultado FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )
            fila = cursor.fetchone()

            if not fila:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada.")
            if fila["resultado"] != "PENDIENTE":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Solo se pueden resolver apuestas pendientes.",
                )

            cursor.execute(
                """
                UPDATE apuestas
                SET resultado = %s,
                    puntos_reales = %s
                WHERE id = %s AND usuario_id = %s
                RETURNING *
                """,
                [peticion.resultado, peticion.puntos_reales, str(apuesta_id), str(usuario_id)],
            )
            apuesta = cursor.fetchone()

    payload_legacy = RespuestaApuesta(exito=True, apuesta=apuesta).model_dump(mode="json")
    return _respuesta_contrato(payload_legacy, version, response, f"{apuesta_id}/resultado")


@router.delete("/{apuesta_id}", summary="Eliminar apuesta")
async def eliminar_apuesta(
    apuesta_id: UUID,
    response: Response,
    version: str = Query(default="legacy", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
):
    """Elimina una apuesta pendiente."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT resultado FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )
            fila = cursor.fetchone()

            if not fila:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada.")
            if fila["resultado"] != "PENDIENTE":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Solo se pueden eliminar apuestas pendientes.",
                )

            cursor.execute(
                """
                DELETE FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )

    payload_legacy = {"exito": True, "mensaje": "Apuesta eliminada."}
    return _respuesta_contrato(payload_legacy, version, response, str(apuesta_id))


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE RESOLUCIÓN AUTOMÁTICA DE APUESTAS
# ═══════════════════════════════════════════════════════════════════════════


class RespuestaResolucion(BaseModel):
    """Respuesta del endpoint de resolución."""

    exito: bool
    resumen: dict = Field(..., description="Resumen de la resolución")


class RespuestaEstadisticas(BaseModel):
    """Respuesta del endpoint de estadísticas."""

    exito: bool
    estadisticas: dict = Field(..., description="Estadísticas de apuestas")
    pendientes_por_mercado: dict = Field(..., description="Pendientes por mercado")


@router.post(
    "/resolver",
    summary="Resolver apuestas pendientes",
    response_model=RespuestaResolucion,
    description="""
    Resuelve automáticamente apuestas PENDIENTE usando datos de partidos.

    ## Requisitos:
    - La apuesta debe tener `partido_id` válido
    - El partido debe tener puntos registrados para el mercado

    ## Proceso:
    1. Busca apuestas PENDIENTE con partido_id
    2. Obtiene puntos reales del partido
    3. Compara valor real vs línea según mercado y lado
    4. Actualiza resultado (GANADA/PERDIDA/PUSH) y ganancia

    ## Parámetros opcionales:
    - `mercado`: Solo resolver apuestas de un mercado específico
    - `limite`: Máximo de apuestas a procesar (default 1000)
    """,
)
async def resolver_apuestas_pendientes(
    usuario_id: UUID = Depends(obtener_usuario_id),
    mercado: Optional[str] = Query(
        None,
        pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$",
        description="Filtrar por mercado específico",
    ),
    limite: int = Query(1000, ge=1, le=5000, description="Máximo de apuestas a procesar"),
    hasta: Optional[date] = Query(None, description="Solo resolver hasta esta fecha"),
) -> RespuestaResolucion:
    """Resuelve apuestas pendientes automáticamente."""
    try:
        resumen = resolver_apuestas(
            usuario_id=str(usuario_id),
            mercado=mercado,
            limite=limite,
            solo_hasta_fecha=hasta,
        )

        logger.info(
            "Resolución completada para usuario=%s: %d resueltas, %d pendientes, %d errores",
            usuario_id,
            resumen.resueltas,
            resumen.pendientes,
            resumen.errores,
        )

        return RespuestaResolucion(exito=True, resumen=resumen.to_dict())

    except Exception as e:
        logger.exception("Error resolviendo apuestas para usuario=%s", usuario_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolviendo apuestas: {str(e)}",
        )


@router.get(
    "/estadisticas",
    summary="Estadísticas de apuestas",
    description="""
    Obtiene estadísticas completas de las apuestas del usuario.

    Incluye:
    - Total de apuestas
    - Desglose por resultado (pendientes, ganadas, perdidas, push)
    - Win rate y ROI
    - Apuestas sin partido_id (no resolubles automáticamente)
    - Pendientes por mercado
    """,
)
async def obtener_estadisticas(
    response: Response,
    version: str = Query(default="legacy", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
):
    """Obtiene estadísticas de apuestas del usuario."""
    _auto_resolver_bitacoras(usuario_id)

    try:
        estadisticas = obtener_estadisticas_apuestas(usuario_id=str(usuario_id))
        pendientes_por_mercado = obtener_apuestas_pendientes_por_mercado(
            usuario_id=str(usuario_id)
        )

        payload_legacy = RespuestaEstadisticas(
            exito=True,
            estadisticas=estadisticas,
            pendientes_por_mercado=pendientes_por_mercado,
        ).model_dump(mode="json")
        return _respuesta_contrato(payload_legacy, version, response, "estadisticas")

    except Exception as e:
        logger.exception("Error obteniendo estadísticas para usuario=%s", usuario_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT DE MÉTRICAS DESDE BITÁCORA
# ═══════════════════════════════════════════════════════════════════════════


class MetricaMercadoBitacora(BaseModel):
    """Métricas de un mercado específico desde bitácora."""

    mercado: str
    total: int
    ganadas: int
    perdidas: int
    push: int
    win_rate: Optional[float] = None
    stake_total: float
    ganancia_total: float
    roi: Optional[float] = None
    edge_promedio: Optional[float] = None
    probabilidad_promedio: Optional[float] = None


class MetricaConfianzaBitacora(BaseModel):
    """Métricas por nivel de confianza."""

    confianza: str
    total: int
    ganadas: int
    perdidas: int
    win_rate: Optional[float] = None
    stake_total: float
    ganancia_total: float
    roi: Optional[float] = None


class MetricaTemporalBitacora(BaseModel):
    """Métricas temporales (por mes)."""

    periodo: str
    total: int
    ganadas: int
    perdidas: int
    win_rate: Optional[float] = None
    ganancia: float
    roi: Optional[float] = None


class RespuestaMetricasBitacora(BaseModel):
    """Respuesta completa de métricas desde bitácora."""

    exito: bool
    periodo: dict
    resumen_global: dict
    por_mercado: List[MetricaMercadoBitacora]
    por_confianza: List[MetricaConfianzaBitacora]
    por_mes: List[MetricaTemporalBitacora]
    advertencias: List[str] = Field(default_factory=list)


@router.get(
    "/metricas",
    summary="Métricas calculadas desde bitácora",
    description="""
    Calcula métricas de rendimiento directamente desde la bitácora de apuestas.

    A diferencia de `/api/metricas/calibracion` que usa predicciones_registradas,
    este endpoint trabaja con apuestas reales guardadas por el usuario.

    ## Métricas incluidas:
    - **Resumen global**: total, win rate, ROI, ganancia/pérdida
    - **Por mercado**: Q1, Q2, Q3, Q4, COMPLETO
    - **Por confianza**: ALTA, MEDIA, BAJA
    - **Por mes**: tendencia temporal

    ## Filtros:
    - `desde`: Fecha inicio (YYYY-MM-DD)
    - `hasta`: Fecha fin (YYYY-MM-DD)
    - `mercado`: Filtrar por mercado específico
    """,
)
async def obtener_metricas_bitacora(
    response: Response,
    version: str = Query(default="legacy", pattern="^(v2|legacy)$"),
    usuario_id: UUID = Depends(obtener_usuario_id),
    desde: Optional[date] = Query(None, description="Fecha inicio"),
    hasta: Optional[date] = Query(None, description="Fecha fin"),
    mercado: Optional[str] = Query(
        None,
        pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$",
        description="Filtrar por mercado",
    ),
) -> RespuestaMetricasBitacora:
    """Calcula métricas desde la bitácora de apuestas."""
    _auto_resolver_bitacoras(usuario_id)

    advertencias: List[str] = []

    # Construir filtros base (global compartido)
    condiciones = ["resultado IN ('GANADA', 'PERDIDA', 'PUSH')"]
    parametros: List[object] = []

    if desde:
        condiciones.append("fecha_partido >= %s")
        parametros.append(desde)
    if hasta:
        condiciones.append("fecha_partido <= %s")
        parametros.append(hasta)
    if mercado:
        condiciones.append("mercado = %s")
        parametros.append(mercado)

    where_sql = " AND ".join(condiciones)

    try:
        with obtener_pool().connection() as conexion:
            with conexion.cursor(row_factory=dict_row) as cursor:
                # 1. Resumen global
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                        COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                        COUNT(*) FILTER (WHERE resultado = 'PUSH') AS push,
                        COALESCE(SUM(stake), 0) AS stake_total,
                        COALESCE(SUM(ganancia), 0) AS ganancia_total,
                        AVG(edge_real) FILTER (WHERE edge_real IS NOT NULL) AS edge_promedio,
                        AVG(probabilidad_sistema) FILTER (WHERE probabilidad_sistema IS NOT NULL) AS prob_promedio
                    FROM apuestas
                    WHERE {where_sql}
                    """,
                    parametros,
                )
                resumen_row = cursor.fetchone() or {}

                total = resumen_row.get("total", 0)
                ganadas = resumen_row.get("ganadas", 0)
                perdidas = resumen_row.get("perdidas", 0)
                stake_total = float(resumen_row.get("stake_total", 0))
                ganancia_total = float(resumen_row.get("ganancia_total", 0))

                resumen_global = {
                    "total": total,
                    "ganadas": ganadas,
                    "perdidas": perdidas,
                    "push": resumen_row.get("push", 0),
                    "win_rate": round(ganadas / (ganadas + perdidas), 4) if (ganadas + perdidas) > 0 else None,
                    "stake_total": stake_total,
                    "ganancia_total": ganancia_total,
                    "roi": round(ganancia_total / stake_total, 4) if stake_total > 0 else None,
                    "edge_promedio": round(float(resumen_row.get("edge_promedio") or 0), 4) or None,
                    "probabilidad_promedio": round(float(resumen_row.get("prob_promedio") or 0), 4) or None,
                }

                if total < 30:
                    advertencias.append(f"Solo {total} apuestas resueltas. Mínimo recomendado: 30.")

                # 2. Por mercado
                cursor.execute(
                    f"""
                    SELECT
                        mercado,
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                        COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                        COUNT(*) FILTER (WHERE resultado = 'PUSH') AS push,
                        COALESCE(SUM(stake), 0) AS stake_total,
                        COALESCE(SUM(ganancia), 0) AS ganancia_total,
                        AVG(edge_real) FILTER (WHERE edge_real IS NOT NULL) AS edge_promedio,
                        AVG(probabilidad_sistema) FILTER (WHERE probabilidad_sistema IS NOT NULL) AS prob_promedio
                    FROM apuestas
                    WHERE {where_sql}
                    GROUP BY mercado
                    ORDER BY mercado
                    """,
                    parametros,
                )
                por_mercado = []
                for row in cursor.fetchall():
                    m_ganadas = row["ganadas"]
                    m_perdidas = row["perdidas"]
                    m_stake = float(row["stake_total"])
                    m_ganancia = float(row["ganancia_total"])
                    por_mercado.append(
                        MetricaMercadoBitacora(
                            mercado=row["mercado"],
                            total=row["total"],
                            ganadas=m_ganadas,
                            perdidas=m_perdidas,
                            push=row["push"],
                            win_rate=round(m_ganadas / (m_ganadas + m_perdidas), 4) if (m_ganadas + m_perdidas) > 0 else None,
                            stake_total=m_stake,
                            ganancia_total=m_ganancia,
                            roi=round(m_ganancia / m_stake, 4) if m_stake > 0 else None,
                            edge_promedio=round(float(row["edge_promedio"] or 0), 4) or None,
                            probabilidad_promedio=round(float(row["prob_promedio"] or 0), 4) or None,
                        )
                    )

                # 3. Por confianza
                cursor.execute(
                    f"""
                    SELECT
                        confianza_sistema AS confianza,
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                        COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                        COALESCE(SUM(stake), 0) AS stake_total,
                        COALESCE(SUM(ganancia), 0) AS ganancia_total
                    FROM apuestas
                    WHERE {where_sql} AND confianza_sistema IS NOT NULL
                    GROUP BY confianza_sistema
                    ORDER BY
                        CASE confianza_sistema
                            WHEN 'ALTA' THEN 1
                            WHEN 'MEDIA' THEN 2
                            WHEN 'BAJA' THEN 3
                        END
                    """,
                    parametros,
                )
                por_confianza = []
                for row in cursor.fetchall():
                    c_ganadas = row["ganadas"]
                    c_perdidas = row["perdidas"]
                    c_stake = float(row["stake_total"])
                    c_ganancia = float(row["ganancia_total"])
                    por_confianza.append(
                        MetricaConfianzaBitacora(
                            confianza=row["confianza"],
                            total=row["total"],
                            ganadas=c_ganadas,
                            perdidas=c_perdidas,
                            win_rate=round(c_ganadas / (c_ganadas + c_perdidas), 4) if (c_ganadas + c_perdidas) > 0 else None,
                            stake_total=c_stake,
                            ganancia_total=c_ganancia,
                            roi=round(c_ganancia / c_stake, 4) if c_stake > 0 else None,
                        )
                    )

                # 4. Por mes
                cursor.execute(
                    f"""
                    SELECT
                        TO_CHAR(fecha_partido, 'YYYY-MM') AS periodo,
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                        COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                        COALESCE(SUM(ganancia), 0) AS ganancia,
                        COALESCE(SUM(stake), 0) AS stake_total
                    FROM apuestas
                    WHERE {where_sql} AND fecha_partido IS NOT NULL
                    GROUP BY TO_CHAR(fecha_partido, 'YYYY-MM')
                    ORDER BY periodo DESC
                    LIMIT 12
                    """,
                    parametros,
                )
                por_mes = []
                for row in cursor.fetchall():
                    t_ganadas = row["ganadas"]
                    t_perdidas = row["perdidas"]
                    t_ganancia = float(row["ganancia"])
                    t_stake = float(row["stake_total"])
                    por_mes.append(
                        MetricaTemporalBitacora(
                            periodo=row["periodo"],
                            total=row["total"],
                            ganadas=t_ganadas,
                            perdidas=t_perdidas,
                            win_rate=round(t_ganadas / (t_ganadas + t_perdidas), 4) if (t_ganadas + t_perdidas) > 0 else None,
                            ganancia=t_ganancia,
                            roi=round(t_ganancia / t_stake, 4) if t_stake > 0 else None,
                        )
                    )

        payload_legacy = RespuestaMetricasBitacora(
            exito=True,
            periodo={
                "desde": desde.isoformat() if desde else "sin_limite",
                "hasta": hasta.isoformat() if hasta else "sin_limite",
            },
            resumen_global=resumen_global,
            por_mercado=por_mercado,
            por_confianza=por_confianza,
            por_mes=por_mes,
            advertencias=advertencias,
        ).model_dump(mode="json")
        return _respuesta_contrato(payload_legacy, version, response, "metricas")

    except Exception as e:
        logger.exception("Error calculando métricas de bitácora para usuario=%s", usuario_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculando métricas: {str(e)}",
        )


