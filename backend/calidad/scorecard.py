# -*- coding: utf-8 -*-
"""Cálculo operacional del scorecard de calidad (Bloque 08).

Este módulo implementa:
- ejecución/persistencia de reglas en analytics.dq_rule_results,
- cálculo de scorecard con penalizaciones P_comp + P_drift + P_partial,
- acceso al scorecard más reciente por dominio.

Nota de gobierno:
- La deuda de bloque 05 (confidence parcial, drift fútbol, contratos legacy)
  NO se maquilla. Se refleja en penalizaciones y overrides.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Mapping, Optional

logger = logging.getLogger(__name__)


SEVERITY_WEIGHTS: Mapping[str, float] = {
    "Crítica": 1.00,
    "Alta": 0.60,
    "Media": 0.30,
}

COMPONENT_WEIGHTS: Mapping[str, Mapping[str, float]] = {
    "NBA": {
        "Completitud": 0.25,
        "IntegridadLogica": 0.22,
        "IntegridadTemporal": 0.12,
        "RangosOutliers": 0.14,
        "Freshness": 0.15,
        "Coverage": 0.12,
    },
    "FUTBOL": {
        "Completitud": 0.22,
        "IntegridadLogica": 0.20,
        "IntegridadTemporal": 0.12,
        "RangosOutliers": 0.14,
        "Freshness": 0.12,
        "Coverage": 0.20,
    },
}

DRIFT_PENALTIES: Mapping[str, float] = {
    "none": 0.0,
    "yellow": 5.0,
    "orange": 10.0,
    "red": 15.0,
}


@dataclass(frozen=True)
class RuleDefinition:
    """Definición de una regla de calidad ejecutable en SQL."""

    rule_id: str
    rule_name: str
    domain: str
    category: str
    severity: str
    source_ref: str
    query_sql: str


RULES: List[RuleDefinition] = [
    # NBA (18)
    RuleDefinition("NBA-COMP-01", "Resultado obligatorio en apuestas NBA", "NBA", "Completitud", "Crítica", "apuestas", "SELECT COUNT(*) FILTER (WHERE COALESCE(TRIM(resultado),'')='') AS failed_rows, COUNT(*) AS total_rows FROM apuestas WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("NBA-COMP-02", "Cuota obligatoria en apuestas NBA", "NBA", "Completitud", "Crítica", "apuestas", "SELECT COUNT(*) FILTER (WHERE cuota IS NULL OR cuota <= 0) AS failed_rows, COUNT(*) AS total_rows FROM apuestas WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("NBA-COMP-03", "Mercado obligatorio en predicciones NBA", "NBA", "Completitud", "Alta", "predicciones_registradas", "SELECT COUNT(*) FILTER (WHERE COALESCE(TRIM(mercado),'')='') AS failed_rows, COUNT(*) AS total_rows FROM predicciones_registradas WHERE COALESCE(fecha_partido::date, timestamp_generacion::date) = %s"),
    RuleDefinition("NBA-LOG-01", "Probabilidad en rango [0,1]", "NBA", "IntegridadLogica", "Crítica", "predicciones_registradas", "SELECT COUNT(*) FILTER (WHERE COALESCE(p_calibrada,p_raw) IS NOT NULL AND (COALESCE(p_calibrada,p_raw) < 0 OR COALESCE(p_calibrada,p_raw) > 1)) AS failed_rows, COUNT(*) AS total_rows FROM predicciones_registradas WHERE COALESCE(fecha_partido::date, timestamp_generacion::date) = %s"),
    RuleDefinition("NBA-LOG-02", "Coherencia stake/ganancia", "NBA", "IntegridadLogica", "Alta", "apuestas", "SELECT COUNT(*) FILTER (WHERE ganancia IS NOT NULL AND (stake IS NULL OR stake <= 0)) AS failed_rows, COUNT(*) AS total_rows FROM apuestas WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("NBA-LOG-03", "Outcome binario válido", "NBA", "IntegridadLogica", "Alta", "predicciones_registradas", "SELECT COUNT(*) FILTER (WHERE fecha_partido IS NOT NULL AND outcome_binario IS NULL) AS failed_rows, COUNT(*) AS total_rows FROM predicciones_registradas WHERE COALESCE(fecha_partido::date, timestamp_generacion::date) = %s"),
    RuleDefinition("NBA-TMP-01", "Fecha creación <= fecha partido", "NBA", "IntegridadTemporal", "Media", "apuestas", "SELECT COUNT(*) FILTER (WHERE creado_en IS NOT NULL AND fecha_partido IS NOT NULL AND creado_en > (fecha_partido::timestamp + INTERVAL '24 hours')) AS failed_rows, COUNT(*) AS total_rows FROM apuestas WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("NBA-TMP-02", "Resolución no previa al partido", "NBA", "IntegridadTemporal", "Alta", "apuestas", "SELECT COUNT(*) FILTER (WHERE fecha_resolucion IS NOT NULL AND fecha_partido IS NOT NULL AND fecha_resolucion < (fecha_partido::timestamp - INTERVAL '6 hours')) AS failed_rows, COUNT(*) AS total_rows FROM apuestas WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("NBA-RNG-01", "Outlier ROI monetario extremo", "NBA", "RangosOutliers", "Alta", "analytics.vw_base_metricas_unificadas_v1", "SELECT COUNT(*) FILTER (WHERE roi_pct_monetario IS NOT NULL AND ABS(roi_pct_monetario) > 500) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND periodo = %s"),
    RuleDefinition("NBA-RNG-02", "Outlier ROI unitario extremo", "NBA", "RangosOutliers", "Alta", "analytics.vw_base_metricas_unificadas_v1", "SELECT COUNT(*) FILTER (WHERE roi_unit_pct IS NOT NULL AND ABS(roi_unit_pct) > 500) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND periodo = %s"),
    RuleDefinition("NBA-RNG-03", "Cuota fuera de rango operativo", "NBA", "RangosOutliers", "Media", "analytics.vw_base_metricas_unificadas_v1", "SELECT COUNT(*) FILTER (WHERE odds_value IS NOT NULL AND (odds_value < 1.01 OR odds_value > 20)) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND periodo = %s"),
    RuleDefinition("NBA-FRSH-01", "Lag diario máximo por fuente NBA", "NBA", "Freshness", "Alta", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table IN ('apuestas','predicciones_registradas') AND freshness_lag_horas > 48) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND periodo = %s"),
    RuleDefinition("NBA-FRSH-02", "Completeness mínima diaria NBA", "NBA", "Freshness", "Crítica", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table IN ('apuestas','predicciones_registradas') AND completeness_rate < 0.95) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND periodo = %s"),
    RuleDefinition("NBA-COV-01", "Cobertura mínima diaria apuestas NBA", "NBA", "Coverage", "Media", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table='apuestas' AND source_coverage < 30) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table='apuestas' AND periodo = %s"),
    RuleDefinition("NBA-COV-02", "Cobertura mínima diaria predicciones NBA", "NBA", "Coverage", "Media", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table='predicciones_registradas' AND source_coverage < 30) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table='predicciones_registradas' AND periodo = %s"),
    RuleDefinition("NBA-COV-03", "Coherencia cobertura entre fuentes NBA", "NBA", "Coverage", "Alta", "analytics.vw_data_quality_core", "WITH a AS (SELECT source_coverage cov FROM analytics.vw_data_quality_core WHERE source_table='apuestas' AND periodo = %s), p AS (SELECT source_coverage cov FROM analytics.vw_data_quality_core WHERE source_table='predicciones_registradas' AND periodo = %s) SELECT COUNT(*) FILTER (WHERE GREATEST(a.cov,p.cov)>0 AND ABS(a.cov-p.cov)::numeric / GREATEST(a.cov,p.cov)::numeric > 0.60) AS failed_rows, COUNT(*) AS total_rows FROM a CROSS JOIN p"),
    RuleDefinition("NBA-COV-04", "Outlier rate de fuente NBA", "NBA", "Coverage", "Alta", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table IN ('apuestas','predicciones_registradas') AND outlier_rate > 0.10) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND periodo = %s"),
    RuleDefinition("NBA-DOM-03", "Confidence bucket no nulo en predicciones", "NBA", "IntegridadLogica", "Alta", "analytics.vw_base_metricas_unificadas_v1", "WITH x AS (SELECT AVG(CASE WHEN confidence_bucket='SIN_CONFIANZA' THEN 1.0 ELSE 0 END) r FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND source='predicciones_registradas' AND periodo = %s) SELECT COUNT(*) FILTER (WHERE r > 0.10) AS failed_rows, COUNT(*) AS total_rows FROM x"),
    # FUTBOL (12)
    RuleDefinition("FUT-COMP-01", "Resultado obligatorio en apuestas fútbol", "FUTBOL", "Completitud", "Crítica", "apuestas_futbol", "SELECT COUNT(*) FILTER (WHERE COALESCE(TRIM(resultado),'')='') AS failed_rows, COUNT(*) AS total_rows FROM apuestas_futbol WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("FUT-COMP-02", "Cuota canónica obligatoria", "FUTBOL", "Completitud", "Crítica", "apuestas_futbol", "SELECT COUNT(*) FILTER (WHERE cuota IS NULL OR cuota <= 0) AS failed_rows, COUNT(*) AS total_rows FROM apuestas_futbol WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("FUT-LOG-01", "Probabilidad sistema en rango [0,1]", "FUTBOL", "IntegridadLogica", "Crítica", "apuestas_futbol", "SELECT COUNT(*) FILTER (WHERE probabilidad_sistema IS NOT NULL AND (probabilidad_sistema < 0 OR probabilidad_sistema > 1)) AS failed_rows, COUNT(*) AS total_rows FROM apuestas_futbol WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("FUT-LOG-02", "Coherencia resultado-ganancia", "FUTBOL", "IntegridadLogica", "Alta", "apuestas_futbol", "SELECT COUNT(*) FILTER (WHERE (UPPER(resultado)='GANADA' AND COALESCE(ganancia,0)<=0) OR (UPPER(resultado)='PERDIDA' AND COALESCE(ganancia,0)>0)) AS failed_rows, COUNT(*) AS total_rows FROM apuestas_futbol WHERE COALESCE(fecha_partido::date, creado_en::date) = %s"),
    RuleDefinition("FUT-TMP-01", "Timestamp generación <= fecha partido", "FUTBOL", "IntegridadTemporal", "Media", "predicciones_futbol", "SELECT COUNT(*) FILTER (WHERE timestamp_generacion IS NOT NULL AND fecha_partido IS NOT NULL AND timestamp_generacion > (fecha_partido::timestamp + INTERVAL '24 hours')) AS failed_rows, COUNT(*) AS total_rows FROM predicciones_futbol WHERE COALESCE(fecha_partido::date, timestamp_generacion::date) = %s"),
    RuleDefinition("FUT-TMP-02", "Resolución temporal consistente", "FUTBOL", "IntegridadTemporal", "Alta", "predicciones_futbol", "SELECT COUNT(*) FILTER (WHERE timestamp_resolucion IS NOT NULL AND timestamp_generacion IS NOT NULL AND timestamp_resolucion < timestamp_generacion) AS failed_rows, COUNT(*) AS total_rows FROM predicciones_futbol WHERE COALESCE(fecha_partido::date, timestamp_generacion::date) = %s"),
    RuleDefinition("FUT-RNG-01", "Outlier ROI monetario extremo fútbol", "FUTBOL", "RangosOutliers", "Alta", "analytics.vw_base_metricas_unificadas_v1", "SELECT COUNT(*) FILTER (WHERE roi_pct_monetario IS NOT NULL AND ABS(roi_pct_monetario) > 500) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='FUTBOL' AND periodo = %s"),
    RuleDefinition("FUT-RNG-02", "Confianza bucket inválido", "FUTBOL", "RangosOutliers", "Media", "analytics.vw_base_metricas_unificadas_v1", "SELECT COUNT(*) FILTER (WHERE confidence_bucket NOT IN ('SIN_CONFIANZA','<0.60','0.60-0.69','0.70-0.79','0.80+')) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='FUTBOL' AND periodo = %s"),
    RuleDefinition("FUT-FRSH-01", "Lag diario máximo por fuente fútbol", "FUTBOL", "Freshness", "Alta", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table IN ('apuestas_futbol','predicciones_futbol') AND freshness_lag_horas > 72) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas_futbol','predicciones_futbol') AND periodo = %s"),
    RuleDefinition("FUT-FRSH-02", "Completeness mínima diaria fútbol", "FUTBOL", "Freshness", "Crítica", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table IN ('apuestas_futbol','predicciones_futbol') AND completeness_rate < 0.90) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas_futbol','predicciones_futbol') AND periodo = %s"),
    RuleDefinition("FUT-COV-01", "Cobertura mínima diaria apuestas fútbol", "FUTBOL", "Coverage", "Media", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table='apuestas_futbol' AND source_coverage < 10) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table='apuestas_futbol' AND periodo = %s"),
    RuleDefinition("FUT-COV-02", "Cobertura mínima diaria predicciones fútbol", "FUTBOL", "Coverage", "Media", "analytics.vw_data_quality_core", "SELECT COUNT(*) FILTER (WHERE source_table='predicciones_futbol' AND source_coverage < 10) AS failed_rows, COUNT(*) AS total_rows FROM analytics.vw_data_quality_core WHERE source_table='predicciones_futbol' AND periodo = %s"),
]


def _normalizar_domain(domain: str) -> str:
    dom = (domain or "").strip().upper()
    if dom == "FOOTBALL":
        return "FUTBOL"
    if dom not in {"NBA", "FUTBOL"}:
        raise ValueError(f"Dominio no soportado: {domain}")
    return dom


def _reglas_por_dominio(domain: str) -> List[RuleDefinition]:
    dom = _normalizar_domain(domain)
    return [r for r in RULES if r.domain == dom]


def _ejecutar_query_regla(conn: Any, rule: RuleDefinition, periodo: date) -> Dict[str, float]:
    with conn.cursor() as cur:
        params = (periodo, periodo) if rule.rule_id == "NBA-COV-03" else (periodo,)
        cur.execute(rule.query_sql, params)
        row = cur.fetchone() or (0, 0)
    failed_rows = int(row[0] or 0)
    total_rows = int(row[1] or 0)
    fail_rate = float(failed_rows / total_rows) if total_rows > 0 else 0.0
    return {
        "failed_rows": failed_rows,
        "total_rows": total_rows,
        "fail_rate": fail_rate,
    }


def _upsert_resultado_regla(
    conn: Any,
    *,
    periodo: date,
    domain: str,
    rule: RuleDefinition,
    failed_rows: int,
    total_rows: int,
    fail_rate: float,
    drift_signal_level: str,
) -> None:
    sql = """
    INSERT INTO analytics.dq_rule_results (
        periodo, domain, rule_id, rule_name, category, severity, source_ref,
        failed_rows, total_rows, fail_rate, drift_signal_level, query_sql
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (periodo, domain, rule_id)
    DO UPDATE SET
        executed_at = NOW(),
        rule_name = EXCLUDED.rule_name,
        category = EXCLUDED.category,
        severity = EXCLUDED.severity,
        source_ref = EXCLUDED.source_ref,
        failed_rows = EXCLUDED.failed_rows,
        total_rows = EXCLUDED.total_rows,
        fail_rate = EXCLUDED.fail_rate,
        drift_signal_level = EXCLUDED.drift_signal_level,
        query_sql = EXCLUDED.query_sql
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                periodo,
                domain,
                rule.rule_id,
                rule.rule_name,
                rule.category,
                rule.severity,
                rule.source_ref,
                failed_rows,
                total_rows,
                fail_rate,
                drift_signal_level,
                rule.query_sql,
            ),
        )


