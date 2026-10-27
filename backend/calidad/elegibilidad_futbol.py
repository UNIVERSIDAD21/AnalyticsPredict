"""Elegibilidad de observaciones por objetivo; sin red, BD, imputación ni fitting."""
from collections import Counter
from datetime import datetime
from math import isfinite
from numbers import Number
from typing import NamedTuple

POLITICA = 'futbol-elegibilidad-por-objetivo-v1'
METRICAS = {
    'goles_ft': ('local_goles_total', 'visitante_goles_total'),
    'goles_1t': ('local_goles_1t', 'visitante_goles_1t'),
    'goles_2t': ('local_goles_2t', 'visitante_goles_2t'),
    'corners_ft': ('local_corners_total', 'visitante_corners_total'),
    'corners_1t': ('local_corners_1t', 'visitante_corners_1t'),
    'corners_2t': ('local_corners_2t', 'visitante_corners_2t'),
    'disparos_ft': ('local_disparos_total', 'visitante_disparos_total'),
    'disparos_arco_ft': ('local_disparos_arco', 'visitante_disparos_arco'),
}
DERIVADAS = ('disparos_1t', 'disparos_2t', 'disparos_arco_1t', 'disparos_arco_2t')
MINIMOS_CONTEXTO = {'h2h': 5, 'local_home': 25, 'visitante_away': 25}


class Dato(NamedTuple):
    estado: str
    valor: float | None
    motivo: str | None = None


def numero(valor):
    if isinstance(valor, bool) or not isinstance(valor, Number):
        return None
    try:
        valor = float(valor)
        return valor if isfinite(valor) and valor >= 0 and valor.is_integer() else None
    except (TypeError, ValueError, OverflowError):
        return None


def configurar_mercado(mercado):
    partes = str(mercado).upper().split('_')
    base = 'corners' if partes[0] == 'CORNERS' else 'goles' if partes[0] == 'GOLES' else 'disparos_arco' if 'ARCO' in partes else 'disparos'
    periodo = partes[-1].lower()
    alcance = 'local' if 'LOCAL' in partes else 'visitante' if 'VISITANTE' in partes else 'total'
    return {'base': base, 'periodo': periodo, 'alcance': alcance, 'metric_key': f'{base}_{periodo}'}


def clasificar(partido, metrica, lado):
    """Clasifica un lado. El FT de goles es regulación, ET/penales separados."""
    if ('valido' in partido and partido['valido'] is not True) or ('estado' in partido and partido['estado'] != 'FINALIZADO'):
        return Dato('INVALIDO', None, 'PARTIDO_NO_VALIDO_FINAL')
    if partido.get('identidad_conflictiva') is True:
        return Dato('INVALIDO', None, 'IDENTIDAD_CONFLICTIVA')
    if metrica in DERIVADAS:
        base = metrica.rsplit('_', 1)[0] + '_ft'
        soporte = clasificar(partido, base, lado)
        return Dato('ESTIMADO', None, 'REPARTO_HEURISTICO_DESDE_FT') if soporte.estado == 'OBSERVADO' else soporte
    columnas = METRICAS.get(metrica)
    if not columnas or lado not in ('local', 'visitante'):
        return Dato('AUSENTE', None, 'OBJETIVO_NO_REPRESENTADO')
    bruto = partido.get(columnas[0 if lado == 'local' else 1])
    if bruto is None:
        return Dato('AUSENTE', None, 'CAMPO_NULL')
    valor = numero(bruto)
    if valor is None:
        return Dato('INVALIDO', None, 'VALOR_NO_ENTERO_NO_NEGATIVO_FINITO')
    base, periodo = metrica.rsplit('_', 1)
    et = partido.get('hubo_tiempo_extra', False)
    if periodo == 'ft' and et is None:
        return Dato('AUSENTE', None, 'REGULACION_NO_ACREDITADA')
    if periodo == 'ft' and et:
        if base != 'goles':
            return Dato('AUSENTE', None, 'FT_CON_ET_SIN_DESGLOSE_ESTADISTICO')
        extra = numero(partido.get(f'{lado}_goles_et'))
        if extra is None:
            return Dato('AUSENTE', None, 'GOLES_ET_NO_ACREDITADOS')
        valor -= extra
        if valor < 0:
            return Dato('INVALIDO', None, 'ET_MAYOR_FT')
    if base in ('goles', 'corners') and periodo in ('1t', '2t'):
        total = numero(partido.get(f'{lado}_{base}_total'))
        otro = numero(partido.get(f'{lado}_{base}_{"2t" if periodo == "1t" else "1t"}'))
        if base == 'goles' and et and total is not None:
            extra = numero(partido.get(f'{lado}_goles_et'))
            total = total-extra if extra is not None else None
        # Un FT desconocido no se inventa; el parcial observado sigue independiente.
        if total is not None and (not et or base == 'goles'):
            if valor > total or (otro is not None and valor+otro != total):
                return Dato('INVALIDO', None, 'PERIODOS_NO_CONCILIAN')
    if base == 'disparos_arco':
        tiros = numero(partido.get(f'{lado}_disparos_total'))
        if tiros is not None and valor > tiros:
            return Dato('INVALIDO', None, 'ARCO_MAYOR_DISPAROS')
    return Dato('OBSERVADO', valor)


