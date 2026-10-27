"""Fuentes públicas de agenda; sin BD, modelos ni efectos por render.

Reutiliza los contratos ESPN existentes. Un feed vacío no acredita publicación
íntegra; los estados y las horas desconocidas permanecen explícitos.
"""
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import json
from zoneinfo import ZoneInfo

from servicios.calendario_wnba import normalizar_evento
from servicios.transporte_agenda import ClienteAgenda, guardar
from scripts.sincronizar_espn_futbol import CODIGOS
from scripts.auditar_fuente_espn_soccer import interpretar_evento

BOGOTA = ZoneInfo('America/Bogota')
FUTBOL = {**CODIGOS, 'usa.1':'USA_MLS', 'arg.1':'ARG_PRIMERA',
          'arg.copa_lpf':'ARG_COPA_LPF', 'arg.copa_de_la_superliga':'ARG_SUPERLIGA',
          'col.1':'COL_PRIMERAA', 'bra.1':'BRA_SERIEA'}
ESTADOS = {'STATUS_SCHEDULED':'PROGRAMADO', 'STATUS_POSTPONED':'POSPUESTO',
           'STATUS_CANCELED':'CANCELADO', 'STATUS_CANCELLED':'CANCELADO',
           'STATUS_DELAYED':'DEMORADO', 'STATUS_SUSPENDED':'SUSPENDIDO',
           'STATUS_ABANDONED':'SUSPENDIDO', 'STATUS_FINAL':'FINALIZADO',
           'STATUS_FULL_TIME':'FINALIZADO', 'STATUS_FINAL_AET':'FINALIZADO',
           'STATUS_FINAL_PEN':'FINALIZADO', 'STATUS_IN_PROGRESS':'EN_VIVO',
           'STATUS_HALFTIME':'EN_VIVO', 'STATUS_END_PERIOD':'EN_VIVO',
           'STATUS_FIRST_HALF':'EN_VIVO', 'STATUS_SECOND_HALF':'EN_VIVO',
           'STATUS_OVERTIME':'EN_VIVO', 'STATUS_SHOOTOUT':'EN_VIVO'}


def meses(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, monthrange(y, m)[1]))


def instante(s):
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Hora sin zona acreditada')
    return d.astimezone(timezone.utc)


def tareas(hoy):
    # La temporada Euroliga empieza en julio; no cambia el 1 de enero.
    year = hoy.year if hoy.month >= 7 else hoy.year - 1
    yield {'grupo':'euroliga', 'periodo':str(year),
           'url':f'https://api-live.euroleague.net/v2/competitions/E/seasons/E{year}/games',
           'params':{'limit':500}, 'ttl':1800}
    for feed, code in FUTBOL.items():
        m = (hoy - timedelta(days=8)).replace(day=1)
        while m <= meses(hoy, 2):
            yield {'grupo':code, 'feed':feed, 'periodo':m.strftime('%Y%m'),
                   'url':f'https://site.api.espn.com/apis/site/v2/sports/soccer/{feed}/scoreboard',
                   'params':{'dates':m.strftime('%Y%m'), 'limit':500},
                   'ttl':1800 if m <= hoy else 21600}
            m = meses(m, 1)
    for code, n in [('nba', 2), ('wnba', 3)]:
        first, last = hoy - timedelta(days=9), meses(hoy, n) + timedelta(days=1)
        for i in range((last-first).days+1):
            d = first + timedelta(days=i)
            yield {'grupo':code, 'periodo':str(d),
                   'url':f'https://site.api.espn.com/apis/site/v2/sports/basketball/{code}/scoreboard',
                   'params':{'dates':d.strftime('%Y%m%d'), 'limit':500},
                   'ttl':900 if d <= hoy else 21600}


