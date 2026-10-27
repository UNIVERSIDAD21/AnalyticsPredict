"""Plan incremental revisable y aplicación atómica. Sin HTTP ni modelos.

Las identidades se resuelven con vínculos de proveedor o crosswalks explícitos,
nunca por semejanza. Una corrección de un final contradictorio queda fuera.
"""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from uuid import NAMESPACE_URL, uuid4, uuid5
from zoneinfo import ZoneInfo

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from servicios.fuentes_agenda import instante
from scripts.sincronizar_euroleague_futuros import TEAM_ALIASES
from scripts.scraper_partidos_futuros import ESPN_NAME_ALIASES

MIGRACION = __import__('pathlib').Path(__file__).resolve().parents[1]/'migrations/2026-10-26_sincronizacion_agendas.sql'
TABLAS = {'partidos_baloncesto','partidos_futbol','horarios_baloncesto','horarios_futbol',
          'fixtures_wnba','partidos_fuente_espn_futbol'}


def plano(v):
    def serializar(x):
        if isinstance(x,datetime) and x.tzinfo is not None:
            return x.astimezone(timezone.utc).isoformat()
        return x.isoformat() if hasattr(x,'isoformat') else str(x)
    return json.loads(json.dumps(v,default=serializar))


def huella(v):
    return hashlib.sha256(json.dumps(plano(v),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def filas(conn, consulta, args=()):
    with conn.cursor(row_factory=dict_row) as c:
        return [plano(r) for r in c.execute(consulta,args).fetchall()]


def existe(conn, tabla):
    with conn.cursor(row_factory=dict_row) as c:
        return c.execute('SELECT to_regclass(%s) tabla',(tabla,)).fetchone()['tabla'] is not None


def identidad(p, r, season):
    return (p['equipo_local_id'],p['equipo_visitante_id'],p['competicion_id'],p['temporada_id']) == (
        r['local_id'],r['visitante_id'],r['competicion_id'],season)


def planificar(conn, registros, incidencias, fuentes, hoy):
    compsb = {r['codigo']:r['id'] for r in filas(conn,'SELECT id,codigo FROM competiciones_baloncesto')}
    compsf = {r['codigo']:r['id'] for r in filas(conn,'SELECT id,codigo FROM competiciones_futbol')}
    seasonsb = filas(conn,'SELECT id,competicion_id,anio_inicio,anio_fin FROM temporadas_baloncesto')
    seasonsf = {(r['liga'],r['anio']):r['temporada_id'] for r in filas(conn,'SELECT liga,anio,temporada_id FROM temporadas_fuente_espn_futbol')}
    teams = filas(conn,'SELECT id,nombre,competicion_principal_id FROM equipos')
    mapsf = {r['id_fuente']:r['equipo_id'] for r in filas(conn,'SELECT id_fuente,equipo_id FROM equipos_fuente_espn_futbol')}
    mapsw = {str(r['espn_team_id']):r['id'] for r in filas(conn,"SELECT id,espn_team_id FROM equipos_baloncesto WHERE competicion_principal_id=%s",(compsb['wnba'],)) if r['espn_team_id']}
    pb = filas(conn,'SELECT * FROM partidos_baloncesto WHERE fecha_partido BETWEEN %s AND %s',
               (hoy-timedelta(days=12),hoy+timedelta(days=96)))
    # Vínculo global por ID para detectar reprogramaciones fuera del día previo.
    ids = list({r['id_fuente'] for r in registros if r['deporte']=='baloncesto'})
    pb_extra = filas(conn,'SELECT * FROM partidos_baloncesto WHERE source_game_id=ANY(%s) OR espn_game_id=ANY(%s)',(ids,ids))
    pb = list({r['id']:r for r in pb+pb_extra}.values())
    pf = filas(conn,'SELECT * FROM partidos_futbol WHERE fecha_partido BETWEEN %s::date-interval \'3 days\' AND %s::date+interval \'96 days\'',(hoy,hoy))
    links = filas(conn,'SELECT * FROM partidos_fuente_espn_futbol')
    source_keys = {(x.get('feed'),x['id_fuente']) for x in registros}
    linked_ids = list({r['partido_id'] for r in links if (r['liga'],r['id_fuente']) in source_keys})
    if linked_ids:
        pf += filas(conn,'SELECT * FROM partidos_futbol WHERE id=ANY(%s::uuid[])',(linked_ids,))
    pf = list({r['id']:r for r in pf}.values())
    fixtures = filas(conn,'SELECT * FROM fixtures_wnba')
    metas = {t:{r['partido_id']:r for r in filas(conn,'SELECT * FROM '+t)} if existe(conn,t) else {}
             for t in ('horarios_baloncesto','horarios_futbol')}
    # Los enlaces aditivos también resuelven reprogramaciones que se alejan de
    # la fecha canónica y de las fuentes legacy más de dos días.
    if metas['horarios_baloncesto']:
        extra=filas(conn,'SELECT * FROM partidos_baloncesto WHERE id=ANY(%s::uuid[])',
                    (list(metas['horarios_baloncesto']),))
        pb=list({r['id']:r for r in pb+extra}.values())
    plan = {'version':1,'fecha_cot':str(hoy),'operaciones':[], 'incidencias':list(incidencias),
            'fuentes':fuentes,'aceptados':[], 'sin_cambios':0}
    claves = set()

    def op(tabla, pid, old, values, r, clave='id'):
        changes = {k:plano(v) for k,v in values.items() if old is None or plano(v)!=old.get(k)}
        if old is not None and not changes:
            return
        key = (tabla,str(pid))
        if key in claves:
            raise ValueError('Dos eventos intentan modificar la misma fila')
        claves.add(key)
        plan['operaciones'].append({'tabla':tabla,'clave':clave,'id':str(pid),
            'antes':old,'valores':changes,'evento':r['id_fuente'],'codigo':r['codigo'],
            'deporte':r['deporte'],'observado_en':r['evidencia']['observado_en'],
            'procedencia':r['evidencia']})

    for original in registros:
        r = dict(original)
        n0 = len(plan['operaciones'])
        claves0 = set(claves)
        try:
            code, sourceid = r['codigo'],r['id_fuente']
            comp = (compsb if r['deporte']=='baloncesto' else compsf)[code]
            r['competicion_id'] = comp
            if r['deporte']=='futbol':
                r['local_id'],r['visitante_id'] = mapsf[r['local_fuente']],mapsf[r['visitante_fuente']]
                season = seasonsf[(r['feed'],r['anio'])]
                source = next((x for x in links if (x['liga'],x['id_fuente'])==(r['feed'],sourceid)),None)
                old = next((x for x in pf if source and x['id']==source['partido_id']),None)
                if source and not old:
                    raise ValueError('Vínculo canónico sin partido')
            else:
                if code=='wnba':
                    r['local_id'],r['visitante_id'] = mapsw[r['local_fuente']],mapsw[r['visitante_fuente']]
                else:
                    aliases = ESPN_NAME_ALIASES if code=='nba' else TEAM_ALIASES
                    mapped = []
                    for name in (r['local_nombre'],r['visitante_nombre']):
                        target = aliases.get(name.casefold(),name).casefold()
                        matches = [x['id'] for x in teams if x['competicion_principal_id']==comp and x['nombre'].casefold()==target]
                        if len(matches)!=1:
                            raise ValueError('Equipo sin crosswalk exacto: '+name)
                        mapped.append(matches[0])
                    r['local_id'],r['visitante_id'] = mapped
                year = r['anio'] if code!='nba' else r['anio']-1
                seasons = [x for x in seasonsb if x['competicion_id']==comp and x['anio_inicio']==year]
                if len(seasons)!=1:
                    raise ValueError('Temporada baloncesto ausente/ambigua')
                season = seasons[0]['id']
                variants = {sourceid,sourceid.replace('_','/')}
                enlazados={pid for pid,m in metas['horarios_baloncesto'].items()
                           if m['competicion_codigo']==code and m['id_fuente']==sourceid}
                matched = [x for x in pb if x['competicion_id']==comp and (
                    x['id'] in enlazados or x.get('source_game_id') in variants or (code in ('nba','wnba') and x.get('espn_game_id')==sourceid))]
                # Fechas ±2 SOLO con identidades exactas, misma fase y temporada.
                near = [x for x in pb if x['competicion_id']==comp and x['equipo_local_id']==r['local_id']
                    and x['equipo_visitante_id']==r['visitante_id'] and x['temporada_id']==season
                    and x['tipo_partido']==r['fase'] and abs((date.fromisoformat(x['fecha_partido'])-date.fromisoformat(r['fecha_fuente'])).days)<=2]
                if not matched and len(near)==1:
                    matched = near
                elif not matched and len(near)>1:
                    raise ValueError('Identidad próxima ambigua')
                if len(matched)>1:
                    raise ValueError('ID fuente duplicado')
                old = matched[0] if matched else None
                source = None
            if old and (not identidad(old,r,season) or old.get('valido') is not True or
                    (r['deporte']=='baloncesto' and old['tipo_partido']!=r['fase'])):
                raise ValueError('Cambio de identidad/fase o fila inválida protegida')
            results = r['resultados']
            final_old = old and ((old.get('local_total',0)>0 and old.get('visitante_total',0)>0)
                      if r['deporte']=='baloncesto' else old['estado']=='FINALIZADO')
            if final_old:
                if r['estado']!='FINALIZADO' or any(old.get(k) is not None and old.get(k)!=v for k,v in results.items()):
                    raise ValueError('Final existente protegido ante contradicción/degradación')
                results = {k:v for k,v in results.items() if old.get(k) is None}
            if old is None and not r['inicio_utc']:
                raise ValueError('Alta sin hora: no se inventa fecha canónica UTC')
            if r['deporte']=='baloncesto':
                if old:
                    pid = old['id']
                    vals = results
                else:
                    pid = str(uuid5(NAMESPACE_URL,f"AnalyticsPredict:agenda:{code}:{sourceid}"))
                    if code=='wnba':
                        # Un no-final WNBA solo vive en su catálogo de fixtures.
                        from ingesta_wnba import uid
                        pid = uid('partido',sourceid)
                    canondate = instante(r['inicio_utc']).astimezone(ZoneInfo('America/New_York')).date() if code=='nba' else date.fromisoformat(r['fecha_fuente'])
                    vals = {'id':pid,'competicion_id':comp,'temporada_id':season,
                        'equipo_local_id':r['local_id'],'equipo_visitante_id':r['visitante_id'],
                        'fecha_partido':str(canondate),'tipo_partido':r['fase'],'valido':True,
                        'fuente_datos':r['proveedor'],'source':r['proveedor'],'source_game_id':sourceid,
                        'espn_game_id':sourceid if code in ('nba','wnba') else None,
                        # El catálogo legacy exige NOT NULL; son placeholders,
                        # nunca finales. El DTO los oculta salvo FINALIZADO.
                        **{f'{l}_{q}':0 for l in ('local','visitante') for q in ('q1','q2','q3','q4','ot','total')},**results}
                if r['estado']=='FINALIZADO':
                    totals = r['resultados']
                    vals = {**vals,'ganador_id':r['local_id'] if totals['local_total']>totals['visitante_total'] else r['visitante_id'],
                            'diferencia_puntos':abs(totals['local_total']-totals['visitante_total'])}
                if code!='wnba' or r['estado']=='FINALIZADO' or old:
                    op('partidos_baloncesto',pid,old,vals,r)
                if code=='wnba':
                    from ingesta_wnba import uid
                    f = next((x for x in fixtures if x['source_game_id']==sourceid),None)
                    fxid = f['id'] if f else uid('fixture',sourceid)
                    payload = {**(f['registro'] if f else {}),**r['fixture_wnba']}
                    if f and (f['equipo_local_id'],f['equipo_visitante_id'],f['temporada_id'],f['fase'])!=(r['local_id'],r['visitante_id'],season,r['fase']):
                        raise ValueError('Cambio de identidad fixture WNBA')
                    if f and f.get('resultado_id') and f['resultado_id']!=pid:
                        raise ValueError('Fixture WNBA vinculado a otro final')
                    # No pierde corroboración oficial previa ni su fecha.
                    if f and f['registro'].get('oficial_verificado') and all(f['registro'].get(k)==payload.get(k) for k in ('inicio_utc','fecha_local','estado')):
                        payload.update({k:v for k,v in f['registro'].items() if k.startswith('oficial_')})
                    fv = {'inicio_utc':r['inicio_utc'],'fecha_local':payload['fecha_local'],
                          'precision_fecha':r['precision_fecha'],'estado':r['estado'],
                          'registro':payload,'revision_sha256':huella(payload)}
                    if r['estado']=='FINALIZADO':
                        fv['resultado_id'] = pid
                    if not f:
                        fv.update(id=fxid,competicion_id=comp,temporada_id=season,
                            equipo_local_id=r['local_id'],equipo_visitante_id=r['visitante_id'],source_game_id=sourceid,fase=r['fase'])
                    op('fixtures_wnba',fxid,f,fv,r)
                else:
                    _meta(op,metas['horarios_baloncesto'],'horarios_baloncesto',pid,r)
            else:
                if old:
                    pid = old['id']
                    vals = dict(results)
                    if not final_old:
                        # El enum legacy no tiene DEMORADO. Su estado exacto
                        # vive en metadatos; no se inventa otra transición.
                        if r['estado']!='DEMORADO':
                            vals['estado'] = r['estado']
                        if r['inicio_utc']:
                            vals['fecha_partido'] = r['inicio_utc']
                else:
                    # Sin enlace fuente, no adjudicar un partido de otro proveedor.
                    near = [x for x in pf if x['competicion_id']==comp and x['equipo_local_id']==r['local_id'] and x['equipo_visitante_id']==r['visitante_id']
                            and abs((instante(x['fecha_partido'])-instante(r['inicio_utc'])).total_seconds())<=172800]
                    if near:
                        raise ValueError('Partido próximo sin vínculo acreditado: no duplicar ni conciliar automáticamente')
                    pid = str(uuid5(NAMESPACE_URL,f"espn:soccer:{r['feed']}:{sourceid}"))
                    vals = {'id':pid,'competicion_id':comp,'temporada_id':season,
                            'equipo_local_id':r['local_id'],'equipo_visitante_id':r['visitante_id'],
                            'fecha_partido':r['inicio_utc'],'estado':r['estado'] if r['estado']!='DEMORADO' else 'PROGRAMADO','valido':True,
                            'fuente_datos':'ESPN_SOCCER','local_goles_et':None,'visitante_goles_et':None,**results}
                if r['estado']=='FINALIZADO' and not final_old:
                    h,a = r['resultados']['local_goles_total'],r['resultados']['visitante_goles_total']
                    vals.update(ganador_id=r['local_id'] if h>a else r['visitante_id'] if a>h else None,
                                diferencia_goles=abs(h-a),resultado_final=f'{h}-{a}')
                op('partidos_futbol',pid,old,vals,r)
                if not source:
                    # La PK doble se administra como inserción, con ID estable.
                    link = {'liga':r['feed'],'id_fuente':sourceid,'partido_id':pid,
                        'sha256_evento':huella({k:v for k,v in r.items() if k!='evidencia'}),
                        'observado_en':r['evidencia']['observado_en'],'evidencia':r['evidencia']}
                    op('partidos_fuente_espn_futbol',pid,None,link,r,clave='partido_id')
                _meta(op,metas['horarios_futbol'],'horarios_futbol',pid,r)
            plan['aceptados'].append({'codigo':code,'id_fuente':sourceid,'partido_id':pid,
                'estado':r['estado'],'inicio_utc':r['inicio_utc'],'precision_fecha':r['precision_fecha']})
            if len(plan['operaciones'])==n0:
                plan['sin_cambios'] += 1
        except (ValueError,KeyError,TypeError) as exc:
            del plan['operaciones'][n0:]
            claves.clear();claves.update(claves0)
            plan['incidencias'].append({'grupo':r['codigo'],'id':r['id_fuente'],'motivo':str(exc)})
    plan['sha256'] = huella(plan)
    return plan


def _meta(op, existentes, tabla, pid, r):
    # Hash semántico: una nueva observación igual no modifica filas/revisiones.
    content = {k:r[k] for k in ('codigo','proveedor','id_fuente','inicio_utc','fecha_fuente',
                'zona_origen','precision_fecha','estado','resultados')}
    old = existentes.get(pid)
    if old and old['revision_sha256']==huella(content):
        return
    if old and instante(old['observado_en'])>instante(r['evidencia']['observado_en']):
        raise ValueError('No aplicar snapshot anterior a la revisión guardada')
    val = {'partido_id':pid,'competicion_codigo':r['codigo'],'proveedor':r['proveedor'],
           'id_fuente':r['id_fuente'],'inicio_utc':r['inicio_utc'],'fecha_fuente':r['fecha_fuente'],
           'zona_origen':r['zona_origen'],'precision_fecha':r['precision_fecha'],'estado':r['estado'],
           'revision_sha256':huella(content),'observado_en':r['evidencia']['observado_en'],
           'evidencia':r['evidencia']}
    op(tabla,pid,old,val,r,clave='partido_id')


def aplicar(conn, plan):
    """El llamador posee la transacción. Antes-images bajo lock; fallo revierte todo."""
    check = {k:v for k,v in plan.items() if k!='sha256'}
    if huella(check)!=plan['sha256']:
        raise ValueError('Plan alterado')
    conn.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:agenda:incremental'))")
    grupos={}
    for op in plan['operaciones']:
        table, key = op['tabla'],op['clave']
        if table not in TABLAS or key not in ('id','partido_id'):
            raise ValueError('Operación fuera de allowlist')
        grupos.setdefault((table,key),[]).append(op['id'])
    before=leer_grupos(conn,grupos,bloquear=True)
    for op in plan['operaciones']:
        table,key=op['tabla'],op['clave']
        if before[(table,key)].get(op['id'])!=op['antes']:
            raise ValueError(f'Before-image cambió: {table}/{op["id"]}')
    # Mantiene la misma transacción y orden de FK. Pipeline reduce viajes de red,
    # no los controles: se valida cada fila después de ejecutar los triggers.
    with conn.pipeline():
        for op in plan['operaciones']:
            table,key=op['tabla'],op['clave'];vals=op['valores'];cols=list(vals)
            args=[Jsonb(v) if isinstance(v,(dict,list)) else v for v in vals.values()]
            if op['antes'] is None:
                conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),
                    sql.SQL(',').join(map(sql.Identifier,cols)),sql.SQL(',').join(sql.Placeholder() for _ in cols)),args)
            else:
                sets=[sql.SQL('{}=%s').format(sql.Identifier(k)) for k in cols]
                if table!='partidos_fuente_espn_futbol':sets.append(sql.SQL('actualizado_en=now()'))
                conn.execute(sql.SQL('UPDATE {} SET {} WHERE {}=%s').format(sql.Identifier(table),sql.SQL(',').join(sets),sql.Identifier(key)),[*args,op['id']])
    after=leer_grupos(conn,grupos)
    revisiones=[]
    for op in plan['operaciones']:
        table,key=op['tabla'],op['clave'];vals=op['valores']
        despues=after[(table,key)][op['id']]
        if any(despues.get(k)!=plano(v) for k,v in vals.items()):
            raise ValueError(f'Trigger o coerción cambió campos explícitos: {table}/{op["id"]}')
        revisiones.append(
            (uuid4(), 'wnba' if op['codigo']=='wnba' else op['deporte'], op['id'],op['codigo'],
             huella([table,op['antes'],op['valores'],op['observado_en']]),Jsonb({'tabla':table,'fila':op['antes']}),
             Jsonb({'tabla':table,'fila':despues}),op['observado_en'],Jsonb(op['procedencia'])))
    if revisiones:
        with conn.pipeline(),conn.cursor() as cur:
            cur.executemany('''INSERT INTO revisiones_agenda(id,deporte,partido_id,competicion_codigo,
                revision_sha256,antes,despues,observado_en,procedencia)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',revisiones)
    return len(plan['operaciones'])


def leer_grupos(conn,grupos,*,bloquear=False):
    """Lectura acotada por IDs con un roundtrip por lote; no consulta la red HTTP."""
    cursors={}
    try:
        with conn.pipeline():
            for (table,key),ids in sorted(grupos.items()):
                if table not in TABLAS or key not in ('id','partido_id'):
                    raise ValueError('Grupo fuera de allowlist')
                cur=conn.cursor(row_factory=dict_row);cursors[(table,key)]=cur
                cur.execute(sql.SQL('SELECT * FROM {} WHERE {}=ANY(%s::uuid[]) ORDER BY {}').format(
                    sql.Identifier(table),sql.Identifier(key),sql.Identifier(key))+
                    (sql.SQL(' FOR UPDATE') if bloquear else sql.SQL('')),(ids,))
            return {tk:{str(r[tk[1]]):plano(r) for r in cur.fetchall()} for tk,cur in cursors.items()}
    finally:
        for cur in cursors.values():cur.close()
