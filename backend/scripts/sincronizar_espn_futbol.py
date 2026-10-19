"""Conecta snapshots ESPN con catálogo canónico solo con manifiesto acreditado.

Sin --aplicar: SELECT read-only y validación completa, sin DDL/DML/proveedor.
Las equivalencias son explícitas; no se usa distancia, similitud ni fuzzy matching.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

from scripts.ingerir_espn_soccer_capturas import validar_lote, _digest, _sha256
from servicios.finales_espn_futbol import CAMPOS_PERIODOS, validar_periodos_final, validar_desempate_final

CODIGOS = {'eng.1':'ENG_PREMIER','esp.1':'ESP_LALIGA','ita.1':'ITA_SERIEA',
           'ger.1':'GER_BUNDESLIGA','fra.1':'FRA_LIGUE1', 'eng.fa':'ENG_FACUP',
           'esp.copa_del_rey':'ESP_COPA', 'ita.coppa_italia':'ITA_COPPA',
           'fra.coupe_de_france':'FRA_COUPE', 'uefa.champions':'EUR_CHAMPIONS',
           'uefa.europa':'EUR_EUROPA', 'uefa.europa.conf':'EUR_CONFERENCE'}
BACKEND=Path(__file__).resolve().parents[1]
ESTADOS={'STATUS_SCHEDULED':'PROGRAMADO','STATUS_ABANDONED':'SUSPENDIDO',
         'STATUS_POSTPONED':'POSPUESTO','STATUS_CANCELED':'CANCELADO'}


def huella_fila(fila):
    return hashlib.sha256(json.dumps(dict(fila), sort_keys=True, separators=(',', ':'),
        default=lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x)).encode()).hexdigest()


def validar_manifiesto(manifiesto):
    if not isinstance(manifiesto,dict) or manifiesto.get('version')!=1:
        raise ValueError('Manifiesto sin versión acreditada')
    equipos={}
    canonicos=set()
    for e in manifiesto.get('equipos',[]):
        if (e.get('liga') not in CODIGOS or not str(e.get('id_fuente','')).isdigit()
                or not e.get('nombre_espn') or not e.get('nombre_canonico')
                or not e.get('slug') or not e.get('evidencia')
                or e.get('metodo') not in {'NOMBRE_EXACTO','ALIAS_REVISADO','ALTA_ROSTER_ESPN'}):
            raise ValueError('Identidad o evidencia incompleta')
        ident=str(e['id_fuente'])
        ligas=e.get('ligas',[e['liga']])
        if (not isinstance(ligas,list) or not ligas or e['liga'] not in ligas
                or any(l not in CODIGOS for l in ligas)):
            raise ValueError('Afiliaciones de fuente no acreditadas')
        UUID(e['equipo_id'])
        if ident in equipos or e['equipo_id'] in canonicos:
            raise ValueError('Colisión de identidades')
        equipos[ident]=e
        canonicos.add(e['equipo_id'])
    temporadas=manifiesto.get('temporadas',{})
    for liga,t in temporadas.items():
        if liga not in CODIGOS or type(t.get('anio')) is not int or not t.get('evidencia'):
            raise ValueError('Temporada sin evidencia')
        if 'activa' in t and type(t['activa']) is not bool:
            raise ValueError('Estado de temporada ambiguo')
        if t.get('nombre')!=f"{t['anio']}-{t['anio']+1}":
            raise ValueError('Temporada incompatible')
    if not equipos or not temporadas:
        raise ValueError('Manifiesto vacío')
    return equipos,temporadas


def planificar(conn, manifiesto, lotes):
    equipos,temporadas=validar_manifiesto(manifiesto)
    lotes=[validar_lote(l) for l in lotes]
    with conn.cursor(row_factory=dict_row) as c:
        clubes={str(e['id']):e for e in c.execute('SELECT id,nombre FROM equipos_futbol')}
        comps={e['codigo']:e for e in c.execute('SELECT id,codigo,pais_id FROM competiciones_futbol')}
        for e in equipos.values():
            existente=clubes.get(e['equipo_id'])
            if existente and existente['nombre']!=e['nombre_canonico']:
                raise ValueError('El catálogo cambió desde la revisión')
            if not existente and e['metodo']!='ALTA_ROSTER_ESPN':
                raise ValueError('Equipo canónico acreditado inexistente')
            if not existente and any(x['nombre'].casefold()==e['nombre_canonico'].casefold() for x in clubes.values()):
                raise ValueError('Posible club duplicado: requiere revisión explícita')
        conciliaciones={}
        for revision in manifiesto.get('conciliaciones',[]):
            clave=(revision.get('liga'),revision.get('id_fuente'))
            if (clave in conciliaciones or clave[0] not in CODIGOS
                    or not revision.get('justificacion')
                    or len(revision.get('huella_antes',''))!=64):
                raise ValueError('Conciliación sin evidencia o repetida')
            UUID(revision['partido_id'])
            conciliaciones[clave]=revision
        eventos={}
        for lote in lotes:
            liga=lote['liga']; temporada=temporadas.get(liga)
            if temporada is None or CODIGOS[liga] not in comps:
                raise ValueError('Competición/temporada no acreditada')
            for ev in lote['eventos']:
                fecha=datetime.fromisoformat(ev['inicio_utc'])
                anio=temporada['anio']
                if not datetime(anio,6,1,tzinfo=timezone.utc)<=fecha<datetime(anio+1,7,1,tzinfo=timezone.utc):
                    raise ValueError('Evento fuera de temporada acreditada')
                for lado in ('local','visitante'):
                    m=equipos.get(ev[lado+'_id_fuente'])
                    if m is None or liga not in m.get('ligas',[m['liga']]) or ev[lado+'_nombre']!=m['nombre_espn']:
                        raise ValueError('Evento sin mapeo exacto revisado')
                if ev.get('periodos') is not None:
                    if not ev['final_acreditado'] or not _sha256(ev.get('sha256_boxscore')):
                        raise ValueError('Periodos sin final o evidencia de summary')
                    validar_periodos_final(ev['periodos'],ev)
                if ev.get('desempate') is not None:
                    if not ev['final_acreditado'] or not _sha256(ev.get('sha256_boxscore')):
                        raise ValueError('Tanda sin final o evidencia de summary')
                    validar_desempate_final(ev['desempate'],ev)
                    if ev.get('periodos') is not None and any(
                            ev['periodos']['campos'][k]!=v for k,v in ev['desempate']['campos'].items()):
                        raise ValueError('Tanda y periodos contradictorios')
                if not ev['final_acreditado'] and ev['estado_fuente'] not in ESTADOS:
                    raise ValueError('Estado no final requiere adaptación explícita')
                clave=(liga,ev['id_fuente'])
                revision={**ev,'observado_en':lote['observado_en']}
                if clave in conciliaciones:
                    revision['conciliacion_previa']=conciliaciones[clave]
                if clave not in eventos or revision['observado_en']>eventos[clave]['observado_en']:
                    eventos[clave]=revision
        usados={e[l+'_id_fuente'] for e in eventos.values() for l in ('local','visitante')}
        ligas_usadas={e['liga'] for e in eventos.values()}
        return {'equipos':{k:v for k,v in equipos.items() if k in usados},
                'temporadas':{k:v for k,v in temporadas.items() if k in ligas_usadas},
                'competiciones':comps,'eventos':list(eventos.values()),'conciliaciones':conciliaciones}


def aplicar_plan(conn, plan):
    """Unidad atómica. Nunca enlaza filas existentes por nombre/fecha aproximados."""
    nuevos=actualizados=0
    with conn.transaction(),conn.cursor(row_factory=dict_row) as c:
        c.execute("SELECT pg_advisory_xact_lock(hashtext('analyticspredict_espn_futbol_canonico'))")
        for liga,t in plan['temporadas'].items():
            comp=plan['competiciones'][CODIGOS[liga]]
            existentes=c.execute('SELECT id FROM temporadas_futbol WHERE competicion_id=%s AND anio_inicio=%s AND anio_fin=%s',
                                (comp['id'],t['anio'],t['anio']+1)).fetchall()
            if len(existentes)>1:
                raise ValueError('Temporada ambigua')
            tid=existentes[0]['id'] if existentes else uuid5(NAMESPACE_URL,f"espn:soccer:{liga}:season:{t['anio']}")
            if not existentes:
                activa=t.get('activa',True)
                c.execute('INSERT INTO temporadas_futbol(id,competicion_id,nombre,anio_inicio,anio_fin,activa,finalizada) VALUES(%s,%s,%s,%s,%s,%s,%s)',
                          (tid,comp['id'],t['nombre'],t['anio'],t['anio']+1,activa,not activa))
            elif 'activa' in t:
                c.execute('UPDATE temporadas_futbol SET activa=%s,finalizada=%s WHERE id=%s AND (activa IS DISTINCT FROM %s OR finalizada IS DISTINCT FROM %s)',
                          (t['activa'],not t['activa'],tid,t['activa'],not t['activa']))
            previo=c.execute('SELECT temporada_id FROM temporadas_fuente_espn_futbol WHERE liga=%s AND anio=%s',(liga,t['anio'])).fetchone()
            if previo and previo['temporada_id']!=tid:
                raise ValueError('Cambio de identidad de temporada')
            c.execute('INSERT INTO temporadas_fuente_espn_futbol VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                      (liga,t['anio'],tid,Jsonb(t['evidencia'])))
            t['id']=tid
        ids_clubes=[e['equipo_id'] for e in plan['equipos'].values()]
        ids_fuente=list(plan['equipos'])
        clubes_existentes={str(r['id']) for r in c.execute(
            'SELECT id FROM equipos_futbol WHERE id=ANY(%s::uuid[])',(ids_clubes,)).fetchall()}
        enlaces_clubes={r['id_fuente']:str(r['equipo_id']) for r in c.execute(
            'SELECT id_fuente,equipo_id FROM equipos_fuente_espn_futbol WHERE id_fuente=ANY(%s) FOR SHARE',
            (ids_fuente,)).fetchall()}
        for e in plan['equipos'].values():
            comp=plan['competiciones'][CODIGOS[e['liga']]]
            if e['equipo_id'] not in clubes_existentes:
                c.execute('INSERT INTO equipos_futbol(id,nombre,nombre_corto,pais_id,competicion_principal_id,activo) VALUES(%s,%s,%s,%s,%s,true)',
                          (e['equipo_id'],e['nombre_canonico'],e['nombre_espn'],
                           e['pais_id'] if 'pais_id' in e else comp['pais_id'],
                           e['competicion_principal_id'] if 'competicion_principal_id' in e else comp['id']))
            # Un partido histórico acredita su competición, no la afiliación
            # ACTUAL del club. Ascensos/descensos se gestionan por separado.
            # Conservar incluso NULL: un vínculo ESPN no autoriza completar catálogo.
            previo=enlaces_clubes.get(e['id_fuente'])
            if previo and previo!=e['equipo_id']:
                raise ValueError('Cambio de identidad de club')
            if not previo:
                c.execute('INSERT INTO equipos_fuente_espn_futbol(id_fuente,equipo_id,evidencia) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING RETURNING equipo_id',
                          (e['id_fuente'],e['equipo_id'],Jsonb(e)))
                if c.fetchone() is None:
                    actual=c.execute('SELECT equipo_id FROM equipos_fuente_espn_futbol WHERE id_fuente=%s',(e['id_fuente'],)).fetchone()
                    if actual is None or str(actual['equipo_id'])!=e['equipo_id']:
                        raise ValueError('Vínculo de club cambió concurrentemente')
        ligas=list({e['liga'] for e in plan['eventos']})
        ids_eventos=[e['id_fuente'] for e in plan['eventos']]
        enlaces_partidos={(r['liga'],r['id_fuente']):r for r in c.execute(
            'SELECT * FROM partidos_fuente_espn_futbol WHERE liga=ANY(%s) AND id_fuente=ANY(%s) FOR UPDATE',
            (ligas,ids_eventos)).fetchall()}
        for ev in plan['eventos']:
            local=plan['equipos'][ev['local_id_fuente']]['equipo_id']
            visitante=plan['equipos'][ev['visitante_id_fuente']]['equipo_id']
            comp=plan['competiciones'][CODIGOS[ev['liga']]]['id']
            temporada=plan['temporadas'][ev['liga']]['id']
            anterior=enlaces_partidos.get((ev['liga'],ev['id_fuente']))
            digest=_digest(ev)
            if anterior:
                if anterior['sha256_evento'].strip()==digest or anterior['observado_en']>=datetime.fromisoformat(ev['observado_en']):
                    continue
                pid=anterior['partido_id']
                ident=c.execute('SELECT equipo_local_id,equipo_visitante_id,competicion_id,fuente_datos,estado FROM partidos_futbol WHERE id=%s FOR UPDATE',(pid,)).fetchone()
                if (str(ident['equipo_local_id']),str(ident['equipo_visitante_id']),ident['competicion_id'],ident['fuente_datos'])!=(local,visitante,comp,'ESPN_SOCCER'):
                    raise ValueError('Cambio de identidad de partido o fuente')
                if ident['estado']=='FINALIZADO' and not ev['final_acreditado']:
                    raise ValueError('No degradar un final acreditado sin reconciliación explícita')
            else:
                revision=plan.get('conciliaciones',{}).get((ev['liga'],ev['id_fuente']))
                if revision:
                    fila=c.execute('SELECT * FROM partidos_futbol WHERE id=%s FOR UPDATE',(revision['partido_id'],)).fetchone()
                    if (not fila or huella_fila(fila)!=revision['huella_antes']
                            or (str(fila['equipo_local_id']),str(fila['equipo_visitante_id']),str(fila['competicion_id']),str(fila['temporada_id']))
                            !=(local,visitante,str(comp),str(temporada))
                            or not ev['final_acreditado']):
                        raise ValueError('Conciliación cambió desde revisión o identidad incompatible')
                    if fila['estado']=='FINALIZADO':
                        mismos=(fila['local_goles_total'],fila['visitante_goles_total'])==(ev['local_goles'],ev['visitante_goles'])
                        periodos=ev.get('periodos',{}).get('campos',{})
                        complemento_et=(periodos.get('hubo_tiempo_extra') is True and all(
                            fila[l+'_goles_total']==periodos.get(l+'_goles_1t',-1)+periodos.get(l+'_goles_2t',-1)
                            for l in ('local','visitante')))
                        if (revision.get('tipo')!='FINAL_VALIDADO_EXPLICITAMENTE'
                                or not _sha256(ev.get('sha256_boxscore')) or not (mismos or complemento_et)):
                            raise ValueError('No sobrescribir un final sin conciliación de marcador/ET explícita')
                    pid=fila['id']
                elif c.execute("SELECT id FROM partidos_futbol WHERE competicion_id=%s AND equipo_local_id=%s AND equipo_visitante_id=%s AND fecha_partido BETWEEN %s::timestamptz-interval '2 days' AND %s::timestamptz+interval '2 days'",
                             (comp,local,visitante,ev['inicio_utc'],ev['inicio_utc'])).fetchone():
                    raise ValueError('Posible partido duplicado entre fuentes: revisar identidad')
                else:
                    pid=uuid5(NAMESPACE_URL,f"espn:soccer:{ev['liga']}:{ev['id_fuente']}")
                    c.execute('INSERT INTO partidos_futbol(id,competicion_id,temporada_id,equipo_local_id,equipo_visitante_id,fecha_partido,fuente_datos,local_goles_et,visitante_goles_et) VALUES(%s,%s,%s,%s,%s,%s,%s,NULL,NULL)',
                          (pid,comp,temporada,local,visitante,ev['inicio_utc'],'ESPN_SOCCER'))
            final=ev['final_acreditado']; gl=ev['local_goles']; gv=ev['visitante_goles']
            c.execute('''UPDATE partidos_futbol SET fecha_partido=%s,estado=%s,
                local_goles_total=%s,visitante_goles_total=%s,
                local_corners_total=COALESCE(%s,local_corners_total),visitante_corners_total=COALESCE(%s,visitante_corners_total),
                local_disparos_total=COALESCE(%s,local_disparos_total),visitante_disparos_total=COALESCE(%s,visitante_disparos_total),
                local_disparos_arco=COALESCE(%s,local_disparos_arco),visitante_disparos_arco=COALESCE(%s,visitante_disparos_arco),
                ganador_id=%s,diferencia_goles=%s,
                datos_corners_completos=(%s OR COALESCE(datos_corners_completos,false)),datos_disparos_completos=(%s OR COALESCE(datos_disparos_completos,false)),
                datos_completos=false,valido=true,resultado_final=%s,url_referencia=%s,fuente_datos='ESPN_SOCCER',actualizado_en=now() WHERE id=%s''',
                (ev['inicio_utc'],'FINALIZADO' if final else ESTADOS[ev['estado_fuente']],gl,gv,
                 ev.get('local_corners'),ev.get('visitante_corners'),
                 ev.get('local_disparos'),ev.get('visitante_disparos'),
                 ev.get('local_disparos_arco'),ev.get('visitante_disparos_arco'),
                 local if final and gl>gv else visitante if final and gv>gl else None,
                 gl-gv if final else None,ev.get('corners_completos',False),ev.get('disparos_completos',False),
                 f'{gl}-{gv}' if final else None,
                 f"https://www.espn.com/soccer/match/_/gameId/{ev['id_fuente']}",pid))
            if ev.get('periodos') is not None:
                campos=ev['periodos']['campos']
                ganador=ev['periodos']['ganador']
                c.execute('UPDATE partidos_futbol SET '+','.join(k+'=%s' for k in CAMPOS_PERIODOS)
                    +',ganador_id=%s WHERE id=%s',
                    [*(campos[k] for k in CAMPOS_PERIODOS),local if ganador=='local' else visitante if ganador=='visitante' else None,pid])
            if ev.get('desempate') is not None:
                tanda=ev['desempate']['campos']
                c.execute('UPDATE partidos_futbol SET local_penales=%s,visitante_penales=%s,hubo_penales=true'
                    + (',hubo_tiempo_extra=NULL' if ev.get('periodos') is None else '')+' WHERE id=%s',
                    (tanda['local_penales'],tanda['visitante_penales'],pid))
            c.execute('''INSERT INTO partidos_fuente_espn_futbol VALUES(%s,%s,%s,%s,%s,%s)
                ON CONFLICT(liga,id_fuente) DO UPDATE SET sha256_evento=EXCLUDED.sha256_evento,
                observado_en=EXCLUDED.observado_en,evidencia=EXCLUDED.evidencia
                WHERE partidos_fuente_espn_futbol.partido_id=EXCLUDED.partido_id
                RETURNING partido_id''',
                (ev['liga'],ev['id_fuente'],pid,digest,ev['observado_en'],Jsonb(ev)))
            if c.fetchone() is None:
                raise ValueError('Vínculo de partido cambió concurrentemente')
            conciliado=not anterior and (ev['liga'],ev['id_fuente']) in plan.get('conciliaciones',{})
            nuevos+=not bool(anterior) and not conciliado; actualizados+=bool(anterior) or conciliado
    return {'insertados':nuevos,'actualizados':actualizados,'eventos':len(plan['eventos'])}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifiesto',type=Path,required=True)
    p.add_argument('--archivo',type=Path,action='append',required=True)
    p.add_argument('--aplicar',action='store_true')
    args=p.parse_args()
    manifest=json.loads(args.manifiesto.read_text())
    lotes=[json.loads(path.read_text()) for path in args.archivo]
    load_dotenv(BACKEND/'.env',override=False)
    with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=8) as conn:
        if not args.aplicar:
            conn.execute('SET TRANSACTION READ ONLY')
        plan=planificar(conn,manifest,lotes)
        print(json.dumps({'equipos':len(plan['equipos']),'eventos':len(plan['eventos']),'modo':'aplicar' if args.aplicar else 'dry-run'}))
        if args.aplicar:
            print(json.dumps(aplicar_plan(conn,plan)))


if __name__=='__main__':
    main()
