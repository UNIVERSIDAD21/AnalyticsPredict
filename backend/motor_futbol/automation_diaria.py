from __future__ import annotations

from typing import Any, Dict, List


def construir_snapshot_consolidado(
    readiness_tracking: Dict[str, Any],
    freshness: Dict[str, Any],
) -> Dict[str, Any]:
    plan = {x["mercado"]: x for x in readiness_tracking.get("plan_operativo", [])}
    fres = {x["mercado"]: x for x in freshness.get("resumen_mercados", [])}

    mercados: List[Dict[str, Any]] = []
    for mercado in sorted(set(plan.keys()) | set(fres.keys())):
        p = plan.get(mercado, {})
        f = fres.get(mercado, {})
        mercados.append(
            {
                "mercado": mercado,
                "masa_actual": p.get("masa_actual"),
                "gaps_actuales": p.get("gaps_actuales"),
                "pendientes": (p.get("readiness_actual") or {}).get("pendientes"),
                "readiness_status": (p.get("readiness_actual") or {}).get("status"),
                "gate_reevaluacion_seria": p.get("puede_disparar_nueva_reevaluacion_seria"),
                "programado_sano": f.get("programado_sano"),
                "programado_amarillo": f.get("programado_amarillo"),
                "programado_vencido": f.get("programado_vencido"),
            }
        )

    return {
        "mercados": mercados,
        "gate_b20": (readiness_tracking.get("gate_disparo_b20") or {}).get("habilitado", False),
        "gate_b20_motivo": (readiness_tracking.get("gate_disparo_b20") or {}).get("motivo"),
        "senal_freshness": (freshness.get("senal_operativa") or {}).get("tipo"),
    }


def generar_alertas(prev: Dict[str, Any] | None, curr: Dict[str, Any]) -> List[Dict[str, str]]:
    alerts: List[Dict[str, str]] = []

    if prev is None:
        return [{"tipo": "primer_snapshot", "mensaje": "Snapshot inicial generado; sin comparación previa."}]

    prev_m = {x["mercado"]: x for x in prev.get("mercados", [])}
    curr_m = {x["mercado"]: x for x in curr.get("mercados", [])}

    prev_vencidos = sum((x.get("programado_vencido") or 0) for x in prev.get("mercados", []))
    curr_vencidos = sum((x.get("programado_vencido") or 0) for x in curr.get("mercados", []))
    if prev_vencidos == 0 and curr_vencidos > 0:
        alerts.append({"tipo": "primer_vencido", "mensaje": f"Apareció el primer PROGRAMADO vencido ({curr_vencidos})."})

    prev_amarillo = sum((x.get("programado_amarillo") or 0) for x in prev.get("mercados", []))
    curr_amarillo = sum((x.get("programado_amarillo") or 0) for x in curr.get("mercados", []))
    if curr_amarillo > prev_amarillo:
        alerts.append({"tipo": "sube_amarillo", "mensaje": f"Subió AMARILLO de {prev_amarillo} a {curr_amarillo}."})

    for mercado, c in curr_m.items():
        p = prev_m.get(mercado, {})

        if (c.get("masa_actual") or 0) > (p.get("masa_actual") or 0):
            alerts.append({"tipo": "sube_masa", "mensaje": f"{mercado} aumentó masa resolutiva: {(p.get('masa_actual') or 0)} -> {(c.get('masa_actual') or 0)}."})

        prev_ready = p.get("readiness_status")
        curr_ready = c.get("readiness_status")
        if prev_ready and curr_ready and prev_ready != curr_ready:
            alerts.append({"tipo": "cambio_readiness", "mensaje": f"{mercado} cambió readiness: {prev_ready} -> {curr_ready}."})

        if (not p.get("gate_reevaluacion_seria")) and bool(c.get("gate_reevaluacion_seria")):
            alerts.append({"tipo": "gate_reevaluacion_habilitado", "mensaje": f"{mercado} habilitó gate de reevaluación seria."})

    if (not prev.get("gate_b20")) and bool(curr.get("gate_b20")):
        alerts.append({"tipo": "gate_b20_habilitado", "mensaje": "Gate B20 quedó habilitado por primera vez (no ejecutar automático)."})

    if not alerts:
        alerts.append({"tipo": "sin_cambios_relevantes", "mensaje": "Sin cambios relevantes en vigilancia diaria."})

    return alerts