def _calcular_drift_signal_level(domain: str, resultados: Iterable[Dict[str, Any]]) -> str:
    """Calcula señal de drift para aplicar penalización en fútbol."""
    dom = _normalizar_domain(domain)
    if dom != "FUTBOL":
        return "none"

    resultados = list(resultados)
    criticas = [r for r in resultados if r["severity"] == "Crítica" and r["failed_rows"] > 0]
    altas = [r for r in resultados if r["severity"] == "Alta" and r["failed_rows"] > 0]

    if len(criticas) >= 2 or any(r["fail_rate"] >= 0.05 for r in criticas):
        return "red"
    if len(altas) >= 2:
        return "orange"
    if len(altas) >= 1:
        return "yellow"
    return "none"


def ejecutar_reglas(conn: Any, domain: str, periodo: date) -> Dict[str, Any]:
    """Ejecuta reglas de calidad de un dominio para un periodo y persiste resultados.

    Args:
        conn: conexión abierta a PostgreSQL.
        domain: "NBA" o "FUTBOL" (acepta "FOOTBALL" como alias).
        periodo: fecha de cálculo de reglas.

    Returns:
        Resumen de ejecución con conteo de reglas y críticos activos.
    """
    dom = _normalizar_domain(domain)
    reglas = _reglas_por_dominio(dom)
    resultados: List[Dict[str, Any]] = []

    try:
        for rule in reglas:
            metrica = _ejecutar_query_regla(conn, rule, periodo)
            resultados.append(
                {
                    "rule_id": rule.rule_id,
                    "category": rule.category,
                    "severity": rule.severity,
                    **metrica,
                }
            )

        drift_level = _calcular_drift_signal_level(dom, resultados)

        for rule, metrica in zip(reglas, resultados):
            _upsert_resultado_regla(
                conn,
                periodo=periodo,
                domain=dom,
                rule=rule,
                failed_rows=metrica["failed_rows"],
                total_rows=metrica["total_rows"],
                fail_rate=metrica["fail_rate"],
                drift_signal_level=drift_level,
            )

        conn.commit()

        criticas_activas = sum(
            1 for r in resultados if r["severity"] == "Crítica" and r["failed_rows"] > 0
        )
        return {
            "domain": dom,
            "periodo": periodo.isoformat(),
            "rules_executed": len(reglas),
            "criticas_activas": criticas_activas,
            "drift_signal_level": drift_level,
        }
    except Exception:
        conn.rollback()
        logger.exception("Error ejecutando reglas de calidad", extra={"domain": dom, "periodo": str(periodo)})
        raise


