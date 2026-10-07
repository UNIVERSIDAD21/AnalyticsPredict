"""Auditoría read-only del P&L NBA; no corrige el histórico ni certifica ROI."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


BACKEND = Path(__file__).resolve().parents[1]
TOLERANCIA = Decimal("0.02")


def clasificar_fila(fila: dict[str, Any]) -> dict[str, Any]:
    """Distingue consistencia aritmética de procedencia externa aún no probada."""
    resultado = fila["resultado"]
    stake = fila["stake"]
    cuota = fila["cuota"]
    ganancia = fila["ganancia"]
    salida = {"estado_pnl": "NO_EVALUABLE", "motivo": None,
              "ganancia_esperada": None, "patron_hipotetico": None,
              "cuota_lado_discrepante": False}
    if resultado not in {"GANADA", "PERDIDA", "PUSH", "ANULADA"}:
        salida["estado_pnl"] = "PENDIENTE_O_DESCONOCIDO"
        salida["motivo"] = "RESULTADO_NO_FINAL"
        return salida
    if fila.get("partido_id") is None:
        salida["motivo"] = "APUESTA_SIN_PARTIDO_VINCULADO"
        return salida
    if fila.get("partido_cero_cero"):
        salida["motivo"] = "RESULTADO_PARTIDO_CERO_CERO_NO_ACREDITADO"
        return salida
    if fila.get("partido_valido") is False:
        salida["motivo"] = "PARTIDO_INVALIDADO"
        return salida
    puntos = fila.get("puntos_partido")
    linea = fila.get("linea")
    lado = fila.get("lado")
    if (resultado in {"GANADA", "PERDIDA", "PUSH"} and puntos is not None
            and linea is not None and lado in {"OVER", "UNDER"}):
        esperado_deportivo = ("PUSH" if puntos == linea else
                              "GANADA" if (puntos > linea) == (lado == "OVER") else
                              "PERDIDA")
        if resultado != esperado_deportivo:
            salida["motivo"] = "RESULTADO_INCOMPATIBLE_CON_MARCADOR"
            return salida
    if stake is None or ganancia is None or stake <= 0:
        salida["motivo"] = "STAKE_O_GANANCIA_INVALIDO"
        return salida
    if resultado in {"GANADA", "PERDIDA"} and (cuota is None or cuota <= 1):
        salida["motivo"] = "CUOTA_DECIMAL_INVALIDA"
        return salida

    esperado = stake * (cuota - 1) if resultado == "GANADA" else (
        -stake if resultado == "PERDIDA" else Decimal("0")
    )
    salida["ganancia_esperada"] = esperado
    if abs(ganancia - esperado) <= TOLERANCIA:
        salida["estado_pnl"] = "ARITMETICAMENTE_CONSISTENTE"
        salida["motivo"] = "NO_CERTIFICADO_SIN_EVIDENCIA_PRIMARIA"
    else:
        salida["motivo"] = "GANANCIA_INCOMPATIBLE_CON_STAKE_CUOTA_RESULTADO"
        if abs(ganancia - esperado / 2) <= TOLERANCIA:
            salida["patron_hipotetico"] = "MITAD_DE_FORMULA_NO_DEMOSTRADA"
    cuota_lado = (fila.get("cuota_over") if fila.get("lado") == "OVER" else
                  fila.get("cuota_under") if fila.get("lado") == "UNDER" else None)
    if cuota_lado is not None and cuota is not None and abs(cuota_lado - cuota) > TOLERANCIA:
        salida["cuota_lado_discrepante"] = True
        if salida["estado_pnl"] == "ARITMETICAMENTE_CONSISTENTE":
            salida["estado_pnl"] = "NO_EVALUABLE"
            salida["motivo"] = "CUOTA_REGISTRADA_DISCREPA_DEL_LADO"
    return salida


def resumir_subconjunto_aritmetico(detalle: list[dict[str, Any]]) -> dict[str, Any]:
    """Métricas descriptivas solo de filas binarias conciliables; nunca certificadas."""
    incluidas = [f for f in detalle if f["estado_pnl"] == "ARITMETICAMENTE_CONSISTENTE"
                 and f["resultado"] in {"GANADA", "PERDIDA"}]

    def agregar(filas: list[dict[str, Any]]) -> dict[str, Any]:
        stake = sum((Decimal(f["stake"]) for f in filas), Decimal("0"))
        profit = sum((Decimal(f["ganancia_esperada"]) for f in filas), Decimal("0"))
        fechas = sorted(f["fecha_partido"] for f in filas if f["fecha_partido"])
        return {
            "n": len(filas), "ganadas": sum(f["resultado"] == "GANADA" for f in filas),
            "perdidas": sum(f["resultado"] == "PERDIDA" for f in filas),
            "profit_neto_formula": str(profit) if filas else None,
            "stake_total": str(stake) if filas else None,
            "stake_promedio": str(stake / len(filas)) if filas else None,
            "roi_pct_aritmetico_no_certificado": float(100 * profit / stake) if stake > 0 else None,
            "win_rate_pct_registrado": (100 * sum(f["resultado"] == "GANADA" for f in filas) / len(filas)) if filas else None,
            "periodo_desde": fechas[0] if fechas else None,
            "periodo_hasta": fechas[-1] if fechas else None,
            "estado": "NO_CERTIFICADO",
        }

    mercados = sorted({f["mercado"] or "SIN_MERCADO" for f in detalle})
    rangos = {
        "cuota_menor_1_5": lambda x: x < Decimal("1.5"),
        "cuota_1_5_a_2_0": lambda x: Decimal("1.5") <= x <= Decimal("2"),
        "cuota_mayor_2_0": lambda x: x > Decimal("2"),
    }
    return {
        "global": agregar(incluidas),
        "por_mercado": {m: agregar([f for f in incluidas if (f["mercado"] or "SIN_MERCADO") == m]) for m in mercados},
        "por_quarter": {q: agregar([f for f in incluidas if f["mercado"] == q]) for q in ("Q1", "Q2", "Q3", "Q4")},
        "por_rango_cuota": {nombre: agregar([f for f in incluidas if condicion(Decimal(f["cuota"]))])
                            for nombre, condicion in rangos.items()},
    }


def auditar(url: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with psycopg.connect(url, row_factory=dict_row) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        conn.execute("SET LOCAL statement_timeout = '30s'")
        filas = conn.execute(
            """SELECT a.id, a.partido_id, a.fecha_partido, a.mercado, a.lado,
                      a.cuota, a.stake, a.resultado, a.ganancia, a.creado_en,
                      a.fecha_resolucion, a.cuota_over, a.cuota_under,
                      a.stake_porcentaje, a.bankroll_momento, a.linea,
                      pb.valido AS partido_valido,
                      CASE a.mercado
                        WHEN 'COMPLETO' THEN pb.local_total + pb.visitante_total
                        WHEN 'Q1' THEN pb.local_q1 + pb.visitante_q1
                        WHEN 'Q2' THEN pb.local_q2 + pb.visitante_q2
                        WHEN 'Q3' THEN pb.local_q3 + pb.visitante_q3
                        WHEN 'Q4' THEN pb.local_q4 + pb.visitante_q4
                      END AS puntos_partido,
                      (pb.local_total = 0 AND pb.visitante_total = 0) AS partido_cero_cero
               FROM apuestas a LEFT JOIN partidos_baloncesto pb ON pb.id = a.partido_id
               ORDER BY a.creado_en, a.id"""
        ).fetchall()
    detalle = []
    conteos = Counter()
    por_mercado: dict[str, Counter] = {}
    for fila in filas:
        evaluacion = clasificar_fila(fila)
        conteos[evaluacion["estado_pnl"]] += 1
        por_mercado.setdefault(fila["mercado"] or "SIN_MERCADO", Counter())[
            evaluacion["estado_pnl"]
        ] += 1
        detalle.append({
            "id": str(fila["id"]),
            "partido_id_presente": fila["partido_id"] is not None,
            "fecha_partido": fila["fecha_partido"].isoformat() if fila["fecha_partido"] else None,
            "creado_en": fila["creado_en"].isoformat() if fila["creado_en"] else None,
            "fecha_resolucion": fila["fecha_resolucion"].isoformat() if fila["fecha_resolucion"] else None,
            "mercado": fila["mercado"], "lado": fila["lado"],
            "cuota": str(fila["cuota"]) if fila["cuota"] is not None else None,
            "stake": str(fila["stake"]) if fila["stake"] is not None else None,
            "ganancia_registrada": str(fila["ganancia"]) if fila["ganancia"] is not None else None,
            "resultado": fila["resultado"],
            "partido_cero_cero": bool(fila["partido_cero_cero"]),
            "partido_valido": fila["partido_valido"],
            "puntos_partido": fila["puntos_partido"],
            "ganancia_esperada": str(evaluacion["ganancia_esperada"]) if evaluacion["ganancia_esperada"] is not None else None,
            "estado_pnl": evaluacion["estado_pnl"],
            "motivo": evaluacion["motivo"],
            "patron_hipotetico": evaluacion["patron_hipotetico"],
            "cuota_lado_discrepante": evaluacion["cuota_lado_discrepante"],
            "fuente_cuota": "NO_REGISTRADA",
            "unidad_stake": "NO_REGISTRADA",
            "modelo_version_id": "NO_REGISTRADO",
        })
    resumen = {
        "filas_total": len(filas),
        "filas_binarias": sum(1 for f in filas if f["resultado"] in {"GANADA", "PERDIDA"}),
        "estados_pnl": dict(conteos),
        "por_mercado": {k: dict(v) for k, v in sorted(por_mercado.items())},
        "patron_mitad_hipotetico": sum(d["patron_hipotetico"] is not None for d in detalle),
        "cuota_lado_discrepante": sum(d["cuota_lado_discrepante"] for d in detalle),
        "partido_id_ausente": sum(not d["partido_id_presente"] for d in detalle),
        "resultado_partido_cero_cero_no_acreditado": sum(d["partido_cero_cero"] for d in detalle),
        "resultado_incompatible_con_marcador": sum(
            d["motivo"] == "RESULTADO_INCOMPATIBLE_CON_MARCADOR" for d in detalle),
        "resultado_sin_partido_vinculado": sum(
            d["motivo"] == "APUESTA_SIN_PARTIDO_VINCULADO" for d in detalle),
        "fuente_cuota": "NO_REGISTRADA",
        "unidad_stake": "NO_REGISTRADA",
        "roi_certificado": None,
        "dictamen": "NO_CERTIFICADO",
        "subconjunto_aritmetico_no_certificado": resumir_subconjunto_aritmetico(detalle),
    }
    return resumen, detalle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, help="JSON privado con clasificación por fila")
    args = parser.parse_args()
    load_dotenv(BACKEND / ".env", override=False)
    url = os.getenv("DATABASE_URL")
    if not url:
        parser.error("DATABASE_URL no configurada")
    resumen, detalle = auditar(url)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(prefix=".auditoria_pnl_", suffix=".json", dir=args.salida.parent)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
                json.dump({"resumen": resumen, "detalle": detalle}, archivo, indent=2, ensure_ascii=False)
                archivo.write("\n")
            os.replace(temporal, args.salida)
        finally:
            if os.path.exists(temporal):
                os.unlink(temporal)
    print(json.dumps(resumen, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
