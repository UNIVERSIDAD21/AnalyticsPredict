"""Periodos explícitos de un final ESPN, con prórroga y penales separados."""
from __future__ import annotations

from scripts.auditar_fuente_espn_soccer import (
    FuenteNoDisponible, _entero_no_negativo, _instante_utc,
)

ESTADOS_FINALES = {'STATUS_FULL_TIME', 'STATUS_FINAL', 'STATUS_FINAL_AET', 'STATUS_FINAL_PEN'}
CAMPOS_PERIODOS = (
    'local_goles_1t', 'local_goles_2t', 'local_goles_et',
    'visitante_goles_1t', 'visitante_goles_2t', 'visitante_goles_et',
    'local_penales', 'visitante_penales', 'hubo_penales', 'hubo_tiempo_extra',
)


def interpretar_desempate_final(payload: dict, esperado: dict) -> dict:
    """La tanda se valida aparte: una vuelta puede no terminar empatada."""
    header=payload.get('header') or {}
    partidos=header.get('competitions') or []
    if str(header.get('id'))!=esperado['id_fuente'] or len(partidos)!=1:
        raise FuenteNoDisponible('Identidad de tanda no acreditada')
    partido=partidos[0];estado=(partido.get('status') or {}).get('type') or {}
    if (str(partido.get('id'))!=esperado['id_fuente']
            or _instante_utc(partido.get('date'))!=_instante_utc(esperado['inicio_utc'])
            or estado.get('name')!='STATUS_FINAL_PEN' or estado.get('completed') is not True):
        raise FuenteNoDisponible('Estado de tanda no acreditado')
    participantes=partido.get('competitors') or []
    lados={x.get('homeAway'):x for x in participantes}
    if len(participantes)!=2 or set(lados)!={'home','away'}:
        raise FuenteNoDisponible('Localía de tanda ambigua')
    campos={'hubo_penales':True};agregado=None
    for lado,etiqueta in [('home','local'),('away','visitante')]:
        item=lados[lado];tanda=item.get('shootoutScore')
        if (str((item.get('team') or {}).get('id'))!=esperado[etiqueta+'_id_fuente']
                or _entero_no_negativo(item.get('score'))!=esperado[etiqueta+'_goles']
                or isinstance(tanda,bool) or not isinstance(tanda,(int,float))
                or tanda<0 or int(tanda)!=tanda):
            raise FuenteNoDisponible('Identidad, FT o goles de tanda contradictorios')
        campos[etiqueta+'_penales']=int(tanda)
    series=partido.get('series') or []
    if series:
        if len(series)!=1 or series[0].get('completed') is not True or series[0].get('leg')!=2 or series[0].get('totalCompetitions')!=2:
            raise FuenteNoDisponible('Desempate agregado sin dos vueltas acreditadas')
        participantes_serie=series[0].get('competitors') or []
        por_id={str(x.get('id')):x for x in participantes_serie}
        if len(participantes_serie)!=2 or set(por_id)!={esperado['local_id_fuente'],esperado['visitante_id_fuente']}:
            raise FuenteNoDisponible('Identidad de serie contradictoria')
        agregado={}
        for etiqueta in ('local','visitante'):
            valor=por_id[esperado[etiqueta+'_id_fuente']].get('aggregateScore')
            if isinstance(valor,bool) or not isinstance(valor,(int,float)) or valor<0 or int(valor)!=valor:
                raise FuenteNoDisponible('Marcador agregado no acreditado')
            agregado[etiqueta]=int(valor)
        ganadores=[etiqueta for etiqueta in ('local','visitante')
                   if por_id[esperado[etiqueta+'_id_fuente']].get('winner') is True]
    else:
        ganadores=[etiqueta for lado,etiqueta in [('home','local'),('away','visitante')]
                   if lados[lado].get('winner') is True]
    ganador='local' if campos['local_penales']>campos['visitante_penales'] else 'visitante'
    if ganadores!=[ganador]:
        raise FuenteNoDisponible('Ganador de tanda contradictorio')
    salida={'contrato':'ESPN_EXPLICIT_SHOOTOUT_WITH_AGGREGATE_V1','campos':campos,
            'ganador_tanda':ganador,'agregado':agregado}
    try:
        validar_desempate_final(salida,esperado)
    except ValueError as exc:
        raise FuenteNoDisponible(str(exc)) from exc
    return salida


