#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor_futbol.automation_diaria import construir_snapshot_consolidado, generar_alertas


def run_script(path: str) -> None:
    subprocess.run([sys.executable, path], cwd=str(ROOT.parent), check=True)


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def main() -> None:
    # Diario mínimo útil: freshness + tracking + readiness.
    run_script("backend/scripts/vigilancia_programado_vencido_b19_6.py")
    run_script("backend/scripts/plan_acumulacion_masa_b19.py")
    run_script("backend/scripts/gate_readiness_corners_b18.py")

    reports = ROOT.parent / "docs" / "reportes"
    freshness = read_json(reports / "BLOQUE_19_6_VIGILANCIA_PROGRAMADO_VENCIDO.json")
    tracking = read_json(reports / "BLOQUE_19_PLAN_ACUMULACION_MASA_CORNERS.json")

    curr = construir_snapshot_consolidado(tracking, freshness)

    state_path = reports / "BLOQUE_19_7_AUTOMATION_STATE.json"
    prev_state = read_json(state_path)
    prev = prev_state.get("snapshot") if prev_state else None

    alerts = generar_alertas(prev, curr)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bloque": "19.7",
        "regla": "B20 no se ejecuta automáticamente; solo se registra habilitación del gate.",
        "snapshot": curr,
        "alertas": alerts,
        "gate_b20": {
            "habilitado": curr.get("gate_b20", False),
            "motivo": curr.get("gate_b20_motivo"),
            "accion": "NO_EJECUTAR_B20_AUTOMATICO",
        },
        "scheduling": {
            "daily": [
                "backend/scripts/vigilancia_programado_vencido_b19_6.py",
                "backend/scripts/plan_acumulacion_masa_b19.py",
                "backend/scripts/gate_readiness_corners_b18.py",
                "backend/scripts/automation_diaria_corners_b19_7.py"
            ],
            "weekly": [
                "backend/scripts/auditoria_resolucion_corners_b19_5.py"
            ],
            "on_gate_change": [
                "backend/scripts/re_scorecard_corners_b17.py"
            ],
        },
    }

    out_json = reports / "BLOQUE_19_7_AUTOMATION_DIARIA_CORNERS.json"
    out_md = reports / "BLOQUE_19_7_AUTOMATION_DIARIA_CORNERS.md"
    out_json.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    lines = [
        "# BLOQUE 19.7 — Automatización diaria consolidada corners prioritarios",
        "",
        "## Snapshot",
        f"- Gate B20 habilitado: {'SÍ' if out['gate_b20']['habilitado'] else 'NO'}",
        f"- Señal freshness: {curr.get('senal_freshness')}",
        "",
        "## Estado por mercado",
        "| Mercado | Masa | Pendientes | Readiness | Gate reevaluación | SANO | AMARILLO | VENCIDO |",
        "|---|---:|---:|---|---|---:|---:|---:|",
    ]
    for m in curr.get("mercados", []):
        lines.append(
            f"| {m['mercado']} | {m['masa_actual']} | {m['pendientes']} | {m['readiness_status']} | "
            f"{'SÍ' if m['gate_reevaluacion_seria'] else 'NO'} | {m['programado_sano']} | {m['programado_amarillo']} | {m['programado_vencido']} |"
        )

    lines += [
        "",
        "## Alertas",
    ]
    for a in alerts:
        lines.append(f"- [{a['tipo']}] {a['mensaje']}")

    lines += [
        "",
        "## Regla de disparo controlado",
        "- Aunque gate B20 se habilite, este flujo NO ejecuta B20 automáticamente.",
        "- Solo registra el cambio y deja evidencia para decisión explícita.",
    ]

    out_md.write_text("\n".join(lines))
    state_path.write_text(json.dumps({"updated_at": out["generated_at"], "snapshot": curr}, indent=2, ensure_ascii=False))

    print(f"Generados: {out_json.name}, {out_md.name}, {state_path.name}")


if __name__ == "__main__":
    main()