def seleccionar(partido, metrica, alcance='total', equipo_id=None):
    if equipo_id is not None:
        if str(partido.get('equipo_local_id')) == str(equipo_id):
            alcance = 'local'
        elif str(partido.get('equipo_visitante_id')) == str(equipo_id):
            alcance = 'visitante'
        else:
            return Dato('INVALIDO', None, 'EQUIPO_AJENO')
    if alcance != 'total':
        return clasificar(partido, metrica, alcance)
    lados = [clasificar(partido, metrica, lado) for lado in ('local', 'visitante')]
    for estado in ('INVALIDO', 'AUSENTE', 'ESTIMADO'):
        if any(d.estado == estado for d in lados):
            d = next(d for d in lados if d.estado == estado)
            return Dato(estado, None, d.motivo)
    return Dato('OBSERVADO', sum(d.valor for d in lados))


def muestra(partidos, metrica, alcance='total', equipo_id=None):
    resumen = {'denominador': 0, 'observados': 0, 'estimados': 0, 'ausentes': 0, 'invalidos': 0,
               'ceros': 0, 'utilizables': 0, 'motivos': {}, 'fecha_min': None, 'fecha_max': None}
    motivos = Counter()
    for p in partidos:
        d = seleccionar(p, metrica, alcance, equipo_id)
        resumen['denominador'] += 1
        resumen[{'OBSERVADO':'observados', 'ESTIMADO':'estimados', 'AUSENTE':'ausentes', 'INVALIDO':'invalidos'}[d.estado]] += 1
        if d.motivo:
            motivos[d.motivo] += 1
        if d.estado in ('OBSERVADO', 'ESTIMADO'):
            resumen['utilizables'] += 1
            if d.valor == 0:
                resumen['ceros'] += 1
            fecha = p.get('fecha_partido')
            if isinstance(fecha, datetime):
                fecha = fecha.isoformat()
            if fecha is not None:
                resumen['fecha_min'] = min(resumen['fecha_min'] or str(fecha), str(fecha))
                resumen['fecha_max'] = max(resumen['fecha_max'] or str(fecha), str(fecha))
    resumen['motivos'] = dict(motivos)
    return resumen


def evaluar_mercado(mercado, conjuntos, local_id, visitante_id, minimos=None):
    config = configurar_mercado(mercado)
    metrica, alcance = config['metric_key'], config['alcance']
    bloques = {}
    for nombre, filas in conjuntos.items():
        equipo = local_id if nombre.startswith('local_') else visitante_id if nombre.startswith('visitante_') else local_id if nombre == 'h2h' and alcance == 'local' else visitante_id if nombre == 'h2h' and alcance == 'visitante' else None
        bloques[nombre] = muestra(filas, metrica, equipo_id=equipo)
    lados = ('local', 'visitante') if alcance == 'total' else (alcance,)
    calculable = all(bloques.get(f'{lado}_global', {}).get('utilizables', 0) > 0 for lado in lados)
    configurados = minimos or MINIMOS_CONTEXTO
    minimos = {k: configurados.get(k, configurados.get(k+'_objetivo', v)) for k,v in MINIMOS_CONTEXTO.items()}
    relevantes = ['h2h', *[f'{lado}_{"home" if lado == "local" else "away"}' for lado in lados]]
    insuficientes = [b for b in relevantes if bloques.get(b, {}).get('utilizables', 0) < minimos[b]]
    estimado = metrica in DERIVADAS
    return {'politica': POLITICA, 'mercado': mercado, 'metrica': metrica, 'alcance': alcance,
            'estado': 'SIN_DATOS' if not calculable else 'ESTIMADO' if estimado else 'MUESTRA_LIMITADA' if insuficientes else 'OBSERVADO',
            'calculable': calculable, 'naturaleza': 'ESTIMADO' if estimado else 'OBSERVADO',
            'muestras': bloques, 'minimos_contexto': minimos, 'bloques_insuficientes': insuficientes,
            'identidad': 'CODIGO_GUARDADO_NO_RECERTIFICADO',
            'advertencias': (['Estadística por mitad estimada desde FT; no hay observaciones de ese periodo.'] if estimado else [])
                            + (['Muestra contextual limitada; los mínimos son avisos, no certificación.'] if insuficientes else [])
                            + ([] if calculable else ['No hay observaciones utilizables para todos los equipos requeridos.'])}