def validar_desempate_final(tanda,evento):
    campos=tanda.get('campos') or {}
    if (tanda.get('contrato')!='ESPN_EXPLICIT_SHOOTOUT_WITH_AGGREGATE_V1'
            or evento.get('estado_fuente')!='STATUS_FINAL_PEN'
            or set(campos)!={'local_penales','visitante_penales','hubo_penales'}
            or campos.get('hubo_penales') is not True):
        raise ValueError('Contrato de tanda no admitido')
    a,b=campos['local_penales'],campos['visitante_penales']
    if type(a) is not int or type(b) is not int or min(a,b)<0 or a==b:
        raise ValueError('Tanda sin ganador numérico')
    agregado=tanda.get('agregado')
    if agregado is not None and (set(agregado)!={'local','visitante'}
            or any(type(x) is not int or x<0 for x in agregado.values())
            or agregado['local']!=agregado['visitante']):
        raise ValueError('Agregado no empatado')
    if evento['local_goles']!=evento['visitante_goles'] and agregado is None:
        raise ValueError('Tanda con FT desigual sin empate agregado acreditado')
    if tanda.get('ganador_tanda')!=('local' if a>b else 'visitante'):
        raise ValueError('Ganador de tanda incompatible')


def interpretar_periodos_final(payload: dict, esperado: dict) -> dict:
    """Nunca resta HT desde FT ni suma una tanda al marcador del partido."""
    header = payload.get('header') or {}
    partidos = header.get('competitions') or []
    formato = (payload.get('format') or {}).get('regulation') or {}
    if (str(header.get('id')) != esperado['id_fuente'] or len(partidos) != 1
            or formato.get('periods') != 2 or formato.get('slug') != 'half'):
        raise FuenteNoDisponible('Identidad o formato de final no acreditados')
    partido = partidos[0]
    estado = (partido.get('status') or {}).get('type') or {}
    if (str(partido.get('id')) != esperado['id_fuente']
            or _instante_utc(partido.get('date')) != _instante_utc(esperado['inicio_utc'])
            or estado.get('completed') is not True
            or estado.get('name') not in ESTADOS_FINALES
            or estado.get('name') != esperado['estado_fuente']):
        raise FuenteNoDisponible('Evento, inicio o estado contradictorio')
    participantes = partido.get('competitors') or []
    lados = {x.get('homeAway'): x for x in participantes}
    if len(participantes) != 2 or set(lados) != {'home', 'away'}:
        raise FuenteNoDisponible('Localía incompleta o ambigua')
    penales = estado['name'] == 'STATUS_FINAL_PEN'
    aet = estado['name'] == 'STATUS_FINAL_AET'
    desempate=interpretar_desempate_final(payload,esperado) if penales else None
    campos = {}
    longitudes = set()
    for lado, etiqueta in (('home', 'local'), ('away', 'visitante')):
        item = lados[lado]
        if str((item.get('team') or {}).get('id')) != esperado[etiqueta + '_id_fuente']:
            raise FuenteNoDisponible('Equipo de otro partido')
        ft = _entero_no_negativo(item.get('score'))
        if ft is None or ft != esperado[etiqueta + '_goles']:
            raise FuenteNoDisponible('Marcador distinto del scoreboard')
        lineas = item.get('linescores') or []
        permitidas = {3, 5} if penales else {4} if aet else {2}
        if len(lineas) not in permitidas:
            raise FuenteNoDisponible('Periodos ausentes o no acreditados')
        longitudes.add(len(lineas))
        valores = []
        for numero, linea in enumerate(lineas, 1):
            periodo = linea.get('period', numero)
            if isinstance(periodo, dict):
                periodo = periodo.get('number')
            valor = _entero_no_negativo(linea.get('displayValue'))
            if periodo != numero or valor is None:
                raise FuenteNoDisponible('Orden o valor de periodos incompatible')
            valores.append(valor)
        extra = sum(valores[2:-1] if penales else valores[2:])
        if valores[0] + valores[1] + extra != ft:
            raise FuenteNoDisponible('Mitades y prórroga no concilian con FT')
        campos.update({etiqueta + '_goles_1t': valores[0], etiqueta + '_goles_2t': valores[1],
                       etiqueta + '_goles_et': extra, etiqueta + '_penales': None})
        if penales:
            tanda = item.get('shootoutScore')
            if (isinstance(tanda, bool) or not isinstance(tanda, (int, float))
                    or tanda < 0 or int(tanda) != tanda or int(tanda) != valores[-1]):
                raise FuenteNoDisponible('Tanda de penales no conciliada')
            campos[etiqueta + '_penales'] = int(tanda)
    if len(longitudes) != 1:
        raise FuenteNoDisponible('Periodos incompatibles entre equipos')
    campos.update(hubo_penales=penales, hubo_tiempo_extra=next(iter(longitudes)) in (4, 5))
    # Mantener la semántica canónica: ganador del marcador del partido, no el
    # clasificado de la eliminatoria. La tanda se conserva en campos separados.
    ganador = ('local' if esperado['local_goles'] > esperado['visitante_goles'] else
               'visitante' if esperado['visitante_goles'] > esperado['local_goles'] else None)
    salida = {'contrato': 'ESPN_EXPLICIT_HALVES_ET_PEN_V1', 'campos': campos, 'ganador': ganador,
              'ganador_tanda':desempate['ganador_tanda'] if desempate else None,
              'agregado':desempate['agregado'] if desempate else None}
    try:
        validar_periodos_final(salida, esperado)
    except ValueError as exc:
        raise FuenteNoDisponible(str(exc)) from exc
    return salida