def recopilar(cache, salida, hoy=None):
    hoy = hoy or datetime.now(BOGOTA).date()
    client = ClienteAgenda(cache)
    results = []
    for task in tareas(hoy):
        try:
            j, meta = client.json(task['url'], task['params'], ttl=task['ttl'])
            rows = j.get('data') if task['grupo']=='euroliga' else j.get('events')
            if not isinstance(rows, list) or len(rows) >= 500 or (
                    task['grupo']=='euroliga' and j.get('total') != len(rows)):
                raise ValueError('Feed truncado o contrato alterado')
            detalles={}
            if task.get('feed'):
                for ev in rows:
                    st=ev.get('status',{}).get('type',{}).get('name')
                    if st in ('STATUS_FINAL_AET','STATUS_FINAL_PEN'):
                        try:
                            _,dm=client.json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{task['feed']}/summary",
                                {'event':str(ev['id'])},ttl=21600)
                            detalles[str(ev['id'])]=dm
                        except Exception:
                            # El normalizador registra el final sin desglose; no
                            # fabrica regulación ni reemplaza el FT previo.
                            pass
            results.append({**task, 'estado':'OK', 'evidencia':meta,'detalles':detalles})
        except Exception as exc:
            # Diagnóstico sin payloads de credenciales ni cadenas de conexión.
            results.append({**task, 'estado':'ERROR', 'motivo':str(exc), 'tipo':type(exc).__name__})
        guardar(salida, {'fecha_cot':str(hoy), 'resultados':results,
                        'http':client.http, 'cache_hits':client.hits})
    return {'fecha_cot':str(hoy), 'resultados':results,
            'http':client.http, 'cache_hits':client.hits}


def hora_espn(e):
    c = e['competitions'][0]
    raw = e.get('date') or c.get('date')
    if not isinstance(raw, str) or len(raw) < 10:
        raise ValueError('Fecha fuente ausente')
    detail = str(e.get('status', {}).get('type', {}).get('detail', '')).upper()
    conocida = len(raw)>10 and c.get('timeValid') is not False and not any(x in detail for x in ('TBD', 'TBA'))
    return (instante(raw).isoformat() if conocida else None), raw[:10]


def puntos_final(e):
    """Cuatro periodos observados + OT explícito; no infiere ceros de ausencias."""
    cs = e['competitions'][0]['competitors']
    sides = {x['homeAway']:x for x in cs}
    r = {}
    if len(cs)!=2 or set(sides)!={'home','away'}:
        raise ValueError('Localía incompleta')
    for side, label in [('home','local'), ('away','visitante')]:
        c = sides[side]
        scores = c.get('linescores') or []
        if len(scores)<4 or any(x.get('period',i+1)!=i+1 for i,x in enumerate(scores)):
            raise ValueError('Periodos finales ausentes o no consecutivos')
        values = [x.get('value') for x in scores]
        if any(isinstance(x,bool) or not isinstance(x,(int,float)) or x<0 or int(x)!=x for x in values):
            raise ValueError('Puntos finales no observados')
        total = float(c['score'])
        if total<=0 or int(total)!=total or sum(values)!=total:
            raise ValueError('Cuartos/OT/FT incompatibles')
        r.update({f'{label}_q{i+1}':int(v) for i,v in enumerate(values[:4])})
        r[f'{label}_ot'], r[f'{label}_total'] = int(sum(values[4:])), int(total)
    if r['local_total']==r['visitante_total']:
        raise ValueError('Final baloncesto empatado')
    if len(sides['home']['linescores']) != len(sides['away']['linescores']):
        raise ValueError('Prórrogas asimétricas')
    for k in range(4, len(sides['home']['linescores'])):
        if sum(x['value'] for x in sides['home']['linescores'][:k]) != sum(x['value'] for x in sides['away']['linescores'][:k]):
            raise ValueError('Prórroga sin empate anterior')
    r['hubo_overtime'] = len(sides['home']['linescores'])>4
    return r


