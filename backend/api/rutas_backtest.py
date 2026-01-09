# -*- coding: utf-8 -*-
"""
rutas_backtest.py — Endpoints de backtest incluyendo reporte (T25).
"""

from __future__ import annotations

from datetime import date, datetime
import csv
import hashlib
import io
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from backtesting.metricas.calculador import calcular_metricas_calibracion
from backtesting.metricas.curva_calibracion import calcular_curva_bins_fijos
from db import obtener_pool

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])


@router.get(
    "/{backtest_id}/reporte",
    summary="Obtener reporte de backtest",
    description="""
    Genera un reporte completo del backtest especificado.

    ## Formatos disponibles:
    - `json`: Reporte estructurado completo (default)
    - `csv`: Archivo CSV con predicciones (descargable)

    ## Contenido del reporte:
    1. Configuración del backtest
    2. Métricas por mercado y origen
    3. Curvas de calibración
    4. Alertas y recomendaciones
    5. Trazabilidad completa
    """,
)
async def obtener_reporte_backtest(
    backtest_id: str,
    formato: str = Query("json", pattern="^(json|csv)$"),
    incluir_predicciones: bool = Query(
        False, description="Incluir lista completa de predicciones en JSON"
    ),
):
    """Genera reporte exportable de un backtest."""
    backtest = _obtener_backtest(backtest_id)
    if not backtest:
        raise HTTPException(
            status_code=404, detail=f"Backtest {backtest_id} no encontrado"
        )

    if formato == "csv":
        return _generar_reporte_csv(backtest_id, backtest)

    return _generar_reporte_json(backtest_id, backtest, incluir_predicciones)


