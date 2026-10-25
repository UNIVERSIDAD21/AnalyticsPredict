"""Cierre explícito e idempotente del registro personal, sin ingesta ni forecasts.

Cada dominio conserva su contrato: NBA final con OT, Euro 40 minutos y fútbol
90 minutos/mitades. Un NULL no es un cero y un calendario no es un resultado.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row

from db import obtener_pool

BOGOTA = ZoneInfo('America/Bogota')


def entero(valor):
    if valor is None or isinstance(valor, bool):
        return None
    try:
        numero = Decimal(str(valor))
        return int(numero) if numero.is_finite() and numero >= 0 and numero == numero.to_integral_value() else None
    except (InvalidOperation, ValueError):
        return None


def valor_futbol(mercado: str, partido: dict) -> int | None:
    """Métrica exacta; nunca completar un lado ausente ni sumar ET a goles FT."""
    partes = mercado.split('_')
    if len(partes) < 2 or partes[-1] not in {'1T', '2T', 'FT'}:
        return None
    periodo = partes[-1]
    lados = ['local'] if 'LOCAL' in partes else ['visitante'] if 'VISITANTE' in partes else ['local', 'visitante']
    familia = partes[0]
    if familia not in {'GOLES', 'CORNERS', 'DISPAROS'}:
        return None
    validos = {familia, periodo, 'LOCAL', 'VISITANTE'} | ({'ARCO'} if familia == 'DISPAROS' else set())
    if set(partes) - validos or ('LOCAL' in partes and 'VISITANTE' in partes):
        return None
    valores = []
    for lado in lados:
        if familia == 'GOLES' and periodo == 'FT':
            mitades = [entero(partido.get(f'{lado}_goles_{p}')) for p in ('1t', '2t')]
            total = entero(partido.get(f'{lado}_goles_total'))
            if all(v is not None for v in mitades):
                valor = sum(mitades)
                et = entero(partido.get(f'{lado}_goles_et'))
                if total is not None and total not in {valor, valor + (et or 0)}:
                    return None
            elif partido.get('hubo_tiempo_extra') is False and entero(partido.get(f'{lado}_goles_et')) in {None, 0}:
                valor = total
            else:
                return None
        else:
            if familia == 'DISPAROS' and periodo != 'FT':
                return None  # El almacén no tiene disparos por mitad.
            if familia in {'CORNERS', 'DISPAROS'} and periodo == 'FT' and partido.get('hubo_tiempo_extra') is not False:
                return None  # No confundir estadísticas 120 min con mercado 90 min.
            metrica = 'disparos_arco' if familia == 'DISPAROS' and 'ARCO' in partes else f"{familia.lower()}_{'total' if periodo == 'FT' else periodo.lower()}"
            valor = entero(partido.get(f'{lado}_{metrica}'))
        if valor is None:
            return None
        valores.append(valor)
    return sum(valores)


def valor_baloncesto(mercado: str, partido: dict, liga: str) -> int | None:
    cuartos = {lado: [entero(partido.get(f'{lado}_q{q}')) for q in range(1, 5)] for lado in ('local', 'visitante')}
    if any(v is None for vs in cuartos.values() for v in vs):
        return None
    totales = {lado: entero(partido.get(f'{lado}_total')) for lado in cuartos}
    for lado in cuartos:
        total, regulacion = totales[lado], sum(cuartos[lado])
        ot = entero(partido.get(f'{lado}_ot'))
        if total is None or total <= 0 or regulacion <= 0 or total != regulacion + (ot or 0):
            return None
    if totales['local'] == totales['visitante'] or not partido.get('ganador_id'):
        return None
    ganador = 'local' if totales['local'] > totales['visitante'] else 'visitante'
    if str(partido.get(f'equipo_{ganador}_id')) != str(partido['ganador_id']):
        return None
    if any((entero(partido.get(f'{lado}_ot')) or 0) > 0 for lado in cuartos) and sum(cuartos['local']) != sum(cuartos['visitante']):
        return None
    if mercado in {'Q1', 'Q2', 'Q3', 'Q4'}:
        return sum(vs[int(mercado[1]) - 1] for vs in cuartos.values())
    if mercado == 'COMPLETO':
        return sum(sum(vs) for vs in cuartos.values()) if liga == 'euroleague' else sum(totales.values())
    return None


def calcular_cierre(apuesta: dict, partido: dict | None, liga: str, *, hoy: date | None = None) -> tuple[dict | None, str | None]:
    if not apuesta.get('partido_id') or not partido:
        return None, 'sin_partido'
    if partido.get('valido') is not True:
        return None, 'partido_no_valido'
    fecha = str(partido.get('fecha_partido') or '')
    try:
        instante = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        dia = instante.astimezone(BOGOTA).date() if instante.tzinfo else instante.date()
    except ValueError:
        return None, 'fecha_no_disponible'
    hoy = hoy or datetime.now(BOGOTA).date()
    if dia > hoy or (instante.tzinfo and hoy == datetime.now(BOGOTA).date() and instante > datetime.now(BOGOTA)):
        return None, 'partido_futuro'
    if liga == 'futbol':
        if partido.get('estado') != 'FINALIZADO':
            return None, 'partido_no_finalizado'
        valor = valor_futbol(apuesta['mercado'], partido)
    elif liga in {'nba', 'euroleague'}:
        if apuesta.get('competicion_id') and str(apuesta['competicion_id']) != str(partido.get('competicion_id')):
            return None, 'competicion_inconsistente'
        valor = valor_baloncesto(apuesta['mercado'], partido, liga)
    else:
        return None, 'competicion_no_soportada'
    if valor is None:
        return None, 'sin_datos_mercado'
    try:
        linea = Decimal(str(apuesta.get('linea')))
        if not linea.is_finite() or linea < 0 or apuesta.get('lado') not in {'OVER', 'UNDER'}:
            return None, 'contrato_apuesta_invalido'
    except InvalidOperation:
        return None, 'contrato_apuesta_invalido'
    if linea * 2 != (linea * 2).to_integral_value():
        return None, 'linea_asiatica_no_soportada'
    resultado = 'PUSH' if valor == linea else 'GANADA' if ((valor > linea) == (apuesta['lado'] == 'OVER')) else 'PERDIDA'
    ganancia = None
    try:
        cuota, stake = (Decimal(str(apuesta.get(k))) for k in ('cuota', 'stake'))
        if cuota.is_finite() and stake.is_finite() and cuota > 1 and stake > 0:
            ganancia = stake * (cuota - 1) if resultado == 'GANADA' else -stake if resultado == 'PERDIDA' else Decimal(0)
            ganancia = ganancia.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        pass  # Outcome verificable aunque la cuota legacy no permita calcular P&L.
    return {'resultado': resultado, 'valor_real': valor, 'ganancia': ganancia}, None


def resolver_bitacora(*, pool=None, deportes=('baloncesto', 'futbol'), limite=1000,
                     mercado=None, hasta=None, partido_id=None, simular=False, solo_liga=None,
                     apuesta_ids=None) -> dict:
    """Solo PENDIENTE, bloqueo por fila, savepoints y conteos tras UPDATE efectivo.

    simular=True no ejecuta DML ni bloqueos. No descarga datos ni altera modelos.
    Las combinadas conservan su resolvedor separado; no hay combinadas Euro.
    """
    resumen = dict(resueltas=0, ganadas=0, perdidas=0, push=0, pendientes=0, errores=0,
                   por_deporte={}, motivos_pendientes={}, detalles_errores=[], importes_no_disponibles=0)
    motivos = Counter()
    with (pool or obtener_pool()).connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for deporte in deportes:
                if deporte not in {'baloncesto', 'futbol'}:
                    raise ValueError('Deporte no soportado')
                tabla = 'apuestas' if deporte == 'baloncesto' else 'apuestas_futbol'
                juegos = 'partidos_baloncesto' if deporte == 'baloncesto' else 'partidos_futbol'
                liga_sql = "COALESCE(cp.codigo, ca.codigo, 'nba')" if deporte == 'baloncesto' else "'futbol'"
                joins = '''LEFT JOIN competiciones_baloncesto cp ON cp.id=p.competicion_id
                           LEFT JOIN competiciones_baloncesto ca ON ca.id=a.competicion_id''' if deporte == 'baloncesto' else ''
                consulta = f'''SELECT to_jsonb(a) apuesta, to_jsonb(p) partido, {liga_sql} liga
                    FROM {tabla} a LEFT JOIN {juegos} p ON p.id=a.partido_id {joins}
                    WHERE a.resultado='PENDIENTE' '''
                params = []
                for condicion, valor in [('a.mercado=%s', mercado), ('p.fecha_partido::date<=%s', hasta), ('a.partido_id=%s', partido_id)]:
                    if valor is not None:
                        consulta += ' AND ' + condicion
                        params.append(valor)
                if solo_liga and deporte == 'baloncesto':
                    # La entrada legacy NBA no puede ni leer selecciones Euro.
                    consulta += f' AND {liga_sql}=%s'
                    params.append(solo_liga)
                if apuesta_ids is not None:
                    consulta += ' AND a.id=ANY(%s::uuid[])'
                    params.append([str(i) for i in apuesta_ids])
                consulta += ' ORDER BY a.fecha_partido NULLS LAST, a.id LIMIT %s'
                params.append(limite)
                if not simular:
                    consulta += ' FOR UPDATE OF a SKIP LOCKED'
                cur.execute(consulta, params)
                filas = cur.fetchall()
                conteo = dict(resueltas=0, pendientes=0, errores=0)
                for fila in filas:
                    cierre, motivo = calcular_cierre(fila['apuesta'], fila['partido'], fila['liga'])
                    if motivo:
                        motivos[motivo] += 1
                        resumen['pendientes'] += 1
                        conteo['pendientes'] += 1
                        continue
                    try:
                        if not simular:
                            with conn.transaction():
                                campo = 'puntos_reales' if deporte == 'baloncesto' else 'valor_real'
                                cur.execute(f'''UPDATE {tabla} SET resultado=%s, {campo}=%s,
                                    ganancia=%s, fecha_resolucion=NOW(), actualizado_en=NOW()
                                    WHERE id=%s AND resultado='PENDIENTE' ''',
                                    (cierre['resultado'], cierre['valor_real'], cierre['ganancia'], fila['apuesta']['id']))
                                if cur.rowcount != 1:
                                    raise RuntimeError('La apuesta cambió durante la resolución')
                        resumen['resueltas'] += 1
                        if cierre['ganancia'] is None:
                            resumen['importes_no_disponibles'] += 1
                        resumen[{'GANADA':'ganadas', 'PERDIDA':'perdidas', 'PUSH':'push'}[cierre['resultado']]] += 1
                        conteo['resueltas'] += 1
                    except Exception:
                        resumen['errores'] += 1
                        conteo['errores'] += 1
                        resumen['detalles_errores'].append(f"No se pudo cerrar {fila['apuesta']['id']}; registro conservado")
                resumen['por_deporte'][deporte] = conteo
    resumen['motivos_pendientes'] = dict(motivos)
    return resumen
