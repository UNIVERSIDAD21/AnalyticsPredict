"""Revisión acotada de finales; comparte transporte y contratos con las agendas."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlencode

from servicios.fuentes_agenda import BOGOTA, FUTBOL, espn, euro, instante, meses
from servicios.transporte_agenda import FuenteNoDisponible, HOSTS


class Capturas:
    """Reproduce únicamente URLs y bytes guardados, sin HTTP ni fechas rejuvenecidas."""
    def __init__(self, path, completar=None):
        self.items = {x['url']: x for x in json.loads(Path(path).read_text(encoding='utf-8'))}
        self.http = self.hits = 0
        self.completar = completar

    def json(self, url, params=None, **_):
        from urllib.parse import urlsplit
        if urlsplit(url).hostname not in HOSTS:
            raise FuenteNoDisponible('Origen no permitido')
        key = url + ('?' + urlencode(params) if params else '')
        if key not in self.items:
            if self.completar is not None:
                result = self.completar.json(url, params, **_)
                self.http = self.completar.http
                return result
            raise FuenteNoDisponible('No existe captura para esta consulta; no se abre la red')
        meta = self.items[key]
        raw = Path(meta['archivo']).read_bytes()
        if sha256(raw).hexdigest() != meta['sha256']:
            raise FuenteNoDisponible('Captura alterada')
        self.hits += 1
        return json.loads(raw), meta


def tareas(liga, desde, hasta):
    code = liga['codigo']
    if liga['deporte'] == 'futbol':
        feed = next((f for f, c in FUTBOL.items() if c == code), None)
        if not feed:
            return
        day = desde.replace(day=1)
        while day <= hasta:
            yield f'https://site.api.espn.com/apis/site/v2/sports/soccer/{feed}/scoreboard', {'dates': day.strftime('%Y%m'), 'limit': 500}, feed
            day = meses(day, 1)
    elif code in ('nba', 'wnba'):
        # El último día UTC incluye los encuentros nocturnos de Colombia.
        day = desde
        while day <= hasta + timedelta(days=1):
            yield f'https://site.api.espn.com/apis/site/v2/sports/basketball/{code}/scoreboard', {'dates': day.strftime('%Y%m%d'), 'limit': 500}, code
            day += timedelta(days=1)
    elif code == 'euroleague':
        first = desde.year - (desde.month < 7)
        last = hasta.year - (hasta.month < 7)
        for year in range(first, last + 1):
            yield f'https://api-live.euroleague.net/v2/competitions/E/seasons/E{year}/games', {'limit': 500}, 'euroliga'


def recolectar(client, liga, desde, hasta, observar=lambda _: None):
    rows, issues, proofs = {}, [], []
    contradictorios = set()
    pending = 0
    jobs = list(tareas(liga, desde, hasta))
    if not jobs:
        return [], [{'grupo': liga['codigo'], 'motivo': 'SIN_ADAPTADOR: competición sin fuente vigente configurada; se conserva su histórico'}], [], 0
    for url, params, feed in jobs:
        observar(f"{liga['nombre']}: revisando {params.get('dates', 'temporada oficial')}")
        try:
            payload, meta = client.json(url, params, ttl=300)
            proofs.append(meta)
            events = payload.get('data') if feed == 'euroliga' else payload.get('events')
            if (not isinstance(events, list) or len(events) >= 500 or
                    (feed == 'euroliga' and payload.get('total') != len(events))):
                raise ValueError('Feed ausente, truncado o con contrato diferente')
            if feed != 'euroliga' and (len(payload.get('leagues', [])) != 1 or payload['leagues'][0].get('slug') != feed):
                raise ValueError('El feed no acredita la liga solicitada')
            for event in events:
                ident = str(event.get('identifier') if feed == 'euroliga' else event.get('id'))
                if ident in contradictorios:
                    continue
                try:
                    raw_date = event.get('utcDate') if feed == 'euroliga' else event.get('date')
                    day = instante(raw_date).astimezone(BOGOTA).date()
                    if not desde <= day <= hasta:
                        continue
                    final = event.get('played') is True if feed == 'euroliga' else event.get('status', {}).get('type', {}).get('completed') is True
                    if not final:
                        pending += 1
                        continue
                    detail = None
                    if feed != 'euroliga' and event.get('status', {}).get('type', {}).get('name') in ('STATUS_FINAL_AET', 'STATUS_FINAL_PEN'):
                        _, detail = client.json(f'https://site.api.espn.com/apis/site/v2/sports/soccer/{feed}/summary', {'event': ident}, ttl=300)
                        proofs.append(detail)
                    row = euro(event, meta, hasta, desde=desde) if feed == 'euroliga' else espn(event, liga['codigo'], feed, meta, hasta, detail, desde=desde)
                    if row is None:
                        continue
                    if ident in rows:
                        a = {k: v for k, v in rows[ident].items() if k != 'evidencia'}
                        b = {k: v for k, v in row.items() if k != 'evidencia'}
                        if a != b:
                            contradictorios.add(ident)
                            raise ValueError('Revisiones distintas del mismo evento; requiere conciliación')
                    rows[ident] = row
                except (ValueError, KeyError, TypeError, IndexError, FuenteNoDisponible) as exc:
                    rows.pop(ident, None)
                    issues.append({'grupo': liga['codigo'], 'id': ident, 'motivo': str(exc)})
        except (ValueError, KeyError, TypeError, FuenteNoDisponible) as exc:
            issues.append({'grupo': liga['codigo'], 'motivo': str(exc), 'ambito': 'VENTANA',
                           'fuente': feed, 'solicitud': url + '?' + urlencode(params)})
    return list(rows.values()), issues, proofs, pending
