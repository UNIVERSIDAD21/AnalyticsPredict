"""Reglas de clasificación contable, sin inferir un stake alternativo."""

from decimal import Decimal

from scripts.auditar_pnl_nba import clasificar_fila, resumir_subconjunto_aritmetico


def _fila(resultado, stake="1000", cuota="1.80", ganancia="800"):
    return {"resultado": resultado, "stake": Decimal(stake) if stake else None,
            "cuota": Decimal(cuota) if cuota else None,
            "ganancia": Decimal(ganancia) if ganancia else None}


def test_ganada_y_perdida_solo_son_consistentes_con_profit_neto():
    assert clasificar_fila(_fila("GANADA"))["estado_pnl"] == "ARITMETICAMENTE_CONSISTENTE"
    assert clasificar_fila(_fila("PERDIDA", ganancia="-1000"))["estado_pnl"] == "ARITMETICAMENTE_CONSISTENTE"
    assert clasificar_fila(_fila("GANADA", ganancia="1800"))["estado_pnl"] == "NO_EVALUABLE"


def test_mitad_de_formula_es_hipotesis_y_no_corrige_stake():
    salida = clasificar_fila(_fila("GANADA", ganancia="400"))
    assert salida["estado_pnl"] == "NO_EVALUABLE"
    assert salida["patron_hipotetico"] == "MITAD_DE_FORMULA_NO_DEMOSTRADA"
    assert salida["ganancia_esperada"] == Decimal("800.00")
    assert clasificar_fila(_fila("PERDIDA", ganancia="-500"))["estado_pnl"] == "NO_EVALUABLE"


def test_anulada_y_datos_incompletos_no_se_convierten_en_roi():
    assert clasificar_fila(_fila("ANULADA", ganancia="0"))["estado_pnl"] == "ARITMETICAMENTE_CONSISTENTE"
    assert clasificar_fila(_fila("ANULADA", ganancia="20"))["estado_pnl"] == "NO_EVALUABLE"
    assert clasificar_fila(_fila("GANADA", stake="", ganancia="800"))["motivo"] == "STAKE_O_GANANCIA_INVALIDO"
    assert clasificar_fila(_fila("GANADA", cuota="1"))["motivo"] == "CUOTA_DECIMAL_INVALIDA"
    assert clasificar_fila(_fila("PENDIENTE"))["estado_pnl"] == "PENDIENTE_O_DESCONOCIDO"


def test_cuota_del_lado_discrepante_excluye_aunque_profit_concilie():
    fila = _fila("GANADA")
    fila.update({"lado": "UNDER", "cuota_under": Decimal("2.10")})
    salida = clasificar_fila(fila)
    assert salida["estado_pnl"] == "NO_EVALUABLE"
    assert salida["motivo"] == "CUOTA_REGISTRADA_DISCREPA_DEL_LADO"


def test_roi_provisional_usa_exclusivamente_mismas_filas_conciliables():
    filas = [
        {"estado_pnl": "ARITMETICAMENTE_CONSISTENTE", "resultado": "GANADA", "stake": "100",
         "cuota": "1.80", "ganancia_esperada": "80", "fecha_partido": "2026-01-01", "mercado": "Q1"},
        {"estado_pnl": "ARITMETICAMENTE_CONSISTENTE", "resultado": "PERDIDA", "stake": "100",
         "cuota": "2.10", "ganancia_esperada": "-100", "fecha_partido": "2026-01-02", "mercado": "COMPLETO"},
        {"estado_pnl": "NO_EVALUABLE", "resultado": "GANADA", "stake": "1000",
         "cuota": "5.00", "ganancia_esperada": "4000", "fecha_partido": "2026-01-03", "mercado": "Q1"},
    ]
    resumen = resumir_subconjunto_aritmetico(filas)
    assert resumen["global"]["n"] == 2
    assert resumen["global"]["profit_neto_formula"] == "-20"
    assert resumen["global"]["roi_pct_aritmetico_no_certificado"] == -10.0
    assert resumen["por_mercado"]["Q1"]["n"] == 1
    assert resumen["por_quarter"]["Q4"]["roi_pct_aritmetico_no_certificado"] is None
    assert resumen["por_rango_cuota"]["cuota_mayor_2_0"]["n"] == 1
