from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "futbol_sla_programado_vencido_b19_6.json"


def cargar_politica_sla(path: Path = POLICY_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text())


def horas_desfase(fecha_programada: datetime, ahora: datetime | None = None) -> float:
    ahora = ahora or datetime.now(timezone.utc)
    if fecha_programada.tzinfo is None:
        fecha_programada = fecha_programada.replace(tzinfo=timezone.utc)
    return (ahora - fecha_programada).total_seconds() / 3600.0


def clasificar_programado_por_sla(fecha_programada: datetime, politica: Dict[str, Any], ahora: datetime | None = None) -> str:
    h = horas_desfase(fecha_programada, ahora)
    if h <= float(politica["sla_horas"]["normal_hasta"]):
        return "SANO"
    if h < float(politica["sla_horas"]["vencido_desde"]):
        return "AMARILLO"
    return "VENCIDO"
