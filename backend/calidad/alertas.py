# -*- coding: utf-8 -*-
"""Generación y consulta de alertas operacionales de calidad (Bloque 08)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"MEDIA": 1, "ALTA": 2, "CRITICA": 3}


@dataclass(frozen=True)
class AlertCandidate:
    alert_id: str
    severity: str
    component: str
    title: str
    condition_text: str
    incident_key: str
    root_cause: str
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    warning_type: Optional[str] = None
    warning_severity: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


def _normalizar_domain(domain: str) -> str:
    dom = (domain or "").strip().upper()
    if dom == "FOOTBALL":
        return "FUTBOL"
    if dom not in {"NBA", "FUTBOL"}:
        raise ValueError(f"Dominio no soportado: {domain}")
    return dom


def _query_value(conn: Any, query: str, params: tuple) -> float:
    with conn.cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    return float((row[0] if row else 0) or 0)


def _obtener_criticas_activas(conn: Any, domain: str, periodo: date) -> int:
    sql = """
    SELECT COUNT(*)
    FROM analytics.dq_rule_results
    WHERE domain = %s AND periodo = %s AND severity = 'Crítica' AND failed_rows > 0
    """
    return int(_query_value(conn, sql, (domain, periodo)))


def _drift_consecutivo_rojo(conn: Any, periodo: date) -> int:
    consecutivos = 0
    day = periodo
    while True:
        sql = """
        SELECT COALESCE(MAX(drift_signal_level), 'none')
        FROM analytics.dq_rule_results
        WHERE domain = 'FUTBOL' AND periodo = %s
        """
        with conn.cursor() as cur:
            cur.execute(sql, (day,))
            row = cur.fetchone()
        level = (row[0] if row and row[0] else "none")
        if level != "red":
            break
        consecutivos += 1
        day = day - timedelta(days=1)
    return consecutivos


def _debounce_ok(conn: Any, domain: str, periodo: date, candidate: AlertCandidate, debounce_periods: int) -> bool:
    if candidate.severity == "CRITICA":
        return True
    prev_period = periodo - timedelta(days=1)
    sql = """
    SELECT COUNT(*)
    FROM analytics.dq_alerts
    WHERE domain=%s AND alert_id=%s AND incident_key=%s
      AND periodo=%s AND emitted = TRUE
    """
    prev_count = int(_query_value(conn, sql, (domain, candidate.alert_id, candidate.incident_key, prev_period)))
    return prev_count >= max(1, debounce_periods - 1)


def _upsert_alert(conn: Any, domain: str, periodo: date, candidate: AlertCandidate, emitted: bool) -> None:
    sql = """
    INSERT INTO analytics.dq_alerts (
      periodo, domain, alert_id, severity, component, title, condition_text,
      incident_key, root_cause, status, emitted, trigger_value, threshold_value,
      warning_type, warning_severity, payload
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
    ON CONFLICT (periodo, domain, alert_id, incident_key)
    DO UPDATE SET
      updated_at = NOW(),
      repeat_count = analytics.dq_alerts.repeat_count + 1,
      emitted = analytics.dq_alerts.emitted OR EXCLUDED.emitted,
      status = CASE
        WHEN analytics.dq_alerts.status = 'RESOLVED' THEN 'OPEN'
        ELSE analytics.dq_alerts.status
      END,
      payload = EXCLUDED.payload
    """
    import json

    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                periodo,
                domain,
                candidate.alert_id,
                candidate.severity,
                candidate.component,
                candidate.title,
                candidate.condition_text,
                candidate.incident_key,
                candidate.root_cause,
                "OPEN" if emitted else "SUPPRESSED",
                emitted,
                candidate.trigger_value,
                candidate.threshold_value,
                candidate.warning_type,
                candidate.warning_severity,
                json.dumps(candidate.payload or {}),
            ),
        )


def _evaluar_alertas(conn: Any, scorecard_result: Dict[str, Any], domain: str, periodo: date) -> List[AlertCandidate]:
    dom = _normalizar_domain(domain)
    candidates: List[AlertCandidate] = []

    nivel = str(scorecard_result.get("nivel", "")).upper()
    score = float(scorecard_result.get("score_final", 0.0))
    criticas_activas = int(scorecard_result.get("criticas_activas", 0))
    drift_signal_level = str(scorecard_result.get("drift_signal_level", "none"))

    if dom == "NBA" and nivel == "C":
        candidates.append(AlertCandidate("DQ-CRIT-01", "CRITICA", "Scorecard", "Nivel C en NBA", "Scorecard NBA en nivel C", "nba_nivel_c", "scorecard", score, 70.0, "quality", "high"))

    if criticas_activas > 0 or _obtener_criticas_activas(conn, dom, periodo) > 0:
        candidates.append(AlertCandidate("DQ-CRIT-02", "CRITICA", "ReglasCriticas", "Regla crítica activa", "Existe al menos una regla crítica con fallo", f"{dom.lower()}_criticas_activas", "dq_rule_results", float(max(criticas_activas, 1)), 0.0, "quality", "high"))

    if dom == "FUTBOL":
        if drift_signal_level == "orange":
            candidates.append(AlertCandidate("DQ-HIGH-05", "ALTA", "Drift", "Drift naranja fútbol", "Drift naranja activo en fútbol", "fut_drift_orange", "drift_runtime", None, None, "drift", "high"))
        if drift_signal_level == "yellow":
            candidates.append(AlertCandidate("DQ-MED-05", "MEDIA", "Drift", "Drift amarillo fútbol", "Drift amarillo detectado en fútbol", "fut_drift_yellow", "drift_runtime", None, None, "drift", "medium"))

        rojos = _drift_consecutivo_rojo(conn, periodo)
        if rojos >= 3:
            candidates.append(AlertCandidate("DQ-CRIT-03", "CRITICA", "Drift", "Drift rojo sostenido fútbol", "Drift rojo detectado por 3+ periodos consecutivos", "fut_drift_red_3d", "drift_runtime", float(rojos), 3.0, "drift", "high"))

    # Alertas de cobertura y outlier/freshness desde vw_data_quality_core
    if dom == "NBA":
        outlier = _query_value(conn, "SELECT COALESCE(MAX(outlier_rate),0) FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND periodo=%s", (periodo,))
        if outlier > 0.10:
            candidates.append(AlertCandidate("DQ-HIGH-03", "ALTA", "Outliers", "Outlier rate elevado NBA", "Outlier rate > 0.10", "nba_outlier_rate", "vw_data_quality_core", outlier, 0.10, "outlier", "medium"))

        cov = _query_value(conn, "SELECT COALESCE(MIN(source_coverage),0) FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND periodo=%s", (periodo,))
        if cov < 30:
            candidates.append(AlertCandidate("DQ-MED-01", "MEDIA", "Coverage", "Cobertura baja NBA", "Cobertura por debajo de mínimo esperado", "nba_coverage_low", "vw_data_quality_core", cov, 30.0, "coverage", "low"))
    else:
        cov_fut = _query_value(conn, "SELECT COALESCE(MIN(source_coverage),0) FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas_futbol','predicciones_futbol') AND periodo=%s", (periodo,))
        if cov_fut < 10:
            candidates.append(AlertCandidate("DQ-MED-02", "MEDIA", "Coverage", "Cobertura baja fútbol", "Cobertura fútbol por debajo de mínimo esperado", "fut_coverage_low", "vw_data_quality_core", cov_fut, 10.0, "coverage", "low"))

    return candidates


def generar_alertas(conn: Any, scorecard_result: Dict[str, Any], domain: str, periodo: date, debounce_periods: int = 2) -> Dict[str, Any]:
    """Genera y persiste alertas operacionales de calidad."""
    dom = _normalizar_domain(domain)

    if str(scorecard_result.get("nivel", "")).upper() == "A" and bool(scorecard_result.get("warning_critico_activo", False)):
        raise ValueError("Hard-check violado: nivel A no puede coexistir con warning crítico activo")

    try:
        candidates = _evaluar_alertas(conn, scorecard_result, dom, periodo)
        emitted_count = 0
        suppressed_count = 0

        for c in candidates:
            emit = _debounce_ok(conn, dom, periodo, c, debounce_periods)
            _upsert_alert(conn, dom, periodo, c, emit)
            if emit:
                emitted_count += 1
            else:
                suppressed_count += 1

        conn.commit()
        return {
            "domain": dom,
            "periodo": periodo.isoformat(),
            "candidatas": len(candidates),
            "emitidas": emitted_count,
            "suprimidas": suppressed_count,
        }
    except Exception:
        conn.rollback()
        logger.exception("Error generando alertas", extra={"domain": dom, "periodo": str(periodo)})
        raise


def obtener_alertas_activas(conn: Any, domain: Optional[str] = None, severidad_min: str = "MEDIA", ventana_dias: int = 14) -> List[Dict[str, Any]]:
    """Obtiene alertas activas (OPEN/ACK) con filtro de severidad mínima."""
    sev_min = severidad_min.upper()
    if sev_min not in SEVERITY_ORDER:
        raise ValueError("severidad_min inválida")

    params: List[Any] = [date.today() - timedelta(days=ventana_dias)]
    sql = """
    SELECT id, periodo, domain, alert_id, severity, component, title, condition_text,
           incident_key, status, emitted, repeat_count, trigger_value, threshold_value,
           warning_type, warning_severity, payload, created_at, updated_at
    FROM analytics.dq_alerts
    WHERE periodo >= %s
      AND status IN ('OPEN', 'ACK')
    """
    if domain:
        dom = _normalizar_domain(domain)
        sql += " AND domain = %s"
        params.append(dom)

    sql += " ORDER BY periodo DESC, created_at DESC"

    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []
    except Exception:
        logger.warning("No fue posible leer dq_alerts (posible tabla no creada aún)")
        return []

    result: List[Dict[str, Any]] = []
    for row in rows:
        sev = row[4]
        if SEVERITY_ORDER.get(sev, 0) < SEVERITY_ORDER[sev_min]:
            continue
        result.append(
            {
                "id": row[0],
                "periodo": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
                "domain": row[2],
                "alert_id": row[3],
                "severity": sev,
                "component": row[5],
                "title": row[6],
                "condition_text": row[7],
                "incident_key": row[8],
                "status": row[9],
                "emitted": row[10],
                "repeat_count": row[11],
                "trigger_value": float(row[12]) if row[12] is not None else None,
                "threshold_value": float(row[13]) if row[13] is not None else None,
                "warning_type": row[14],
                "warning_severity": row[15],
                "payload": row[16] or {},
            }
        )
    return result