def _generar_reporte_json(
    backtest_id: str, backtest: dict, incluir_predicciones: bool
) -> JSONResponse:
    """Genera reporte en formato JSON."""
    config = backtest.get("configuracion", {})
    mercados = backtest.get("mercados") or config.get(
        "mercados", ["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    )
    origenes = _resolver_origenes_backtest(config)

    metricas = _obtener_metricas_backtest(backtest, mercados, origenes)
    curvas = _obtener_curvas_backtest(backtest, mercados, origenes)
    alertas = _obtener_alertas_backtest(backtest, mercados, origenes)
    trazabilidad = _obtener_trazabilidad_backtest(backtest, origenes)

    reporte = {
        "metadata": {
            "backtest_id": backtest_id,
            "fecha_generacion": datetime.now().isoformat(),
            "version_sistema": "2.1.0",
            "formato": "json",
        },
        "configuracion": {
            "periodo": {
                "inicio": backtest.get("fecha_inicio_eval"),
                "fin": backtest.get("fecha_fin_eval"),
            },
            "ventana": {
                "modo": config.get("modo_ventana"),
                "n_temporadas": config.get("n_temporadas"),
                "excluir_pretemporada": config.get("excluir_pretemporada", True),
            },
            "mercados": mercados,
            "lineas_sinteticas": {
                "activo": config.get("usar_lineas_sinteticas", True),
                "offsets": config.get("offsets_linea", [-6, -3, 0, 3, 6]),
            },
        },
        "trazabilidad": trazabilidad,
        "resumen_global": _calcular_resumen_global(backtest, mercados, origenes),
        "metricas_por_mercado": metricas,
        "curvas_calibracion": curvas,
        "alertas": alertas,
        "recomendaciones": _generar_recomendaciones(metricas, alertas),
        "firma_digital": {
            "hash_reporte": _calcular_hash_reporte(metricas, trazabilidad),
            "timestamp": datetime.now().isoformat(),
        },
    }

    if incluir_predicciones:
        reporte["predicciones"] = _obtener_predicciones_backtest(backtest, mercados, origenes)

    return JSONResponse(content=reporte)


def _generar_reporte_csv(backtest_id: str, backtest: dict) -> StreamingResponse:
    """Genera reporte en formato CSV (predicciones)."""
    config = backtest.get("configuracion", {})
    mercados = backtest.get("mercados") or config.get(
        "mercados", ["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    )
    origenes = _resolver_origenes_backtest(config)
    predicciones = _obtener_predicciones_backtest(backtest, mercados, origenes)

    output = io.StringIO(newline="")

    headers = [
        "prediccion_id",
        "fecha_partido",
        "mercado",
        "equipo_local",
        "equipo_visitante",
        "lado",
        "linea",
        "linea_sintetica",
        "p_raw",
        "p_calibrada",
        "media_predicha",
        "desviacion_predicha",
        "valor_real",
        "outcome",
        "modelo_version_id",
        "cutoff_entrenamiento",
    ]

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(headers)

    for pred in predicciones:
        writer.writerow(
            [
                pred.get("id"),
                pred.get("fecha_partido"),
                pred.get("mercado"),
                pred.get("equipo_local"),
                pred.get("equipo_visitante"),
                pred.get("lado"),
                pred.get("linea"),
                pred.get("linea_es_sintetica"),
                pred.get("p_raw"),
                pred.get("p_calibrada"),
                pred.get("media_predicha"),
                pred.get("desviacion_predicha"),
                pred.get("valor_real"),
                _outcome_to_string(pred.get("outcome_binario")),
                pred.get("modelo_version_id"),
                pred.get("cutoff_entrenamiento"),
            ]
        )

    output.seek(0)
    content = "\ufeff" + output.getvalue()

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=backtest_{backtest_id}_predicciones.csv"
            )
        },
    )


def _outcome_to_string(outcome: Optional[bool]) -> str:
    """Convierte outcome binario a string legible."""
    if outcome is None:
        return "PUSH"
    return "WIN" if outcome else "LOSS"


def _generar_recomendaciones(metricas: list, alertas: list) -> list:
    """Genera recomendaciones basadas en métricas y alertas."""
    recomendaciones = []

    eces = [m.get("ece") for m in metricas if m.get("ece") is not None]
    if eces:
        ece_promedio = sum(eces) / len(eces)
        if ece_promedio < 0.03:
            recomendaciones.append(
                f"Calibración EXCELENTE (ECE promedio {ece_promedio:.3f})"
            )
        elif ece_promedio < 0.05:
            recomendaciones.append(
                f"Calibración BUENA (ECE promedio {ece_promedio:.3f})"
            )
        else:
            recomendaciones.append(
                "Calibración REGULAR "
                f"(ECE promedio {ece_promedio:.3f}) - Considerar recalibración"
            )

    sesgos = [m.get("sesgo_media") for m in metricas if m.get("sesgo_media") is not None]
    if sesgos:
        sesgo_promedio = sum(sesgos) / len(sesgos)
        if abs(sesgo_promedio) < 1.0:
            recomendaciones.append(
                f"Sesgo sistemático MÍNIMO ({sesgo_promedio:+.1f} puntos)"
            )
        else:
            direccion = "subestima" if sesgo_promedio > 0 else "sobreestima"
            recomendaciones.append(
                "Sesgo detectado: modelo "
                f"{direccion} por {abs(sesgo_promedio):.1f} puntos"
            )

    alertas_critical = [a for a in alertas if a.get("severidad") == "CRITICAL"]
    if alertas_critical:
        recomendaciones.append(
            f"⚠️ {len(alertas_critical)} alertas CRÍTICAS requieren atención inmediata"
        )

    mercados_problematicos = {
        alerta.get("mercado")
        for alerta in alertas
        if alerta.get("severidad") in ["CRITICAL", "WARNING"]
    }
    if mercados_problematicos:
        recomendaciones.append(
            f"Mercados a revisar: {', '.join(sorted(mercados_problematicos))}"
        )

    if not alertas_critical and all(ece < 0.05 for ece in eces if ece is not None):
        recomendaciones.append("✅ Modelo apto para uso en producción con monitoreo estándar")
    else:
        recomendaciones.append("⚠️ Revisar alertas antes de usar en producción")

    return recomendaciones


def _calcular_hash_reporte(metricas: list, trazabilidad: dict) -> str:
    """Calcula hash de integridad del reporte."""
    contenido = json.dumps(
        {
            "metricas": metricas,
            "trazabilidad": trazabilidad,
        },
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(contenido.encode()).hexdigest()[:16]}"


def _resolver_origenes_backtest(config: dict) -> list[str]:
    origenes = config.get("origenes") or config.get("origen")
    if isinstance(origenes, str):
        return [origenes]
    if isinstance(origenes, list) and origenes:
        return origenes
    return ["BACKTEST_SINTETICO"]


def _obtener_backtest(backtest_id: str) -> Optional[dict]:
    """Obtiene información del backtest."""
    pool = obtener_pool()
    consulta = """
        SELECT
            id,
            estado,
            configuracion_json,
            fecha_inicio_eval,
            fecha_fin_eval,
            mercados,
            iniciado_en,
            completado_en,
            total_predicciones_generadas
        FROM ejecuciones_backtest
        WHERE id = %s
        LIMIT 1
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, [backtest_id])
            fila = cursor.fetchone()

    if not fila:
        return None

    configuracion = fila[2] or {}
    if isinstance(configuracion, str):
        configuracion = json.loads(configuracion)

    return {
        "id": fila[0],
        "estado": fila[1],
        "configuracion": configuracion,
        "fecha_inicio_eval": fila[3],
        "fecha_fin_eval": fila[4],
        "mercados": fila[5] or [],
        "iniciado_en": fila[6],
        "completado_en": fila[7],
        "total_predicciones_generadas": fila[8],
    }


def _obtener_metricas_backtest(
    backtest: dict, mercados: list[str], origenes: list[str]
) -> list:
    """Obtiene métricas calculadas para el backtest."""
    metricas = []
    inicio = backtest.get("fecha_inicio_eval")
    fin = backtest.get("fecha_fin_eval")

    if not inicio or not fin:
        return metricas

    for mercado in mercados:
        for origen in origenes:
            resultado = calcular_metricas_calibracion(
                mercado=mercado,
                origen=origen,
                fecha_inicio=inicio,
                fecha_fin=fin,
            )
            metricas.append(
                {
                    "mercado": mercado,
                    "origen": origen,
                    "n": resultado.get("n_predicciones", 0),
                    "brier_score": resultado.get("brier_score"),
                    "brier_score_raw": resultado.get("brier_score_raw"),
                    "brier_score_calibrado": resultado.get("brier_score_calibrado"),
                    "log_loss": resultado.get("log_loss"),
                    "ece": resultado.get("ece"),
                    "mce": resultado.get("mce"),
                    "mae_media": resultado.get("distribucion", {}).get("mae_media"),
                    "rmse_media": resultado.get("distribucion", {}).get("rmse_media"),
                    "sesgo_media": resultado.get("distribucion", {}).get("sesgo_media"),
                    "base_rate": resultado.get("base_rate"),
                    "interpretacion": _interpretar_metricas(resultado),
                }
            )

    return metricas


def _interpretar_metricas(metricas: dict) -> dict:
    ece = metricas.get("ece")
    brier = metricas.get("brier_score")
    sesgo = metricas.get("distribucion", {}).get("sesgo_media")

    interpretacion = {}
    if ece is None:
        interpretacion["calibracion"] = "SIN_DATOS"
    elif ece < 0.03:
        interpretacion["calibracion"] = "EXCELENTE"
    elif ece < 0.05:
        interpretacion["calibracion"] = "BUENA"
    else:
        interpretacion["calibracion"] = "REGULAR"

    if brier is None:
        interpretacion["precision"] = "SIN_DATOS"
    elif brier < 0.20:
        interpretacion["precision"] = "ALTA"
    elif brier < 0.24:
        interpretacion["precision"] = "ACEPTABLE"
    else:
        interpretacion["precision"] = "BAJA"

    if sesgo is None:
        interpretacion["sesgo"] = "SIN_DATOS"
    elif abs(sesgo) < 1.0:
        interpretacion["sesgo"] = "MINIMO"
    elif abs(sesgo) < 2.5:
        interpretacion["sesgo"] = "MODERADO"
    else:
        interpretacion["sesgo"] = "ALTO"

    return interpretacion


def _obtener_curvas_backtest(
    backtest: dict, mercados: list[str], origenes: list[str]
) -> dict:
    """Obtiene datos de curvas de calibración."""
    curvas: dict[str, dict] = {}
    inicio = backtest.get("fecha_inicio_eval")
    fin = backtest.get("fecha_fin_eval")

    if not inicio or not fin:
        return curvas

    for mercado in mercados:
        for origen in origenes:
            predicciones = _obtener_predicciones_para_curva(
                mercado=mercado,
                origen=origen,
                desde=inicio,
                hasta=fin,
            )
            resultado = calcular_curva_bins_fijos(predicciones)
            curvas.setdefault(mercado, {})[origen] = {
                "tipo_bins": "fijos",
                "bins": [
                    {
                        "rango": f"{bin_item.rango_inicio:.1f}-{bin_item.rango_fin:.1f}",
                        "n": bin_item.n,
                        "p_promedio": bin_item.probabilidad_promedio,
                        "frecuencia_real": bin_item.frecuencia_real,
                        "gap": bin_item.gap,
                    }
                    for bin_item in resultado.bins
                ],
                "ece": resultado.ece,
            }

    return curvas


def _obtener_alertas_backtest(
    backtest: dict, mercados: list[str], origenes: list[str]
) -> list:
    """Obtiene alertas generadas durante/después del backtest."""
    pool = obtener_pool()
    inicio = backtest.get("fecha_inicio_eval")
    fin = backtest.get("fecha_fin_eval")

    if not inicio or not fin:
        return []

    consulta = """
        SELECT mercado, tipo_alerta, severidad, mensaje, detalles_json, origen
        FROM alertas_calibracion
        WHERE periodo_inicio >= %s
          AND periodo_fin <= %s
          AND mercado = ANY(%s)
          AND origen = ANY(%s)
        ORDER BY timestamp_deteccion DESC
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, [inicio, fin, mercados, origenes])
            filas = cursor.fetchall()

    alertas = []
    for fila in filas:
        detalles = fila[4] or {}
        if isinstance(detalles, str):
            detalles = json.loads(detalles)
        alertas.append(
            {
                "mercado": fila[0],
                "tipo": fila[1],
                "severidad": fila[2],
                "mensaje": fila[3],
                "recomendacion": detalles.get("recomendacion"),
                "origen": fila[5],
            }
        )

    return alertas


