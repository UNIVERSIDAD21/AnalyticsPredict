"""Calendario móvil WNBA: fuentes acotadas, fixtures sin puntos y revisiones.

Consultar BD no sincroniza. Sincronizar no incorpora FT ni actualiza modelos.
La transacción y el respaldo pertenecen al llamador.
"""
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import time
from uuid import uuid4

import requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ingesta_wnba import BOGOTA, exigir, huella, uid, instante

MIGRACION = Path(__file__).resolve().parents[1] / 'migrations/2026-10-25_calendario_wnba.sql'
ESPN = 'https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard'
OFICIAL = 'https://cdn.wnba.com/static/json/staticData/scheduleLeagueV2.json'


def ventana(desde=None):
    desde = desde or datetime.now(BOGOTA).date()
    mes = desde.month - 1 + 3
    year, month = desde.year + mes // 12, mes % 12 + 1
    return desde, date(year, month, min(desde.day, monthrange(year, month)[1]))


def normalizar_evento(e, desde, hasta):
    exigir(isinstance(e, dict) and str(e.get('id', '')).isdigit(), 'Evento sin ID ESPN')
    cs = e.get('competitions', [])
    exigir(len(cs) == 1, 'Competición ESPN ambigua')
    c = cs[0]
    lados = {x.get('homeAway'): x for x in c.get('competitors', [])}
    exigir(set(lados) == {'home', 'away'}, 'Localía ESPN no acreditada')
    h, a = lados['home']['team'], lados['away']['team']
    exigir(str(h.get('id', '')).isdigit() and str(a.get('id', '')).isdigit() and h['id'] != a['id'], 'Equipos ESPN ambiguos')
    tipo = e.get('status', c.get('status', {})).get('type', {})
    nombre = tipo.get('name', '')
    estados = {'STATUS_SCHEDULED':'PROGRAMADO','STATUS_POSTPONED':'POSPUESTO',
               'STATUS_CANCELED':'CANCELADO','STATUS_CANCELLED':'CANCELADO',
               'STATUS_DELAYED':'DEMORADO','STATUS_SUSPENDED':'SUSPENDIDO',
               'STATUS_FINAL':'FINALIZADO','STATUS_IN_PROGRESS':'EN_VIVO',
               'STATUS_HALFTIME':'EN_VIVO','STATUS_END_PERIOD':'EN_VIVO'}
    exigir(nombre in estados, 'Estado ESPN desconocido: '+nombre)
    raw_fecha = e.get('date') or c.get('date')
    solo_dia = bool(raw_fecha) and len(raw_fecha) == 10
    hora = c.get('timeValid') is not False and not any(x in str(tipo.get('detail','')).upper() for x in ('TBD','TBA')) and bool(raw_fecha) and not solo_dia
    dt = instante(raw_fecha) if raw_fecha and not solo_dia else None
    # Una fecha sin hora NO es medianoche UTC convertida al día anterior COT.
    dia = dt.astimezone(BOGOTA).date() if hora else date.fromisoformat(raw_fecha[:10]) if raw_fecha else None
    if dia and not desde <= dia <= hasta:
        return None
    season = e.get('season', {})
    anio = season.get('year', dia.year if dia else None)
    exigir(type(anio) is int and (dia is None or anio == dia.year), 'Temporada WNBA anual contradictoria')
    fase = {1:'PRE',2:'REG',3:'POST'}.get(season.get('type'))
    exigir(fase is not None, 'Fase WNBA no reconocida')
    notas = ' '.join(str(x.get('headline','')) for x in c.get('notes', []))
    if 'commissioner' in notas.lower() and 'final' in notas.lower():
        fase = 'COPA'
    return {'source_game_id':str(e['id']), 'temporada':anio, 'fase':fase,
            'local_id_fuente':str(h['id']), 'visitante_id_fuente':str(a['id']),
            'local_nombre':h.get('displayName'), 'visitante_nombre':a.get('displayName'),
            'inicio_utc':dt.astimezone(timezone.utc).isoformat() if hora else None,
            'fecha_local':dia.isoformat() if dia else None, 'precision_fecha':'HORA' if hora else 'DIA' if dia else 'PENDIENTE',
            **({'ventana_consulta':f'{desde}/{hasta}'} if dia is None else {}),
            'estado':estados[nombre], 'fuente':'ESPN',
            'condicional': bool(c.get('ifNecessary')) or 'if necessary' in notas.lower(),
            'url_fuente':'https://www.espn.com/wnba/game/_/gameId/'+str(e['id']),
            'oficial_verificado':False}


