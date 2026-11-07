"""Agenda acotada y verificable: HTTP compartido, sin SQL ni selección de modelos."""
from __future__ import annotations

from collections import deque
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

from servicios.fuentes_agenda import BOGOTA, FUTBOL, espn, euro, instante, meses, hora_espn
from servicios.sincronizacion_agendas import huella
from scripts.auditar_fuente_espn_soccer import FuenteNoDisponible as FinalNoAcreditado

CONTRATO = 'AGENDA_MULTILIGA_V1'


def pedidos(ligas, hoy, horizonte=60):
    """Ventana COT exacta. El día UTC adicional no amplía el rango comunicado."""
    if type(horizonte) is not int or not 1 <= horizonte <= 60:
        raise ValueError('Horizonte permitido: 1 a 60 días')
    desde, hasta = hoy - timedelta(days=1), hoy + timedelta(days=horizonte)
    grupos = []
    for liga in ligas:
        code = liga['codigo']
        feed = next((f for f, c in FUTBOL.items() if c == code), None)
        tasks = []
        if liga['deporte'] == 'futbol' and feed:
            day = desde.replace(day=1)
            while day <= hasta:
                tasks.append((f'https://site.api.espn.com/apis/site/v2/sports/soccer/{feed}/scoreboard',
                              {'dates': day.strftime('%Y%m'), 'limit': 500}, feed))
                day = meses(day, 1)
        elif code in ('nba', 'wnba'):
            for offset in range((hasta - desde).days + 2):
                day = desde + timedelta(days=offset)
                tasks.append((f'https://site.api.espn.com/apis/site/v2/sports/basketball/{code}/scoreboard',
                              {'dates': day.strftime('%Y%m%d'), 'limit': 500}, code))
        elif code == 'euroleague':
            for year in range(desde.year - (desde.month < 7), hasta.year - (hasta.month < 7) + 1):
                tasks.append((f'https://api-live.euroleague.net/v2/competitions/E/seasons/E{year}/games',
                              {'limit': 500}, 'euroliga'))
        group = deque()
        for url, params, origin in tasks:
            descriptor = {'liga': dict(liga), 'url': url, 'params': params, 'feed': origin,
                          'desde': str(desde), 'hasta': str(hasta)}
            group.append({**descriptor, 'clave': huella(descriptor)})
        grupos.append(group)
    result = []
    while any(grupos):
        for group in grupos:
            if group:
                result.append(group.popleft())
    return result


