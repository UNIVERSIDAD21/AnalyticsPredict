"""Contrato puro de outcomes analíticos; sin apuestas, BD ni imputación.

Resolver correctamente un valor no acredita que el pronóstico fuera prospectivo.
La emisión y el resultado se conservan como evidencias separadas.
"""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re

from calidad.elegibilidad_futbol import configurar_mercado, seleccionar
from motor.resolucion_bitacora import entero

POLITICA = 'resolucion-analitica-por-objetivo-v1'


def objeto(valor):
    if isinstance(valor, dict):
        return valor
    try:
        r = json.loads(valor) if isinstance(valor, str) else None
        return r if isinstance(r, dict) else {}
    except (ValueError, TypeError):
        return {}


def instante(valor):
    try:
        d = valor if isinstance(valor, datetime) else datetime.fromisoformat(str(valor).replace('Z', '+00:00'))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError, TypeError):
        return None


def valor_futbol(mercado, partido):
    mercado = str(getattr(mercado, 'value', mercado)).upper()
    patron = r'(?:GOLES|CORNERS)(?:_(?:LOCAL|VISITANTE))?_(?:FT|1T|2T)|DISPAROS(?:_(?:LOCAL|VISITANTE))?(?:_ARCO)?_(?:FT|1T|2T)'
    if not re.fullmatch(patron, mercado):
        return None, 'MERCADO_NO_SOPORTADO'
    config = configurar_mercado(mercado)
    # Ausencia del indicador ET no demuestra que el total represente 90 min.
    partido = {**partido, 'hubo_tiempo_extra': partido.get('hubo_tiempo_extra')}
    d = seleccionar(partido, config['metric_key'], config['alcance'])
    if d.estado != 'OBSERVADO':
        return None, 'OBJETIVO_ESTIMADO_SIN_OBSERVACION' if d.estado == 'ESTIMADO' else d.motivo
    return int(d.valor), None


def valor_basket(mercado, partido, liga, incluye_ot=None):
    if mercado not in {'Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'}:
        return None, 'MERCADO_NO_SOPORTADO'
    totales = {l: entero(partido.get(l+'_total')) for l in ('local', 'visitante')}
    if any(v is None or v <= 0 for v in totales.values()) or totales['local'] == totales['visitante']:
        return None, 'FINAL_NO_ACREDITADO'
    ganador = 'local' if totales['local'] > totales['visitante'] else 'visitante'
    if partido.get('ganador_id') and str(partido['ganador_id']) != str(partido.get('equipo_'+ganador+'_id')):
        return None, 'GANADOR_INCONSISTENTE'
    cuartos = {l: [entero(partido.get(f'{l}_q{q}')) for q in range(1, 5)] for l in totales}
    for l, qs in cuartos.items():
        if any(v is not None and v > totales[l] for v in qs):
            return None, 'PERIODO_MAYOR_FT'
        if all(v is not None for v in qs):
            ot = entero(partido.get(l+'_ot'))
            if sum(qs) > totales[l] or (partido.get(l+'_ot') is not None and (ot is None or sum(qs)+ot != totales[l])):
                return None, 'PERIODOS_NO_CONCILIAN'
    if all(v is not None for qs in cuartos.values() for v in qs):
        extra = any(totales[l] > sum(cuartos[l]) for l in totales)
        if extra and sum(cuartos['local']) != sum(cuartos['visitante']):
            return None, 'OT_SIN_EMPATE_REGULACION'
    if mercado != 'COMPLETO':
        valores = [qs[int(mercado[1])-1] for qs in cuartos.values()]
    elif liga == 'nba' or (liga == 'wnba' and incluye_ot is True):
        valores = list(totales.values())
    elif liga == 'euroleague' or (liga == 'wnba' and incluye_ot is False):
        valores = [v for qs in cuartos.values() for v in qs]
    else:
        return None, 'CONTRATO_OT_NO_ACREDITADO'
    if any(v is None for v in valores):
        return None, 'CAMPO_NULL_O_INVALIDO'
    return sum(valores), None


def comparar(valor, linea):
    try:
        if isinstance(linea, bool):
            raise ValueError
        n = Decimal(str(linea))
        if not n.is_finite() or n < 0:
            raise ValueError
        if n*2 != (n*2).to_integral_value():
            return None, 'LINEA_ASIATICA_NO_SOPORTADA'
    except (InvalidOperation, ValueError, TypeError):
        return None, 'LINEA_INVALIDA'
    return ('PUSH' if valor == n else 'OVER' if valor > n else 'UNDER'), None


def evaluar(registro, partido, liga, ahora=None):
    """Diagnóstico determinista, sin modificar los argumentos ni históricos."""
    ahora = ahora or datetime.now(timezone.utc)
    if not partido:
        return None, 'SIN_PARTIDO'
    if str(registro.get('partido_id')) != str(partido.get('id')):
        return None, 'PARTIDO_INCONSISTENTE'
    if partido.get('valido') is not True:
        return None, 'PARTIDO_NO_VALIDO'
    fecha = partido.get('fecha_partido')
    dt = instante(fecha)
    try:
        dia = fecha if type(fecha) is date else date.fromisoformat(str(fecha)[:10])
    except (ValueError, TypeError):
        return None, 'FECHA_NO_ACREDITADA'
    if (dt and dt > ahora) or dia > ahora.date():
        return None, 'PARTIDO_FUTURO'
    payload = objeto(registro.get('payload'))
    fuente = payload.get('fuente')
    if liga == 'futbol':
        if registro.get('deporte') != 'futbol':
            return None, 'DOMINIO_INCONSISTENTE'
        if partido.get('estado') != 'FINALIZADO':
            return None, 'PARTIDO_NO_FINALIZADO'
        valor, motivo = valor_futbol(registro.get('mercado'), partido)
    elif liga in {'nba', 'wnba', 'euroleague'}:
        if registro.get('deporte') != 'baloncesto' or (fuente == 'analisis_nba' and liga != 'nba'):
            return None, 'DOMINIO_INCONSISTENTE'
        contrato = objeto(payload.get('seguimiento_analitico'))
        declarada = contrato.get('liga')
        if declarada and declarada != liga:
            return None, 'DOMINIO_INCONSISTENTE'
        if liga != 'nba' and declarada != liga:
            return None, 'DOMINIO_NO_ACREDITADO'
        valor, motivo = valor_basket(registro.get('mercado'), partido, liga, contrato.get('incluye_ot'))
    else:
        return None, 'DOMINIO_NO_ACREDITADO'
    if motivo:
        return None, motivo
    lado = str(getattr(registro.get('lado'), 'value', registro.get('lado'))).upper()
    if lado not in {'OVER', 'UNDER'}:
        return None, 'SIN_OBJETIVO_OVER_UNDER'
    relacion, motivo = comparar(valor, registro.get('linea'))
    if motivo:
        return None, motivo
    resultado = 'PUSH' if relacion == 'PUSH' else 'GANADA' if lado == relacion else 'PERDIDA'
    return {'politica': POLITICA, 'valor_real': valor, 'resultado_outcome': resultado,
            'relacion_linea': relacion, 'mercado': registro['mercado'], 'liga': liga,
            'lado': lado, 'linea': str(registro['linea']), 'partido_id': str(partido['id']),
            'partido_sha256': sha256(json.dumps(partido, sort_keys=True, default=str, allow_nan=False).encode()).hexdigest(),
            'resuelto_utc': ahora.isoformat(), 'prospectiva_certificada': False,
            'limitacion': 'Outcome observado; no acredita anterioridad, disponibilidad original ni calibración.'}, None