def _obtener_trazabilidad_backtest(backtest: dict, origenes: list[str]) -> dict:
    """Obtiene información de trazabilidad."""
    pool = obtener_pool()
    inicio = backtest.get("fecha_inicio_eval")
    fin = backtest.get("fecha_fin_eval")

    if not inicio or not fin:
        return {}

    consulta = """
        SELECT
            pr.modelo_version_id,
            mv.hash_datos,
            mv.cutoff_entrenamiento,
            mv.partidos_entrenamiento,
            mv.equipos
        FROM predicciones_registradas pr
        LEFT JOIN modelo_versiones mv ON mv.id = pr.modelo_version_id
        WHERE pr.fecha_partido >= %s
          AND pr.fecha_partido <= %s
          AND pr.origen = ANY(%s)
        ORDER BY pr.fecha_partido DESC
        LIMIT 1
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, [inicio, fin, origenes])
            fila = cursor.fetchone()

    if not fila:
        return {}

    return {
        "modelo_version_id": fila[0],
        "modelo_hash": fila[1],
        "cutoff_entrenamiento": fila[2],
        "partidos_entrenamiento": fila[3],
        "equipos_incluidos": fila[4],
        "hash_datos_backtest": _calcular_hash_datos_backtest(backtest),
    }


def _calcular_resumen_global(
    backtest: dict, mercados: list[str], origenes: list[str]
) -> dict:
    """Calcula resumen global del backtest."""
    pool = obtener_pool()
    inicio = backtest.get("fecha_inicio_eval")
    fin = backtest.get("fecha_fin_eval")

    if not inicio or not fin:
        return {}

    consulta = """
        SELECT
            COUNT(*) AS total_predicciones,
            SUM(CASE WHEN resuelto THEN 1 ELSE 0 END) AS total_resueltas,
            SUM(CASE WHEN outcome_binario IS NULL THEN 1 ELSE 0 END) AS total_pushes,
            MIN(fecha_partido) AS primera_prediccion,
            MAX(fecha_partido) AS ultima_prediccion
        FROM predicciones_registradas
        WHERE fecha_partido >= %s
          AND fecha_partido <= %s
          AND mercado = ANY(%s)
          AND origen = ANY(%s)
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, [inicio, fin, mercados, origenes])
            fila = cursor.fetchone()

    if not fila:
        return {}

    total_predicciones = int(fila[0] or 0)
    total_resueltas = int(fila[1] or 0)
    total_pushes = int(fila[2] or 0)
    tasa_push = (total_pushes / total_predicciones) if total_predicciones else 0.0

    return {
        "total_predicciones": total_predicciones,
        "total_resueltas": total_resueltas,
        "total_pushes": total_pushes,
        "tasa_push": round(tasa_push, 4),
        "periodo_efectivo": {
            "primera_prediccion": fila[3],
            "ultima_prediccion": fila[4],
        },
    }