def espn(e, code, feed, evidencia, hoy, detalle=None):
    c = e['competitions']
    if len(c)!=1 or len(c[0]['competitors'])!=2:
        raise ValueError('Competición/localía ambigua')
    sides = {x['homeAway']:x for x in c[0]['competitors']}
    if set(sides)!={'home','away'}:
        raise ValueError('Localía ambigua')
    st = e.get('status',c[0].get('status',{})).get('type',{})
    estado = ESTADOS[st['name']]
    if (estado=='FINALIZADO') != (st.get('completed') is True):
        raise ValueError('Estado final contradictorio')
    inicio, fecha = hora_espn(e)
    dia = instante(inicio).astimezone(BOGOTA).date() if inicio else date.fromisoformat(fecha)
    if not hoy-timedelta(days=8) <= dia <= meses(hoy, 3 if code=='wnba' else 2):
        return None
    r = {'deporte':'baloncesto' if code in ('nba','wnba') else 'futbol',
         'codigo':code, 'feed':feed, 'proveedor':'ESPN', 'id_fuente':str(e['id']),
         'inicio_utc':inicio, 'fecha_fuente':fecha, 'zona_origen':'UTC' if inicio else 'DIA_FUENTE_SIN_ZONA',
         'precision_fecha':'HORA' if inicio else 'DIA', 'estado':estado,
         'local_fuente':str(sides['home']['team']['id']),
         'visitante_fuente':str(sides['away']['team']['id']),
         'local_nombre':sides['home']['team']['displayName'],
         'visitante_nombre':sides['away']['team']['displayName'],
         'anio':e.get('season',{}).get('year'), 'evidencia':evidencia, 'resultados':{}}
    if r['local_fuente']==r['visitante_fuente']:
        raise ValueError('Equipo repetido')
    if code in ('nba','wnba'):
        r['fase'] = {1:'PRE',2:'REG',3:'POST'}[e['season']['type']]
        if code=='wnba':
            r['fixture_wnba'] = normalizar_evento(e, hoy-timedelta(days=8), meses(hoy,3))
            r['fase'] = r['fixture_wnba']['fase']
        if estado=='FINALIZADO':
            if not inicio or instante(inicio)>instante(evidencia['observado_en']):
                raise ValueError('Final futuro/no acreditado')
            r['resultados'] = puntos_final(e)
    else:
        if estado=='FINALIZADO':
            if not inicio or instante(inicio)>instante(evidencia['observado_en']):
                raise ValueError('Final futuro/no acreditado')
            parsed = interpretar_evento(e, feed)
            # Una tanda/ET requiere su summary explícito antes de tocar FT.
            r['resultados'] = {l+'_goles_total':parsed[l+'_goles'] for l in ('local','visitante')}
            if st['name'] in ('STATUS_FINAL_AET','STATUS_FINAL_PEN'):
                if detalle is None:
                    raise ValueError('Final ET/tanda: requiere desglose explícito; conservado para revisión')
                from servicios.finales_espn_futbol import interpretar_periodos_final
                from pathlib import Path
                import hashlib
                raw=Path(detalle['archivo']).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=detalle['sha256']:
                    raise ValueError('Summary de ET/tanda alterado')
                p=interpretar_periodos_final(json.loads(raw),parsed)
                r['resultados'].update(p['campos'])
                r['evidencia']={**evidencia,'detalle':detalle}
            else:
                r['resultados'].update(hubo_tiempo_extra=False,hubo_penales=False)
    return r


