"""Conecta snapshots ESPN con catálogo canónico solo con manifiesto acreditado.

Sin --aplicar: SELECT read-only y validación completa, sin DDL/DML/proveedor.
Las equivalencias son explícitas; no se usa distancia, similitud ni fuzzy matching.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

from scripts.ingerir_espn_soccer_capturas import validar_lote, _digest

CODIGOS = {'eng.1':'ENG_PREMIER','esp.1':'ESP_LALIGA','ita.1':'ITA_SERIEA',
           'ger.1':'GER_BUNDESLIGA','fra.1':'FRA_LIGUE1'}
BACKEND=Path(__file__).resolve().parents[1]
ESTADOS={'STATUS_SCHEDULED':'PROGRAMADO','STATUS_ABANDONED':'SUSPENDIDO',
         'STATUS_POSTPONED':'POSPUESTO','STATUS_CANCELED':'CANCELADO'}


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
        UUID(e['equipo_id'])
        if ident in equipos or e['equipo_id'] in canonicos:
            raise ValueError('Colisión de identidades')
        equipos[ident]=e
        canonicos.add(e['equipo_id'])
    temporadas=manifiesto.get('temporadas',{})
    for liga,t in temporadas.items():
        if liga not in CODIGOS or type(t.get('anio')) is not int or not t.get('evidencia'):
            raise ValueError('Temporada sin evidencia')
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
                    if m is None or m['liga']!=liga or ev[lado+'_nombre']!=m['nombre_espn']:
                        raise ValueError('Evento sin mapeo exacto revisado')
                if not ev['final_acreditado'] and ev['estado_fuente'] not in ESTADOS:
                    raise ValueError('Estado no final requiere adaptación explícita')
                clave=(liga,ev['id_fuente'])
                revision={**ev,'observado_en':lote['observado_en']}
                if clave not in eventos or revision['observado_en']>eventos[clave]['observado_en']:
                    eventos[clave]=revision
        return {'equipos':equipos,'temporadas':temporadas,'competiciones':comps,'eventos':list(eventos.values())}


def aplicar_plan(conn, plan):
    """Unidad atómica. Nunca enlaza filas existentes por nombre/fecha aproximados."""
    nuevos=actualizados=0
    with conn.transaction(),conn.cursor(row_factory=dict_row) as c:
        for liga,t in plan['temporadas'].items():
            comp=plan['competiciones'][CODIGOS[liga]]
            existentes=c.execute('SELECT id FROM temporadas_futbol WHERE competicion_id=%s AND anio_inicio=%s AND anio_fin=%s',
                                (comp['id'],t['anio'],t['anio']+1)).fetchall()
            if len(existentes)>1:
                raise ValueError('Temporada ambigua')
            tid=existentes[0]['id'] if existentes else uuid5(NAMESPACE_URL,f"espn:soccer:{liga}:season:{t['anio']}")
            if not existentes:
                c.execute('INSERT INTO temporadas_futbol(id,competicion_id,nombre,anio_inicio,anio_fin,activa,finalizada) VALUES(%s,%s,%s,%s,%s,true,false)',
                          (tid,comp['id'],t['nombre'],t['anio'],t['anio']+1))
            previo=c.execute('SELECT temporada_id FROM temporadas_fuente_espn_futbol WHERE liga=%s AND anio=%s',(liga,t['anio'])).fetchone()
            if previo and previo['temporada_id']!=tid:
                raise ValueError('Cambio de identidad de temporada')
            c.execute('INSERT INTO temporadas_fuente_espn_futbol VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                      (liga,t['anio'],tid,Jsonb(t['evidencia'])))
            t['id']=tid
        for e in plan['equipos'].values():
            comp=plan['competiciones'][CODIGOS[e['liga']]]
            existe=c.execute('SELECT id FROM equipos_futbol WHERE id=%s',(e['equipo_id'],)).fetchone()
            if not existe:
                c.execute('INSERT INTO equipos_futbol(id,nombre,nombre_corto,pais_id,competicion_principal_id,activo) VALUES(%s,%s,%s,%s,%s,true)',
                          (e['equipo_id'],e['nombre_canonico'],e['nombre_espn'],comp['pais_id'],comp['id']))
            else:
                c.execute('UPDATE equipos_futbol SET competicion_principal_id=%s WHERE id=%s AND competicion_principal_id IS DISTINCT FROM %s',
                          (comp['id'],e['equipo_id'],comp['id']))
            previo=c.execute('SELECT equipo_id FROM equipos_fuente_espn_futbol WHERE id_fuente=%s',(e['id_fuente'],)).fetchone()
            if previo and str(previo['equipo_id'])!=e['equipo_id']:
                raise ValueError('Cambio de identidad de club')
            c.execute('INSERT INTO equipos_fuente_espn_futbol(id_fuente,equipo_id,evidencia) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',
                      (e['id_fuente'],e['equipo_id'],Jsonb(e)))
        for ev in plan['eventos']:
            local=plan['equipos'][ev['local_id_fuente']]['equipo_id']
            visitante=plan['equipos'][ev['visitante_id_fuente']]['equipo_id']
            comp=plan['competiciones'][CODIGOS[ev['liga']]]['id']
            temporada=plan['temporadas'][ev['liga']]['id']
            anterior=c.execute('SELECT * FROM partidos_fuente_espn_futbol WHERE liga=%s AND id_fuente=%s',
                               (ev['liga'],ev['id_fuente'])).fetchone()
            digest=_digest(ev)
            if anterior:
                if anterior['sha256_evento'].strip()==digest or anterior['observado_en']>=datetime.fromisoformat(ev['observado_en']):
                    continue
                pid=anterior['partido_id']
                ident=c.execute('SELECT equipo_local_id,equipo_visitante_id,competicion_id,fuente_datos,estado FROM partidos_futbol WHERE id=%s',(pid,)).fetchone()
                if (str(ident['equipo_local_id']),str(ident['equipo_visitante_id']),ident['competicion_id'],ident['fuente_datos'])!=(local,visitante,comp,'ESPN_SOCCER'):
                    raise ValueError('Cambio de identidad de partido o fuente')
                if ident['estado']=='FINALIZADO' and not ev['final_acreditado']:
                    raise ValueError('No degradar un final acreditado sin reconciliación explícita')
            else:
                if c.execute("SELECT id FROM partidos_futbol WHERE competicion_id=%s AND equipo_local_id=%s AND equipo_visitante_id=%s AND fecha_partido BETWEEN %s::timestamptz-interval '2 days' AND %s::timestamptz+interval '2 days'",
                             (comp,local,visitante,ev['inicio_utc'],ev['inicio_utc'])).fetchone():
                    raise ValueError('Posible partido duplicado entre fuentes: revisar identidad')
                pid=uuid5(NAMESPACE_URL,f"espn:soccer:{ev['liga']}:{ev['id_fuente']}")
                c.execute('INSERT INTO partidos_futbol(id,competicion_id,temporada_id,equipo_local_id,equipo_visitante_id,fecha_partido,fuente_datos,local_goles_et,visitante_goles_et) VALUES(%s,%s,%s,%s,%s,%s,%s,NULL,NULL)',
                          (pid,comp,temporada,local,visitante,ev['inicio_utc'],'ESPN_SOCCER'))
            final=ev['final_acreditado']; gl=ev['local_goles']; gv=ev['visitante_goles']
            c.execute('''UPDATE partidos_futbol SET fecha_partido=%s,estado=%s,
                local_goles_total=%s,visitante_goles_total=%s,
                local_corners_total=%s,visitante_corners_total=%s,
                local_disparos_total=%s,visitante_disparos_total=%s,
                local_disparos_arco=%s,visitante_disparos_arco=%s,
                ganador_id=%s,diferencia_goles=%s,
                datos_corners_completos=%s,datos_disparos_completos=%s,
                datos_completos=false,valido=true,resultado_final=%s,url_referencia=%s,actualizado_en=now() WHERE id=%s''',
                (ev['inicio_utc'],'FINALIZADO' if final else ESTADOS[ev['estado_fuente']],gl,gv,
                 ev.get('local_corners'),ev.get('visitante_corners'),
                 ev.get('local_disparos'),ev.get('visitante_disparos'),
                 ev.get('local_disparos_arco'),ev.get('visitante_disparos_arco'),
                 local if final and gl>gv else visitante if final and gv>gl else None,
                 gl-gv if final else None,ev.get('corners_completos',False),ev.get('disparos_completos',False),
                 f'{gl}-{gv}' if final else None,
                 f"https://www.espn.com/soccer/match/_/gameId/{ev['id_fuente']}",pid))
            c.execute('''INSERT INTO partidos_fuente_espn_futbol VALUES(%s,%s,%s,%s,%s,%s)
                ON CONFLICT(liga,id_fuente) DO UPDATE SET sha256_evento=EXCLUDED.sha256_evento,
                observado_en=EXCLUDED.observado_en,evidencia=EXCLUDED.evidencia''',
                (ev['liga'],ev['id_fuente'],pid,digest,ev['observado_en'],Jsonb(ev)))
            nuevos+=not bool(anterior); actualizados+=bool(anterior)
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
