#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "docs" / "reportes"

TH = {
    "min_resueltas_validacion": 120,
    "min_lineas_validacion": 2,
    "max_brier_promocion": 0.23,
    "max_logloss_promocion": 0.67,
    "max_ece_promocion": 0.06,
    "max_drift": 0.03,
    "min_resolution_rate": 0.70,
    "max_fallback": 0.35,
}


def sev(score: float) -> str:
    if score >= 0.8:
        return "CRITICA"
    if score >= 0.5:
        return "ALTA"
    if score >= 0.25:
        return "MEDIA"
    return "BAJA"


def load(name: str) -> Dict[str, Any]:
    return json.loads((REPORTS / name).read_text())


def main() -> None:
    b10 = load("BLOQUE_10_WALKFORWARD_SCORECARD_FUTBOL.json")
    b12 = load("BLOQUE_12_MONITOREO_AUTODEMOTION_FUTBOL.json")
    b13 = load("BLOQUE_13_SHADOW_MODE_OPERATIVO_FUTBOL.json")

    by10 = {m["mercado"]: m for m in b10["scorecard_market"]}
    by12 = {d["mercado"]: d for d in b12["decisiones"]}
    mensal = {m["mercado"]: m for m in b13["ventanas"].get("mensual", [])}

    matrix: List[Dict[str, Any]] = []
    cause_group = {
        "volumen_resuelto_insuficiente": "resolucion/outcomes",
        "coverage_lineas_insuficiente": "coverage",
        "calibracion_fuera_tolerancia": "calibracion",
        "inestabilidad_ventanas": "monitoreo/gates",
        "tasa_resolucion_operativa_baja": "resolucion/outcomes",
        "fallback_alto": "datos/ETL",
        "datos_incompletos_o_estado_mercado": "monitoreo/gates",
        "auto_demotion_activo": "monitoreo/gates",
        "features_modelado_insuficiente": "modelo/features",
    }
    grouped = defaultdict(Counter)

    for mercado, s in by10.items():
        m12 = by12.get(mercado, {})
        m13 = mensal.get(mercado, {})

        causes: List[Dict[str, Any]] = []

        n_res = float(s.get("n_resueltas") or 0)
        c1 = max(0.0, (TH["min_resueltas_validacion"] - n_res) / TH["min_resueltas_validacion"])
        if c1 > 0:
            causes.append({"causa": "volumen_resuelto_insuficiente", "severidad": sev(c1), "evidencia": {"n_resueltas": n_res, "umbral": TH["min_resueltas_validacion"]}})

        lineas = float(s.get("lineas_cubiertas") or 0)
        c2 = max(0.0, (TH["min_lineas_validacion"] - lineas) / max(TH["min_lineas_validacion"], 1))
        if c2 > 0:
            causes.append({"causa": "coverage_lineas_insuficiente", "severidad": sev(c2), "evidencia": {"lineas": lineas, "umbral": TH["min_lineas_validacion"]}})

        brier = float(s.get("brier") or 0)
        logl = float(s.get("log_loss") or 0)
        ece = float(s.get("ece") or 0)
        c3 = max(brier / TH["max_brier_promocion"], logl / TH["max_logloss_promocion"], ece / TH["max_ece_promocion"]) - 1.0
        if c3 > 0:
            causes.append({"causa": "calibracion_fuera_tolerancia", "severidad": sev(min(1.0, c3)), "evidencia": {"brier": brier, "log_loss": logl, "ece": ece}})

        drift = abs(float(s.get("window_drift_brier") or 0))
        c4 = max(0.0, drift / TH["max_drift"] - 1.0)
        if c4 > 0:
            causes.append({"causa": "inestabilidad_ventanas", "severidad": sev(min(1.0, c4)), "evidencia": {"drift": drift, "umbral": TH["max_drift"]}})

        tasa_op = float(m13.get("tasa_resolucion") or 0)
        tasa_eval = float((m12.get("metricas") or {}).get("resolved_rate") or 0)
        tasa = min(tasa_op if tasa_op > 0 else 1.0, tasa_eval if tasa_eval > 0 else 1.0)
        if tasa <= 0:
            tasa = max(tasa_op, tasa_eval)
        c5 = max(0.0, (TH["min_resolution_rate"] - tasa) / TH["min_resolution_rate"])
        if c5 > 0:
            causes.append({"causa": "tasa_resolucion_operativa_baja", "severidad": sev(c5), "evidencia": {"tasa_operativa": tasa_op, "tasa_eval": tasa_eval, "umbral": TH["min_resolution_rate"]}})

        fb = max(float(s.get("fallback_rate") or 0), float((m12.get("metricas") or {}).get("fallback_rate") or 0), float(m13.get("fallback_rate") or 0))
        c6 = max(0.0, fb / TH["max_fallback"] - 1.0)
        if c6 > 0:
            causes.append({"causa": "fallback_alto", "severidad": sev(min(1.0, c6)), "evidencia": {"fallback_rate": fb, "umbral": TH["max_fallback"]}})

        m12_motivos = m12.get("motivos") or []
        if any(x in m12_motivos for x in ["estado_mercado_no_estable", "volumen_o_resolucion_critica"]):
            causes.append({"causa": "datos_incompletos_o_estado_mercado", "severidad": "ALTA", "evidencia": {"motivos_monitor": m12_motivos}})

        if "auto_demotion" in m12_motivos:
            causes.append({"causa": "auto_demotion_activo", "severidad": "ALTA", "evidencia": {"estado_actual": m12.get("estado_actual"), "estado_nuevo": m12.get("estado_nuevo")}})

        # proxy: muy bajo volumen con calibración aparentemente buena suele indicar modelo no validado en operación
        if n_res < 20:
            causes.append({"causa": "features_modelado_insuficiente", "severidad": "MEDIA", "evidencia": {"proxy": "muestra insuficiente para validar señal de modelo"}})

        # rescue score: más alto = más rescatable
        rescue = (
            min(1.0, n_res / 120.0) * 0.35
            + min(1.0, lineas / 4.0) * 0.15
            + max(0.0, 1.0 - min(1.0, brier / TH["max_brier_promocion"])) * 0.20
            + max(0.0, 1.0 - min(1.0, ece / TH["max_ece_promocion"])) * 0.10
            + max(0.0, min(1.0, tasa_op)) * 0.10
            + max(0.0, 1.0 - min(1.0, fb)) * 0.10
        )

        for c in causes:
            grouped[cause_group[c["causa"]]][c["causa"]] += 1

        matrix.append({
            "mercado": mercado,
            "estado_actual": s.get("status_final"),
            "causas": causes,
            "rescue_score": round(rescue, 4),
            "evidencia": {
                "n_resueltas": n_res,
                "lineas_cubiertas": lineas,
                "brier": brier,
                "log_loss": logl,
                "ece": ece,
                "resolved_rate_monitor": tasa_eval,
                "resolved_rate_operativo": tasa_op,
                "fallback_rate": fb,
            },
        })

    ranking = sorted(matrix, key=lambda x: x["rescue_score"], reverse=True)
    top = [r["mercado"] for r in ranking[:3]]

    out = {
        "snapshot": b10.get("resumen", {}),
        "matriz_causal_por_mercado": matrix,
        "agrupacion_causas": {k: dict(v) for k, v in grouped.items()},
        "ranking_rescate": [{"mercado": r["mercado"], "rescue_score": r["rescue_score"]} for r in ranking],
        "recomendacion_foco": {
            "mercados_prioritarios": top,
            "rationale": "priorizados por mejor score de rescate (coverage relativo + menor degradación + señal calibración) dentro del bloqueo total actual"
        }
    }

    json_path = REPORTS / "BLOQUE_15_AUDITORIA_CAUSAL_BLOQUEO_FUTBOL.json"
    json_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    md = REPORTS / "BLOQUE_15_AUDITORIA_CAUSAL_BLOQUEO_FUTBOL.md"
    lines = [
        "# BLOQUE 15 — Auditoría de causa raíz de bloqueo total por mercado (fútbol)",
        "",
        "## Resumen ejecutivo",
        f"- Snapshot: {out['snapshot']}",
        "- Diagnóstico causal: el bloqueo 24/24 se explica principalmente por **volumen resuelto insuficiente** + **tasa de resolución operativa baja** + **demotions automáticos activos**.",
        "",
        "## Agrupación de causas raíz",
    ]
    for g, causes in out["agrupacion_causas"].items():
        lines.append(f"- **{g}**: {causes}")
    lines += [
        "",
        "## Ranking de rescate (más rescatable -> menos)",
    ]
    for i, r in enumerate(out["ranking_rescate"], 1):
        lines.append(f"{i}. {r['mercado']} (score={r['rescue_score']})")

    lines += [
        "",
        "## Recomendación de foco (siguiente fase, máximo 2-3 mercados)",
        f"- Prioritarios: {', '.join(top)}",
        "- Estrategia: concentrar ingesta/resolución/outcomes y cobertura de líneas solo en estos mercados durante 2 ventanas de monitoreo antes de expandir.",
        "",
        "## Tabla causal por mercado",
        "| Mercado | Estado | Causas principales |",
        "|---|---|---|",
    ]
    for m in matrix:
        c = ", ".join(sorted({x['causa'] for x in m['causas']}))
        lines.append(f"| {m['mercado']} | {m['estado_actual']} | {c} |")

    lines += [
        "",
        "## Riesgos residuales",
        "- Con volumen actual, cualquier mejora de métricas puntuales puede ser estadísticamente frágil.",
        "- Sin fortalecer resolución de outcomes y cobertura de líneas, el gate seguirá bloqueando mercados aunque UI/contrato estén limpios.",
        "",
        "## Siguiente frente técnico con foco",
        "1) Resolver pipeline de outcomes/resolución para elevar tasa resuelta por mercado.",
        "2) Aumentar coverage de líneas en mercados priorizados.",
        "3) Re-correr walk-forward + monitoreo en 2 ventanas consecutivas y reauditar." 
    ]
    md.write_text("\n".join(lines))
    print(f"Generados: {json_path.name}, {md.name}")


if __name__ == "__main__":
    main()