def euro(e, evidencia, hoy):
    if e['season']['competitionCode']!='E' or e['identifier']!=f"{e['season']['code']}_{e['gameCode']}":
        raise ValueError('Identidad Euroliga incompatible')
    fecha = e['date'][:10]
    inicio = instante(e['utcDate']).isoformat() if e['confirmedDate'] is True and e['confirmedHour'] is True else None
    if inicio:
        local = datetime.fromisoformat(e['localDate'])
        offset = (local - instante(inicio).replace(tzinfo=None)).total_seconds()/3600
        if offset != e['localTimeZone']:
            raise ValueError('UTC/hora local oficial contradictorios')
    dia = instante(inicio).astimezone(BOGOTA).date() if inicio else date.fromisoformat(fecha)
    if not hoy-timedelta(days=8) <= dia <= meses(hoy,2):
        return None
    estados = {'Confirmed':'PROGRAMADO','Postponed':'POSPUESTO', 'Cancelled':'CANCELADO',
               'Canceled':'CANCELADO','Suspended':'SUSPENDIDO','InProgress':'EN_VIVO'}
    estado = 'FINALIZADO' if e['played'] is True else estados[e['gameStatus']]
    r = {'deporte':'baloncesto','codigo':'euroleague','proveedor':'EUROLEAGUE_OFFICIAL',
         'id_fuente':e['identifier'],'anio':e['season']['year'],
         'fase':{'RS':'REG','PO':'POST','FF':'POST','PI':'POST'}[e['phaseType']['code']],
         'local_fuente':e['local']['club']['code'],'visitante_fuente':e['road']['club']['code'],
         'local_nombre':e['local']['club']['name'],'visitante_nombre':e['road']['club']['name'],
         'inicio_utc':inicio,'fecha_fuente':fecha,'precision_fecha':'HORA' if inicio else 'DIA',
         'zona_origen':f"UTC{e['localTimeZone']:+g}", 'estado':estado,'evidencia':evidencia,'resultados':{}}
    if estado=='FINALIZADO':
        if not inicio or instante(inicio)>instante(evidencia['observado_en']):
            raise ValueError('Final oficial futuro/no acreditado')
        fake = {'competitions':[{'competitors':[]} ]}
        for side, key in [('home','local'),('away','road')]:
            part = e[key]['partials']; extra = part.get('extraPeriods') or {}
            values = [part[f'partials{i}'] for i in range(1,5)]
            if not isinstance(extra,dict) or set(extra)!={str(i+1) for i in range(len(extra))}:
                raise ValueError('OT oficial sin periodos consecutivos')
            values.extend(extra[str(i+1)] for i in range(len(extra)))
            fake['competitions'][0]['competitors'].append({'homeAway':side,'score':e[key]['score'],
                 'linescores':[{'value':v,'period':i+1} for i,v in enumerate(values)]})
        r['resultados'] = puntos_final(fake)
    return r


def normalizar(reporte, hoy):
    """Replay verificable sin HTTP. Revisa hash y deduplica revisiones iguales."""
    import hashlib
    from pathlib import Path
    registros, incidencias, fuentes, conflictivos = {}, [], [], set()
    for task in reporte['resultados']:
        if task['estado']!='OK':
            incidencias.append({k:v for k,v in task.items() if k!='evidencia'})
            continue
        meta = task['evidencia']
        raw = Path(meta['archivo']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=meta['sha256']:
            raise ValueError('Snapshot fuente alterado')
        j = json.loads(raw)
        rows = j.get('data') if task['grupo']=='euroliga' else j.get('events')
        if not isinstance(rows,list) or len(rows)>=500 or (task['grupo']=='euroliga' and j.get('total')!=len(rows)):
            raise ValueError('Snapshot truncado')
        fuentes.append({'grupo':task['grupo'],'periodo':task['periodo'],**meta,'eventos':len(rows)})
        for e in rows:
            try:
                feed = task.get('feed') or next((f for f,c in FUTBOL.items() if c==task['grupo']), task['grupo'])
                r = euro(e,meta,hoy) if task['grupo']=='euroliga' else espn(e,task['grupo'],feed,meta,hoy,task.get('detalles',{}).get(str(e.get('id'))))
                if r is None:
                    continue
                key = (r['codigo'],r['id_fuente'])
                if key in conflictivos:
                    continue
                if key in registros:
                    prev = {k:v for k,v in registros[key].items() if k!='evidencia'}
                    if prev != {k:v for k,v in r.items() if k!='evidencia'}:
                        # No escoger arbitrariamente una revisión entre feeds de día.
                        conflictivos.add(key)
                        raise ValueError('Revisiones contradictorias del mismo evento')
                registros[key] = r
            except (ValueError,KeyError,TypeError) as exc:
                incidencias.append({'grupo':task['grupo'],'id':e.get('id',e.get('identifier')),'motivo':str(exc)})
                if 'key' in locals() and key in registros and str(e.get('id',e.get('identifier')))==key[1]:
                    registros.pop(key,None)
    return list(registros.values()), incidencias, fuentes