def validar_periodos_final(periodos: dict, evento: dict) -> None:
    if periodos.get('contrato') != 'ESPN_EXPLICIT_HALVES_ET_PEN_V1':
        raise ValueError('Contrato de periodos no admitido')
    campos = periodos.get('campos') or {}
    if set(campos) != set(CAMPOS_PERIODOS):
        raise ValueError('Campos de periodos incompletos')
    for lado in ('local', 'visitante'):
        goles = [campos[lado + '_goles_' + p] for p in ('1t', '2t', 'et')]
        if any(type(x) is not int or x < 0 for x in goles) or sum(goles) != evento[lado + '_goles']:
            raise ValueError('Periodos y FT contradictorios')
    if type(campos['hubo_penales']) is not bool or type(campos['hubo_tiempo_extra']) is not bool:
        raise ValueError('Flags de periodos ambiguos')
    estado=evento.get('estado_fuente')
    if (campos['hubo_penales'] != (estado=='STATUS_FINAL_PEN')
            or estado=='STATUS_FINAL_AET' and not campos['hubo_tiempo_extra']
            or estado in {'STATUS_FULL_TIME','STATUS_FINAL'} and campos['hubo_tiempo_extra']):
        raise ValueError('Estado y periodos contradictorios')
    if campos['hubo_penales']:
        a, b = campos['local_penales'], campos['visitante_penales']
        validar_desempate_final({'contrato':'ESPN_EXPLICIT_SHOOTOUT_WITH_AGGREGATE_V1',
            'campos':{'local_penales':a,'visitante_penales':b,'hubo_penales':True},
            'ganador_tanda':periodos.get('ganador_tanda'),'agregado':periodos.get('agregado')},evento)
    elif campos['local_penales'] is not None or campos['visitante_penales'] is not None:
        raise ValueError('Penales presentes sin tanda')
    if periodos.get('ganador') != ('local' if evento['local_goles']>evento['visitante_goles'] else
                                  'visitante' if evento['visitante_goles']>evento['local_goles'] else None):
        raise ValueError('Ganador y FT contradictorios')
    if not campos['hubo_tiempo_extra'] and any(campos[l + '_goles_et'] for l in ('local', 'visitante')):
        raise ValueError('Goles ET sin prórroga')
