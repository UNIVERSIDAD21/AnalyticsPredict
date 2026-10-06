"""Clasifica trazas NBA read-only; una fecha de partido no sustituye hora de inicio."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


BACKEND = Path(__file__).resolve().parents[1]


def clasificar_traza(fila: dict[str, Any]) -> tuple[str, str]:
    """Invalida orden imposible; no infiere kickoff, fit_end ni outcome externo."""
    pred = fila.get("timestamp_generacion")
    cutoff = fila.get("cutoff_entrenamiento")
    entrenamiento = fila.get("fecha_entrenamiento")
    juego = fila.get("fecha_partido")
    resolucion = fila.get("timestamp_resolucion")
    if pred is None or cutoff is None or entrenamiento is None or juego is None:
        return "NO_DETERMINABLE", "METADATOS_ESENCIALES_AUSENTES"
    if pred.tzinfo is None or entrenamiento.tzinfo is None:
        return "NO_DETERMINABLE", "TIMEZONE_NO_DEMOSTRADO"
    dia_pred_utc = pred.astimezone(timezone.utc).date()
    if cutoff > dia_pred_utc:
        return "TEMPORALMENTE_INVALIDA", "CUTOFF_POSTERIOR_A_GENERACION_UTC"
    if entrenamiento > pred:
        return "TEMPORALMENTE_INVALIDA", "VERSION_REGISTRADA_DESPUES_DE_PREDICCION"
    if resolucion is not None and pred >= resolucion:
        return "TEMPORALMENTE_INVALIDA", "GENERACION_NO_ANTERIOR_A_RESOLUCION"
    if resolucion is None:
        return "NO_DETERMINABLE", "OUTCOME_O_RESOLUCION_AUN_NO_DISPONIBLE"
    fit_end = fila.get("fit_end_preciso")
    inicio_evento = fila.get("inicio_evento_preciso")
    outcome = fila.get("outcome_time_independiente")
    if all((fit_end, inicio_evento, outcome)):
        if any(valor.tzinfo is None for valor in (fit_end, inicio_evento, outcome)):
            return "NO_DETERMINABLE", "TIMEZONE_NO_DEMOSTRADO"
        if fit_end < pred < inicio_evento < outcome:
            return "TEMPORALMENTE_VALIDA", "ORDEN_ESTRICTO_DOCUMENTADO"
        return "TEMPORALMENTE_INVALIDA", "ORDEN_ESTRICTO_INCOMPATIBLE"
    if cutoff == dia_pred_utc:
        return "AMBIGUA", "CUTOFF_Y_GENERACION_MISMO_DIA_SIN_HORA_DE_DATOS"
    if dia_pred_utc >= juego:
        return "AMBIGUA", "FECHA_PARTIDO_SIN_HORA_NI_SEMANTICA_UTC_DEMOSTRADA"
    return "NO_DETERMINABLE", "FALTA_FIT_END_O_HORA_EVENTO_O_OUTCOME_INDEPENDIENTE"


def auditar(url: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with psycopg.connect(url, row_factory=dict_row) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        conn.execute("SET LOCAL statement_timeout = '30s'")
        filas = conn.execute("""
            SELECT p.id, p.partido_id, p.mercado, p.timestamp_generacion,
                   p.fecha_partido, p.timestamp_resolucion, p.resuelto,
                   p.modelo_version_id, m.version AS modelo_version,
                   m.fecha_entrenamiento, m.cutoff_entrenamiento,
                   b.source AS fuente_partido
            FROM predicciones_registradas p
            LEFT JOIN modelo_versiones m ON m.id = p.modelo_version_id
            LEFT JOIN partidos_baloncesto b ON b.id = p.partido_id
            ORDER BY p.timestamp_generacion, p.id
        """).fetchall()
    estados, motivos, mercados = Counter(), Counter(), {}
    detalle = []
    for fila in filas:
        estado, motivo = clasificar_traza(fila)
        estados[estado] += 1
        motivos[motivo] += 1
        mercados.setdefault(fila["mercado"] or "SIN_MERCADO", Counter())[estado] += 1
        detalle.append({
            "id": str(fila["id"]), "partido_id": str(fila["partido_id"]) if fila["partido_id"] else None,
            "mercado": fila["mercado"], "fuente_partido": fila["fuente_partido"],
            "timestamp_generacion": fila["timestamp_generacion"].isoformat() if fila["timestamp_generacion"] else None,
            "fecha_partido": fila["fecha_partido"].isoformat() if fila["fecha_partido"] else None,
            "timestamp_resolucion": fila["timestamp_resolucion"].isoformat() if fila["timestamp_resolucion"] else None,
            "modelo_version_id": fila["modelo_version_id"], "modelo_version": fila["modelo_version"],
            "fecha_entrenamiento": fila["fecha_entrenamiento"].isoformat() if fila["fecha_entrenamiento"] else None,
            "cutoff_entrenamiento": fila["cutoff_entrenamiento"].isoformat() if fila["cutoff_entrenamiento"] else None,
            "fit_end_preciso": None, "inicio_evento_preciso": None,
            "outcome_time_independiente": None,
            "estado_temporal": estado, "motivo": motivo,
        })
    resumen = {
        "total": len(filas), "estados": dict(estados), "motivos": dict(motivos),
        "por_mercado": {k: dict(v) for k, v in sorted(mercados.items())},
        "timezone_comparacion": "UTC",
        "semantica_fecha_partido": "SOLO_FECHA_SIN_HORA_NI_ZONA_CANONICA_DEMOSTRADA",
        "timestamp_resolucion": "HORA_DE_REGISTRO_NO_OUTCOME_INDEPENDIENTE",
        "subconjunto_certificable": estados.get("TEMPORALMENTE_VALIDA", 0),
        "dictamen": "NO_CERTIFICADO",
    }
    return resumen, detalle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, help="JSON privado con clasificación por predicción")
    args = parser.parse_args()
    load_dotenv(BACKEND / ".env", override=False)
    url = os.getenv("DATABASE_URL")
    if not url:
        parser.error("DATABASE_URL no configurada")
    resumen, detalle = auditar(url)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(prefix=".temporalidad_nba_", suffix=".json", dir=args.salida.parent)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
                json.dump({"resumen": resumen, "detalle": detalle}, archivo, ensure_ascii=False, indent=2)
                archivo.write("\n")
            os.replace(temporal, args.salida)
        finally:
            if os.path.exists(temporal):
                os.unlink(temporal)
    print(json.dumps(resumen, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
