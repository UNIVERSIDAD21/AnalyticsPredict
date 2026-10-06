"""Scorecard local del corte single-user; no modifica datos ni envía alertas."""

from __future__ import annotations

from typing import Any


def _entero(valor: Any) -> int | None:
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def evaluar_corte(reporte: dict[str, Any]) -> dict[str, Any]:
    """Evalúa agregados auditados, sin convertir ausencias en cero ni inferir caída de fuentes."""
    nba = reporte.get("nba_datos") or {}
    futbol = reporte.get("futbol_datos") or {}
    pnl = (reporte.get("bitacora_nba") or {}).get("calidad_pnl") or {}
    temporal = reporte.get("walk_forward_nba_auditoria_metadata") or {}
    pred_futbol = reporte.get("predicciones_futbol") or {}
    integridad = reporte.get("null_outliers_integridad") or {}
    reglas: list[dict[str, Any]] = []

    def agregar(clave: str, dominio: str, valor: int | float | None, limite: str,
                estado: str, motivo: str) -> None:
        reglas.append({"id": clave, "dominio": dominio, "valor": valor,
                       "umbral": limite, "estado": estado, "motivo": motivo})

    for dominio, datos, clave in (
        ("NBA", nba, "partidos_ultimos_30_dias"),
        ("FUTBOL", futbol, "finalizados_ultimos_30_dias"),
    ):
        valor = _entero(datos.get(clave))
        agregar(f"{dominio}-FRESH-30", dominio, valor, ">=1 observación en 30 días; interpretar con calendario",
                "NO_EVALUABLE" if valor is None else "OBSERVAR" if valor == 0 else "OK",
                "Cero observaciones no prueba caída de la fuente ni certifica actualidad fuera de temporada.")

    for dominio, datos, clave in (
        ("NBA", nba, "duplicados_source_id"),
        ("FUTBOL", futbol, "duplicados_sofascore_id"),
    ):
        valor = _entero(datos.get(clave))
        agregar(f"{dominio}-DUP-ID", dominio, valor, "0 duplicados por ID de fuente no nulo",
                "NO_EVALUABLE" if valor is None else "CRITICO" if valor > 0 else "OK",
                "La regla no detecta duplicados de partidos sin identificador de fuente.")

    total_nba = _entero(nba.get("partidos"))
    sin_fuente = _entero(nba.get("sin_source"))
    tasa_sin_fuente = sin_fuente / total_nba if total_nba and sin_fuente is not None else None
    agregar("NBA-SOURCE-NULL", "NBA", round(tasa_sin_fuente, 6) if tasa_sin_fuente is not None else None,
            "<=1% histórico sin source; revisar procedencia antes de modelar",
            "NO_EVALUABLE" if tasa_sin_fuente is None else "OBSERVAR" if tasa_sin_fuente > 0.01 else "OK",
            "No inventar procedencia para registros legacy.")

    cero_cero = _entero(nba.get("cero_cero"))
    agregar("NBA-SCORE-00", "NBA", cero_cero, "0 casos sin clasificar como finalizados válidos",
            "NO_EVALUABLE" if cero_cero is None else "OBSERVAR" if cero_cero > 0 else "OK",
            "Conservar 0–0 hasta distinguir programado, cancelado y error de marcador.")

    finalizados = _entero(futbol.get("finalizados"))
    for mercado, clave in (("CORNERS", "finalizados_con_corners_completos"),
                           ("DISPAROS", "finalizados_con_disparos_completos")):
        completos = _entero(futbol.get(clave))
        tasa = completos / finalizados if finalizados and completos is not None else None
        agregar(f"FUT-{mercado}-COVERAGE", "FUTBOL", round(tasa, 6) if tasa is not None else None,
                ">=95% de finalizados con datos completos para el mercado",
                "NO_EVALUABLE" if tasa is None else "OBSERVAR" if tasa < 0.95 else "OK",
                "Un mercado con cobertura insuficiente permanece beta.")

    inconsistentes = [_entero(pnl.get("ganadas_con_ganancia_inconsistente")),
                      _entero(pnl.get("perdidas_con_ganancia_inconsistente")),
                      _entero(pnl.get("sin_base_valida"))]
    errores_pnl = sum(inconsistentes) if all(v is not None for v in inconsistentes) else None
    agregar("NBA-PNL-CONSISTENCY", "NBA", errores_pnl, "0 inconsistencias; tolerancia absoluta 0,02",
            "NO_EVALUABLE" if errores_pnl is None else "CRITICO" if errores_pnl > 0 else "OK",
            "ROI/profit no certificados cuando hay registros incompatibles con stake/cuota.")

    cutoff = _entero(temporal.get("cutoff_posterior_a_generacion_dia"))
    agregar("NBA-FIT-END", "NBA", cutoff, "0 cutoff posteriores a generación",
            "NO_EVALUABLE" if cutoff is None else "CRITICO" if cutoff > 0 else "OK",
            "No afirmar ausencia de leakage hasta probar fit_end < prediction_time < outcome_time.")

    sin_modelo = _entero(pred_futbol.get("sin_modelo_id"))
    sin_calibrador = _entero(pred_futbol.get("sin_calibrador_id"))
    agregar("FUT-TRACE-MODEL", "FUTBOL", sin_modelo, "0 predicciones sin versión de modelo",
            "NO_EVALUABLE" if sin_modelo is None else "CRITICO" if sin_modelo > 0 else "OK",
            "La ausencia de versión bloquea certificación por modelo.")
    agregar("FUT-TRACE-CAL", "FUTBOL", sin_calibrador, "0 predicciones declaradas calibradas sin ID",
            "NO_EVALUABLE" if sin_calibrador is None else "OBSERVAR" if sin_calibrador > 0 else "OK",
            "Sin ID no atribuir mejora de calibración, aunque p_calibrada esté poblada.")

    for clave, dominio, campo, severidad, umbral in (
        ("NBA-PROB-RANGE", "NBA", "nba_prob_fuera_rango", "CRITICO", "p_raw/p_calibrada en [0,1]"),
        ("FUT-PROB-RANGE", "FUTBOL", "futbol_prob_fuera_rango", "CRITICO", "probabilidades en [0,1]"),
        ("NBA-STAKE-ODDS", "NBA", "nba_stake_cuota_invalidos", "CRITICO", "stake>0 y cuota>1 en resultados binarios"),
        ("FUT-ORPHAN-GAME", "FUTBOL", "futbol_predicciones_partido_huerfano", "CRITICO", "0 predicciones sin partido"),
        ("FUT-GOALS-NULL", "FUTBOL", "futbol_finalizados_goles_nulos", "CRITICO", "0 finalizados sin goles"),
        ("NBA-SCORE-OUTLIER", "NBA", "nba_marcador_outlier_revision", "OBSERVAR", "0 marcadores <0 o >250; solo revisión"),
        ("FUT-GOALS-OUTLIER", "FUTBOL", "futbol_goles_outlier_revision", "OBSERVAR", "0 goles <0 o >30; solo revisión"),
    ):
        valor = _entero(integridad.get(campo))
        agregar(clave, dominio, valor, umbral,
                "NO_EVALUABLE" if valor is None else severidad if valor > 0 else "OK",
                "Los outliers se conservan para revisión; no se corrigen ni excluyen automáticamente.")

    fuentes = reporte.get("fuentes") or {}
    for nombre, dominio in (("ESPN", "NBA"), ("SOFASCORE", "FUTBOL")):
        probe = fuentes.get(nombre) or {}
        http = _entero(probe.get("http_status"))
        json_valido = probe.get("json_valido")
        estado = ("NO_EVALUABLE" if http is None or json_valido is None else
                  "OK" if http == 200 and json_valido is True else "CRITICO")
        agregar(f"{nombre}-AVAILABILITY", dominio, http,
                "HTTP 200 y contrato JSON válido en probe externo separado", estado,
                "403 indica fuente bloqueada; no se infiere disponibilidad desde la frescura de BD.")

    alertas = [{"id": r["id"], "severidad": r["estado"], "valor": r["valor"]}
               for r in reglas if r["estado"] in {"CRITICO", "OBSERVAR"}]
    return {"corte_utc": reporte.get("corte_utc"), "estado": "NO_CERTIFICADO" if any(
        r["estado"] == "CRITICO" for r in reglas) else "REVISAR",
        "reglas": reglas, "alertas_locales": alertas,
        "nota": "Alertas solo en este reporte local; no se envían notificaciones externas."}