def _obtener_predicciones_backtest(
    backtest: dict, mercados: list[str], origenes: list[str]
) -> list:
    """Obtiene todas las predicciones del backtest."""
    pool = obtener_pool()
    inicio = backtest.get("fecha_inicio_eval")
    fin = backtest.get("fecha_fin_eval")

    if not inicio or not fin:
        return []

    consulta = """
        SELECT
            pr.id,
            pr.fecha_partido,
            pr.mercado,
            pr.equipo_local,
            pr.equipo_visitante,
            pr.lado,
            pr.linea,
            pr.linea_es_sintetica,
            pr.p_raw,
            pr.p_calibrada,
            pr.media_predicha,
            pr.desviacion_predicha,
            pr.valor_real,
            pr.outcome_binario,
            pr.modelo_version_id,
            mv.cutoff_entrenamiento
        FROM vista_predicciones_para_calibracion pr
        LEFT JOIN modelo_versiones mv ON mv.id = pr.modelo_version_id
        WHERE pr.fecha_partido >= %s
          AND pr.fecha_partido <= %s
          AND pr.mercado = ANY(%s)
          AND pr.origen = ANY(%s)
        ORDER BY pr.fecha_partido, pr.mercado
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, [inicio, fin, mercados, origenes])
            filas = cursor.fetchall()

    predicciones = []
    for fila in filas:
        predicciones.append(
            {
                "id": fila[0],
                "fecha_partido": fila[1],
                "mercado": fila[2],
                "equipo_local": fila[3],
                "equipo_visitante": fila[4],
                "lado": fila[5],
                "linea": fila[6],
                "linea_es_sintetica": fila[7],
                "p_raw": fila[8],
                "p_calibrada": fila[9],
                "media_predicha": fila[10],
                "desviacion_predicha": fila[11],
                "valor_real": fila[12],
                "outcome_binario": fila[13],
                "modelo_version_id": fila[14],
                "cutoff_entrenamiento": fila[15],
            }
        )

    return predicciones


def _obtener_predicciones_para_curva(
    *,
    mercado: str,
    origen: str,
    desde: date,
    hasta: date,
) -> list[tuple[float, bool]]:
    pool = obtener_pool()
    consulta = """
        SELECT p_efectiva, outcome_binario
        FROM vista_predicciones_para_calibracion
        WHERE mercado = %s
          AND origen = %s
          AND fecha_partido >= %s
          AND fecha_partido <= %s
          AND p_efectiva IS NOT NULL
          AND outcome_binario IS NOT NULL
        ORDER BY fecha_partido
    """
    params = [mercado, origen, desde, hasta]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            filas = cursor.fetchall()

    return [(float(fila[0]), bool(fila[1])) for fila in filas]


def _calcular_hash_datos_backtest(backtest: dict) -> str:
    payload = {
        "fecha_inicio_eval": _serializar_fecha(backtest.get("fecha_inicio_eval")),
        "fecha_fin_eval": _serializar_fecha(backtest.get("fecha_fin_eval")),
        "mercados": backtest.get("mercados"),
        "configuracion": backtest.get("configuracion"),
    }
    contenido = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(contenido.encode()).hexdigest()[:16]


def _serializar_fecha(valor: Optional[date]) -> Optional[str]:
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor
    return valor.isoformat()