def obtener_json(url, sesion, evidencia):
    r = sesion.get(url, timeout=(5, 20), allow_redirects=False)
    evidencia.append({'url':url, 'http':r.status_code, 'sha256':__import__('hashlib').sha256(r.content).hexdigest()})
    exigir(r.status_code not in (401,403,429) and not 300 <= r.status_code < 400,
           f'Fuente detenida HTTP {r.status_code}; sin bypass ni reintento')
    r.raise_for_status()
    exigir(len(r.content) <= 8_000_000, 'Respuesta fuera del límite; fuente parcialmente consultada')
    return r.json()


def consultar(desde=None, *, sesion=None, pausa=1.5, cache=None):
    desde, hasta = ventana(desde)
    s = sesion or requests.Session()
    fuentes, errores, registros, vistos = [], [], {}, set()
    observado = datetime.now(timezone.utc).isoformat()
    oficial = None
    try:
        oficial = obtener_json(OFICIAL, s, fuentes)
        exigir(oficial.get('leagueSchedule',{}).get('leagueId') == '10', 'Feed no pertenece a WNBA')
        fuentes[-1]['estado'] = 'CONSULTADA'
    except (ValueError, requests.RequestException) as e:
        errores.append({'fuente':'oficial','motivo':type(e).__name__})
        if fuentes: fuentes[-1]['estado'] = 'FALLO_CONSULTA'
    total = (hasta - desde).days + 1
    dias_ok = 0
    bordes_ok = 0
    # ESPN agrupa por su día de competición; consultar guardas y filtrar por COT
    # evita perder eventos próximos a medianoche y cambios de DST del proveedor.
    for n in range(-1,total+1):
        dia = desde + timedelta(days=n)
        url = ESPN+'?dates='+dia.strftime('%Y%m%d')+'&limit=1000'
        try:
            if cache and (Path(cache)/(str(dia)+'.json')).exists():
                path = Path(cache)/(str(dia)+'.json')
                j = json.loads(path.read_text())
                fuentes.append({'url':url,'http':200,'sha256':__import__('hashlib').sha256(path.read_bytes()).hexdigest(),'estado':'CACHE_OBSERVADA'})
            else:
                j = obtener_json(url, s, fuentes)
                time.sleep(pausa)
            events = j.get('events')
            exigir(isinstance(events,list) and len(events)<1000, 'ESPN truncado o sin lista de eventos')
            if 0 <= n < total:
                dias_ok += 1
            else:
                bordes_ok += 1
            for e in events:
                r = normalizar_evento(e, desde, hasta)
                if r:
                    key = r['source_game_id']
                    exigir(key not in registros or registros[key] == r, 'Revisiones contradictorias durante la consulta')
                    registros[key] = r
                vistos.add(str(e['id']))
            fuentes[-1]['estado'] = 'CONSULTADA'
        except (ValueError, KeyError, requests.RequestException) as e:
            errores.append({'fuente':url,'motivo':str(e) if isinstance(e,ValueError) else type(e).__name__})
            if fuentes and fuentes[-1]['url'] == url:
                fuentes[-1]['estado'] = 'FALLO_CONSULTA'
                if fuentes[-1].get('http') in (401,403,429): break
    # Un feed oficial de una temporada no certifica la temporada siguiente.
    anio_oficial = str(oficial.get('leagueSchedule',{}).get('seasonYear','')) if oficial else ''
    completo_oficial = bool(oficial) and desde.year == hasta.year and anio_oficial == str(desde.year)
    estado = 'PARTIDOS_PUBLICADOS' if registros else 'CONSULTADA_SIN_ENCUENTROS' if dias_ok == total and completo_oficial else 'CONSULTA_PARCIAL' if dias_ok else 'FALLO_CONSULTA'
    return {'desde':str(desde),'hasta':str(hasta),'comprobado_utc':observado,'estado':estado,
            'dias_consultados':dias_ok,'dias_requeridos':total,'fuentes':fuentes,'errores':errores,
            'guardas_huso_consultadas':bordes_ok,'guardas_huso_requeridas':2,
            'oficial_completa':completo_oficial,'temporada_oficial':anio_oficial or None,
            'estado_consulta_espn':'CONSULTADA_COMPLETA' if dias_ok==total and bordes_ok==2 else 'CONSULTA_PARCIAL' if dias_ok else 'FALLO_CONSULTA',
            'estado_consulta_oficial':'CONSULTADA_COMPLETA' if completo_oficial else 'CONSULTA_PARCIAL' if oficial else 'FALLO_CONSULTA',
            'detalle':f'{len(registros)} encuentros fuente publicados. {dias_ok}/{total} días ESPN. '+
                ('Calendario oficial del rango comprobado.' if completo_oficial else 'Verificación oficial incompleta; no se afirma ausencia de encuentros ni calendario siguiente no publicado sin evidencia.'),
            'partidos':list(registros.values())}


