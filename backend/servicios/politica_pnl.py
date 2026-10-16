"""Publicación monetaria del histórico sin soportes originales.

El propietario confirmó que no existen soportes. Conciliar una fórmula no acredita
moneda, origen ni instante de cuota/stake. Se preservan filas e importes individuales;
los KPI agregados no publican sumas/ROI como si esa procedencia estuviera acreditada.
"""
from datetime import datetime, timezone


def no_concilia_sql(*, resultado='resultado', stake='stake', cuota='cuota',
                     ganancia='ganancia', cuota_lado=None):
    """Fragmento con expresiones de código/columnas allowlisted, nunca del usuario."""
    resultado = f'({resultado})::text'
    lado = f"AND ({resultado} NOT IN ('GANADA','PERDIDA') OR {cuota_lado} IS NULL OR ABS({cuota} - {cuota_lado}) <= 0.02)" if cuota_lado else ''
    return f"""(
        {resultado} IN ('GANADA','PERDIDA','PUSH','ANULADA')
        AND NOT COALESCE(
            {stake} > 0 AND {ganancia} IS NOT NULL
            AND ({resultado} NOT IN ('GANADA','PERDIDA') OR {cuota} > 1)
            AND ABS({ganancia} - CASE
                WHEN {resultado} = 'GANADA' THEN {stake} * ({cuota} - 1)
                WHEN {resultado} = 'PERDIDA' THEN -{stake} ELSE 0 END) <= 0.02
            {lado}, FALSE)
    )"""


def publicar_pnl(datos, *, n_resueltas=None, n_no_conciliables=None):
    """Un mismo contrato para todos los segmentos; no modifica el argumento."""
    salida = dict(datos)
    if n_resueltas is None:
        n_resueltas = sum(int(datos.get(k) or 0) for k in ('ganadas','perdidas','push','anuladas'))
    n_resueltas = int(n_resueltas)
    for campo in ('roi', 'roi_global', 'ganancia', 'ganancia_total', 'ganancia_neta',
                  'ganancia_acumulada', 'stake_total', 'stake_acumulado'):
        if campo in salida:
            salida[campo] = None
    salida['n_pnl_no_evaluable'] = n_resueltas
    salida['calidad_pnl'] = {
        'estado': 'NO_CERTIFICADO' if n_resueltas else 'NO_EVALUABLE',
        'n_resueltas': n_resueltas, 'n_evaluables': 0, 'n_excluidas': n_resueltas,
        'n_no_conciliables': n_no_conciliables,
        'n_dudosas_importe_o_outcome': datos.get('n_pnl_no_evaluable'),
        'n_binarias_registradas': (int(datos.get('ganadas') or 0) + int(datos.get('perdidas') or 0)
            if 'ganadas' in datos and 'perdidas' in datos else None),
        'motivos': {'SOPORTES_ORIGINALES_NO_DISPONIBLES': n_resueltas} if n_resueltas else {},
        'unidad': None, 'grano': 'APUESTA', 'corte_utc': datetime.now(timezone.utc).isoformat(),
        'importes_individuales': 'REGISTRADOS_NO_CERTIFICADOS',
    }
    return salida