def verificar_captura(payload, meta):
    raw = Path(meta['archivo']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != meta['sha256'] or json.loads(raw) != payload:
        raise ValueError('Captura fuente alterada o JSON distinto de sus bytes')
    if meta.get('http') != 200 or not meta.get('url'):
        raise ValueError('Captura sin respuesta acreditada')
    instante(meta['observado_en'])


def inventario_evento(evento, feed):
    """Identidad mínima para localizar un error aunque no pueda normalizarse."""
    official = feed == 'euroliga'
    event_id = evento.get('identifier') if official else evento.get('id')
    year = (evento.get('season') or {}).get('year')
    if official:
        raw = evento.get('utcDate') if evento.get('confirmedDate') is True and evento.get('confirmedHour') is True else (evento.get('date') or '')[:10]
    else:
        confirmed, source_day = hora_espn(evento)
        raw = confirmed or source_day
    if not event_id or type(year) is not int or not isinstance(raw, str):
        raise ValueError('Evento sin ID, temporada o fecha localizable')
    if len(raw) == 10:
        day = date.fromisoformat(raw)
        start = None
    else:
        start = instante(raw)
        day = start.astimezone(BOGOTA).date()
    final = evento.get('played') is True if official else (evento.get('status') or {}).get('type', {}).get('completed') is True
    return {'id': str(event_id), 'anio': str(year), 'fecha': str(day),
            'inicio_utc': start.isoformat() if start else None, 'final': final}


def recolectar_agenda(client, solicitudes, observar=lambda _: None):
    """Una fuente fallida no impide leer las demás. No abre clientes paralelos."""
    rows, blocked, consultas = {}, set(), []
    for request in solicitudes:
        code, feed = request['liga']['codigo'], request['feed']
        lower, upper = date.fromisoformat(request['desde']), date.fromisoformat(request['hasta'])
        result = {**request, 'estado': 'ERROR', 'inventario': [], 'incidencias': [], 'pruebas': []}
        observar(f'{code}: agenda {request["params"].get("dates", "temporada oficial")}')
        try:
            payload, meta = client.json(request['url'], request['params'], ttl=1800)
            verificar_captura(payload, meta)
            meta = {**meta, 'observado_en': instante(meta['observado_en']).isoformat()}
            expected_url = request['url'] + '?' + urlencode(request['params'])
            if meta['url'] != expected_url:
                raise ValueError('La captura no corresponde a la solicitud')
            result['pruebas'] = [meta]
            if not isinstance(payload, dict):
                raise ValueError('Contrato de raíz JSON no admitido')
            events = payload.get('data') if feed == 'euroliga' else payload.get('events')
            if not isinstance(events, list) or len(events) >= 500:
                raise ValueError('Feed ausente o truncado')
            if feed == 'euroliga':
                if payload.get('total') != len(events):
                    raise ValueError('Total oficial incompatible')
            else:
                leagues = payload.get('leagues') or []
                if len(leagues) != 1 or leagues[0].get('slug') != feed:
                    raise ValueError('La respuesta no acredita la competición')
                total = payload.get('total')
                if total is not None and total != len(events):
                    raise ValueError('Total ESPN incompatible')
            result.update(estado='OBSERVADA', pruebas=[meta], motivo=None)
            for event in events:
                try:
                    item = inventario_evento(event, feed)
                except (ValueError, KeyError, TypeError, AttributeError):
                    result['estado'] = 'ERROR'
                    result['incidencias'].append({'grupo': code, 'motivo': 'EVENTO_SIN_IDENTIDAD_MINIMA', 'ambito': 'VENTANA'})
                    continue
                if not lower <= date.fromisoformat(item['fecha']) <= upper:
                    continue
                result['inventario'].append(item)
                key = (code, item['id'])
                try:
                    if key in blocked:
                        raise ValueError('Revisiones contradictorias del mismo evento')
                    detail = None
                    status = (event.get('status') or {}).get('type', {}).get('name')
                    if feed != 'euroliga' and status in ('STATUS_FINAL_AET', 'STATUS_FINAL_PEN'):
                        _, detail = client.json(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{feed}/summary',
                                                {'event': item['id']}, ttl=1800)
                        result['pruebas'].append(detail)
                    row = euro(event, meta, upper, desde=lower) if feed == 'euroliga' else espn(
                        event, code, feed, meta, upper, detail, desde=lower)
                    if row is None:
                        raise ValueError('El evento inventariado no se pudo normalizar')
                    old = rows.get(key)
                    semantic = lambda r: {k: v for k, v in r.items() if k != 'evidencia'}
                    if old and semantic(old) != semantic(row):
                        blocked.add(key)
                        raise ValueError('Revisiones contradictorias del mismo evento')
                    rows[key] = row
                except (ValueError, KeyError, TypeError, IndexError, AttributeError, RuntimeError, FinalNoAcreditado) as exc:
                    rows.pop(key, None)
                    blocked.add(key)
                    result['incidencias'].append({'grupo': code, 'id': item['id'],
                        'motivo': str(exc), 'evento': item, 'evidencia': meta})
        except (ValueError, KeyError, TypeError, AttributeError, OSError, RuntimeError) as exc:
            result['motivo'] = str(exc)
            result['estado'] = 'ERROR'
        consultas.append(result)
    inventory = {}
    for query in consultas:
        for item in query['inventario']:
            inventory[(query['liga']['codigo'], item['id'])] = item
    return {'contrato': CONTRATO, 'registros': list(rows.values()), 'consultas': consultas,
            'eventos_fuente_unicos': len(inventory),
            'denominador': 'Solo eventos enumerados por las capturas; no calendario oficial íntegro'}


def cobertura_agenda(paquete, ligas):
    result = []
    for liga in ligas:
        code = liga['codigo']
        qs = [q for q in paquete['consultas'] if q['liga']['codigo'] == code]
        items = {e['id']: e for q in qs for e in q['inventario']}
        normal = [r for r in paquete['registros'] if r['codigo'] == code]
        times = [r['inicio_utc'] for r in normal if r['inicio_utc']]
        result.append({'codigo': code, 'solicitadas': len(qs),
            'consultas_observadas': sum(q['estado'] == 'OBSERVADA' for q in qs),
            'desde_solicitado': min((q['desde'] for q in qs), default=None),
            'hasta_solicitado': max((q['hasta'] for q in qs), default=None),
            'eventos_enumerados': len(items), 'eventos_normalizados': len(normal),
            'horas_confirmadas': sum(r['precision_fecha'] == 'HORA' for r in normal),
            'horas_sin_confirmar': sum(r['precision_fecha'] != 'HORA' for r in normal),
            'ultimo_inicio_observado': max(times, default=None),
            'ultima_fecha_publicada': max((e['fecha'] for e in items.values()), default=None),
            'estado': ('SIN_ADAPTADOR' if not qs else 'PARCIAL' if any(q['estado'] != 'OBSERVADA' or q['incidencias'] for q in qs)
                       else 'SIN_EVENTOS_PUBLICADOS' if not items else 'OBSERVADA_EN_FUENTE'),
            'cobertura_oficial': 'DESCONOCIDA'})
    return result