def aplicar(conn, reporte):
    """Solo fixtures; nunca FT, apuestas, modelos ni correcciones de históricos."""
    conn.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:wnba:calendario'))")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id FROM competiciones_baloncesto WHERE codigo='wnba'")
        comp = cur.fetchone(); exigir(comp is not None, 'WNBA no configurada')
        cid = comp['id']
        cur.execute('SELECT * FROM equipos_baloncesto WHERE competicion_principal_id=%s', (cid,))
        mappings = cur.fetchall()
        maps = {str(x['espn_team_id']):str(x['id']) for x in mappings if x['espn_team_id']}
        resultado = {'altas':0,'revisados':0,'sin_cambios':0}
        for r in reporte['partidos']:
            exigir(r['local_id_fuente'] in maps and r['visitante_id_fuente'] in maps,'Equipo WNBA sin crosswalk explícito; no se infiere por nombre')
            h, a = maps[r['local_id_fuente']], maps[r['visitante_id_fuente']]
            cur.execute('SELECT id FROM temporadas_baloncesto WHERE competicion_id=%s AND anio_inicio=%s AND es_anual', (cid,r['temporada']))
            season = cur.fetchone()
            if not season:
                tid = uid('temporada',str(r['temporada']))
                cur.execute('INSERT INTO temporadas_baloncesto(id,competicion_id,nombre,anio_inicio,anio_fin,es_anual) VALUES(%s,%s,%s,%s,%s,true)', (tid,cid,str(r['temporada']),r['temporada'],r['temporada']))
            else: tid = str(season['id'])
            fid = uid('fixture',r['source_game_id'])
            digest = huella(r)
            cur.execute('SELECT * FROM fixtures_wnba WHERE source_game_id=%s FOR UPDATE',(r['source_game_id'],))
            old = cur.fetchone()
            if old:
                exigir(str(old['equipo_local_id'])==h and str(old['equipo_visitante_id'])==a and str(old['temporada_id'])==tid and old['fase']==r['fase'], 'Cambio de identidad WNBA: requiere revisión, no sobrescritura')
                if old['resultado_id'] is not None:
                    exigir(r['estado']=='FINALIZADO' and all(r.get(k)==old['registro'].get(k)
                           for k in ('inicio_utc','fecha_local','local_id_fuente','visitante_id_fuente')),
                           'Final válido protegido: requiere revisión histórica explícita')
                    # El calendario no reemplaza el registro/hash de un FT ya validado.
                    resultado['sin_cambios']+=1
                    continue
                if not r.get('oficial_verificado') and old['registro'].get('oficial_verificado') and all(
                        r.get(k)==old['registro'].get(k) for k in ('inicio_utc','fecha_local','estado','local_id_fuente','visitante_id_fuente')):
                    # Conservar la corroboración anterior y SU fecha, no afirmar que
                    # una consulta bloqueada la acaba de volver a verificar.
                    r={**r,**{k:v for k,v in old['registro'].items() if k.startswith('oficial_') or k=='condicional'}}
                    digest=huella(r)
                if old['revision_sha256']==digest:
                    resultado['sin_cambios']+=1;continue
                exigir(old['resultado_id'] is None, 'Final válido protegido: requiere revisión histórica explícita')
                resultado['revisados']+=1
                fid = str(old['id'])
            else: resultado['altas']+=1
            cur.execute('''INSERT INTO fixtures_wnba(id,competicion_id,temporada_id,equipo_local_id,equipo_visitante_id,source_game_id,
               inicio_utc,fecha_local,precision_fecha,estado,fase,revision_sha256,registro)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT(id) DO UPDATE SET inicio_utc=excluded.inicio_utc,fecha_local=excluded.fecha_local,
               precision_fecha=excluded.precision_fecha,estado=excluded.estado,revision_sha256=excluded.revision_sha256,
               registro=excluded.registro,actualizado_en=now()''',
               (fid,cid,tid,h,a,r['source_game_id'],r['inicio_utc'],r['fecha_local'],r['precision_fecha'],r['estado'],r['fase'],digest,Jsonb(r)))
            cur.execute('''INSERT INTO revisiones_fixtures_wnba(fixture_id,sha256,registro,observado_utc,procedencia)
               VALUES(%s,%s,%s,%s,%s) ON CONFLICT(fixture_id,sha256) DO NOTHING''',
               (fid,digest,Jsonb(r),reporte['comprobado_utc'],Jsonb({'fuentes':reporte['fuentes']})))
        cur.execute('''INSERT INTO comprobaciones_calendario_wnba(id,desde,hasta,comprobado_utc,reporte)
            VALUES(%s,%s,%s,%s,%s)''',(uuid4(),reporte['desde'],reporte['hasta'],reporte['comprobado_utc'],Jsonb({k:v for k,v in reporte.items() if k!='partidos'})))
    return resultado