def _leer_resultados_periodo(conn: Any, domain: str, periodo: date) -> List[Dict[str, Any]]:
    sql = """
    SELECT rule_id, category, severity, failed_rows, total_rows, fail_rate, drift_signal_level
    FROM analytics.dq_rule_results
    WHERE domain = %s AND periodo = %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (domain, periodo))
        rows = cur.fetchall() or []

    resultado = []
    for row in rows:
        resultado.append(
            {
                "rule_id": row[0],
                "category": row[1],
                "severity": row[2],
                "failed_rows": int(row[3] or 0),
                "total_rows": int(row[4] or 0),
                "fail_rate": float(row[5] or 0.0),
                "drift_signal_level": (row[6] or "none"),
            }
        )
    return resultado


def _component_penalties(domain: str, resultados: List[Dict[str, Any]]) -> Dict[str, float]:
    comps = COMPONENT_WEIGHTS[domain]
    penalties: Dict[str, float] = {c: 0.0 for c in comps}

    for comp in comps:
        rows = [r for r in resultados if r["category"] == comp]
        if not rows:
            penalties[comp] = 0.0
            continue
        num = 0.0
        den = 0.0
        for r in rows:
            sev_w = SEVERITY_WEIGHTS[r["severity"]]
            num += sev_w * float(r["fail_rate"])
            den += sev_w
        comp_fail = (num / den) if den > 0 else 0.0
        penalties[comp] = 100.0 * comp_fail * comps[comp]
    return penalties


def _partial_penalty(resultados: List[Dict[str, Any]]) -> float:
    if not resultados:
        return 10.0
    na_rules = sum(1 for r in resultados if int(r["total_rows"]) == 0)
    na_ratio = na_rules / len(resultados)
    if na_ratio <= 0.10:
        return 0.0
    if na_ratio <= 0.30:
        return 5.0
    return 10.0


def _nivel_por_score(score: float) -> str:
    if score >= 90.0:
        return "A"
    if score >= 70.0:
        return "B"
    return "C"


def _aplicar_overrides(
    *,
    nivel_base: str,
    criticas_activas: int,
    maxima_fail_rate_critica: float,
    drift_signal_level: str,
) -> Dict[str, Any]:
    nivel = nivel_base
    override_max_b_por_critica = False
    override_c_automatico = False
    override_drift_red_max_b = False

    if criticas_activas >= 2 or maxima_fail_rate_critica >= 0.05:
        nivel = "C"
        override_c_automatico = True
    elif criticas_activas >= 1 and nivel == "A":
        nivel = "B"
        override_max_b_por_critica = True

    if drift_signal_level == "red" and nivel == "A":
        nivel = "B"
        override_drift_red_max_b = True

    return {
        "nivel": nivel,
        "override_max_b_por_critica": override_max_b_por_critica,
        "override_c_automatico": override_c_automatico,
        "override_drift_red_max_b": override_drift_red_max_b,
    }


def _persistir_scorecard(conn: Any, payload: Dict[str, Any]) -> None:
    sql = """
    INSERT INTO analytics.dq_scorecard_daily (
        periodo, domain, score_final, nivel, criticas_activas,
        drift_penalty, partial_penalty, componentes, overrides
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
    ON CONFLICT (periodo, domain)
    DO UPDATE SET
        calculated_at = NOW(),
        score_final = EXCLUDED.score_final,
        nivel = EXCLUDED.nivel,
        criticas_activas = EXCLUDED.criticas_activas,
        drift_penalty = EXCLUDED.drift_penalty,
        partial_penalty = EXCLUDED.partial_penalty,
        componentes = EXCLUDED.componentes,
        overrides = EXCLUDED.overrides
    """

    import json

    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                payload["periodo"],
                payload["domain"],
                payload["score_final"],
                payload["nivel"],
                payload["criticas_activas"],
                payload["drift_penalty"],
                payload["partial_penalty"],
                json.dumps(payload["componentes"]),
                json.dumps(payload["overrides"]),
            ),
        )


def calcular_scorecard(conn: Any, domain: str, periodo: date) -> Dict[str, Any]:
    """Calcula scorecard de calidad para dominio/periodo.

    Fórmula aplicada (v1.1):
    score = max(0, 100 - P_comp - P_drift - P_partial)

    Incluye overrides críticos:
    - >=1 regla crítica activa => nivel máximo B.
    - >=2 críticas activas o una crítica con fail_rate >=5% => nivel C automático.
    - Drift rojo en fútbol => nivel máximo operativo B.
    """
    dom = _normalizar_domain(domain)

    try:
        resultados = _leer_resultados_periodo(conn, dom, periodo)
        if not resultados:
            raise ValueError(
                f"No hay resultados de reglas para domain={dom}, periodo={periodo}. Ejecuta ejecutar_reglas primero."
            )

        comp_penalties = _component_penalties(dom, resultados)
        p_comp = float(sum(comp_penalties.values()))

        drift_signal_level = max((r["drift_signal_level"] for r in resultados), default="none")
        drift_penalty = float(DRIFT_PENALTIES.get(drift_signal_level, 0.0) if dom == "FUTBOL" else 0.0)

        partial_penalty = float(_partial_penalty(resultados))

        score_base = max(0.0, 100.0 - p_comp - drift_penalty - partial_penalty)
        nivel_base = _nivel_por_score(score_base)

        criticas = [r for r in resultados if r["severity"] == "Crítica" and r["failed_rows"] > 0]
        criticas_activas = len(criticas)
        maxima_fail_rate_critica = max((r["fail_rate"] for r in criticas), default=0.0)

        overrides = _aplicar_overrides(
            nivel_base=nivel_base,
            criticas_activas=criticas_activas,
            maxima_fail_rate_critica=maxima_fail_rate_critica,
            drift_signal_level=drift_signal_level,
        )

        payload = {
            "periodo": periodo,
            "domain": dom,
            "score_final": float(round(score_base, 4)),
            "nivel": overrides["nivel"],
            "criticas_activas": criticas_activas,
            "drift_penalty": float(round(drift_penalty, 4)),
            "partial_penalty": float(round(partial_penalty, 4)),
            "componentes": {k: float(round(v, 4)) for k, v in comp_penalties.items()},
            "overrides": overrides,
            "drift_signal_level": drift_signal_level,
        }

        # Hard-check: no nivel A con crítica activa
        if payload["nivel"] == "A" and criticas_activas > 0:
            payload["nivel"] = "B"
            payload["overrides"]["override_max_b_por_critica"] = True

        _persistir_scorecard(conn, payload)
        conn.commit()

        return {
            "score_final": payload["score_final"],
            "nivel": payload["nivel"],
            "criticas_activas": payload["criticas_activas"],
            "drift_penalty": payload["drift_penalty"],
            "partial_penalty": payload["partial_penalty"],
            "componentes": payload["componentes"],
            "overrides": payload["overrides"],
            "drift_signal_level": payload["drift_signal_level"],
        }
    except Exception:
        conn.rollback()
        logger.exception("Error calculando scorecard", extra={"domain": dom, "periodo": str(periodo)})
        raise


def obtener_scorecard_actual(conn: Any, domain: str) -> Optional[Dict[str, Any]]:
    """Obtiene el scorecard más reciente de un dominio para consumo API."""
    dom = _normalizar_domain(domain)

    sql = """
    SELECT periodo, score_final, nivel, criticas_activas, drift_penalty,
           partial_penalty, componentes, overrides
    FROM analytics.dq_scorecard_daily
    WHERE domain = %s
    ORDER BY periodo DESC
    LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (dom,))
        row = cur.fetchone()

    if not row:
        return None

    return {
        "periodo": row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
        "score_final": float(row[1]),
        "nivel": row[2],
        "criticas_activas": int(row[3]),
        "drift_penalty": float(row[4]),
        "partial_penalty": float(row[5]),
        "componentes": row[6],
        "overrides": row[7],
    }