def listar(conn, desde=None):
    desde,hasta=ventana(desde)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute('''SELECT f.*,e.nombre local,v.nombre visitante,t.nombre temporada_nombre,'wnba' competicion_codigo
          FROM fixtures_wnba f JOIN equipos e ON e.id=f.equipo_local_id JOIN equipos v ON v.id=f.equipo_visitante_id
          JOIN temporadas_baloncesto t ON t.id=f.temporada_id JOIN competiciones_baloncesto c ON c.id=f.competicion_id
          WHERE c.codigo='wnba' AND (f.fecha_local BETWEEN %s AND %s OR (f.fecha_local IS NULL AND f.registro->>'ventana_consulta'=%s))
          ORDER BY f.fecha_local NULLS LAST,f.inicio_utc,f.id''',(desde,hasta,f'{desde}/{hasta}'))
        rows=cur.fetchall()
        cur.execute('''SELECT reporte FROM comprobaciones_calendario_wnba WHERE desde=%s AND hasta=%s
          ORDER BY comprobado_utc DESC LIMIT 1''',(desde,hasta))
        check=cur.fetchone()
        return rows,check['reporte'] if check else {'desde':str(desde),'hasta':str(hasta),
               'comprobado_utc':'N/D','estado':'SIN_COMPROBAR','detalle':'BD consultada; aún no se sincronizó este rango con la fuente. Actualizar sincroniza calendario, no resultados ni modelo.','fuentes':[]}


def vincular_final(conn, registro, partido_id):
    """Enlace estable después de importar un final validado. No inventa FT ni lo corrige."""
    from ingesta_wnba import validar_registro
    validar_registro(registro)
    exigir(registro['final_completo'], 'Solo se vinculan finales completos')
    with conn.cursor(row_factory=dict_row) as cur:
        # Compatible con instalaciones que aún no aplicaron esta ampliación.
        cur.execute("SELECT to_regclass('public.fixtures_wnba') existe")
        if cur.fetchone()['existe'] is None: return False
        cur.execute('SELECT * FROM fixtures_wnba WHERE source_game_id=%s FOR UPDATE',(registro['source_game_id'],))
        f=cur.fetchone()
        if not f: return False
        exigir(str(f['equipo_local_id'])==uid('equipo',registro['local_id_fuente']) and
               str(f['equipo_visitante_id'])==uid('equipo',registro['visitante_id_fuente']), 'Final y fixture de identidades distintas')
        exigir(str(f['temporada_id'])==uid('temporada',str(registro['temporada'])) and f['fase']==registro['fase'],
               'Final y fixture de temporada/fase distintas: requiere revisión')
        exigir(f['resultado_id'] is None or str(f['resultado_id'])==str(partido_id), 'Fixture ya vinculado a otro final')
        inicio=instante(registro['inicio_utc']).astimezone(timezone.utc)
        fecha=inicio.astimezone(BOGOTA).date()
        payload={**f['registro'],'estado':'FINALIZADO','resultado_sha256':huella(registro),
                 'inicio_utc':inicio.isoformat(),'fecha_local':fecha.isoformat(),'precision_fecha':'HORA'}
        digest=huella(payload)
        if str(f['resultado_id']) == str(partido_id) and f['revision_sha256'] == digest:
            return False
        cur.execute('''INSERT INTO revisiones_fixtures_wnba(fixture_id,sha256,registro,observado_utc,procedencia)
           VALUES(%s,%s,%s,now(),%s) ON CONFLICT(fixture_id,sha256) DO NOTHING''',
           (f['id'],digest,Jsonb(payload),Jsonb({'final_fuente':registro['url_fuente'],'registro_sha256':huella(registro)})))
        cur.execute("UPDATE fixtures_wnba SET resultado_id=%s,estado='FINALIZADO',inicio_utc=%s,fecha_local=%s,precision_fecha='HORA',registro=%s,revision_sha256=%s,actualizado_en=now() WHERE id=%s",(partido_id,inicio,fecha,Jsonb(payload),digest,f['id']))
        cur.execute("UPDATE apuestas SET partido_id=%s WHERE fixture_wnba_id=%s AND partido_id IS NULL AND competicion_id=%s",(partido_id,f['id'],f['competicion_id']))
        cur.execute("SELECT to_regclass('public.selecciones_combinada') existe")
        if cur.fetchone()['existe'] is not None:
            cur.execute("""UPDATE selecciones_combinada SET partido_id=%s WHERE partido_id IS NULL
                AND razones @> %s::jsonb""",(partido_id,Jsonb([{'tipo':'trazabilidad_wnba','partido_id':str(f['id'])}])))
        return True
