#!/usr/bin/env python3
"""Sincronización local NBA/Euroliga/fútbol (2 meses) y WNBA (3).

Por defecto sólo prepara un plan READ ONLY. --aplicar exige un respaldo fresco.
--migrar instala metadatos aditivos dentro de la transacción respaldada.
No entrena, activa modelos, registra pronósticos ni toca apuestas.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
import psycopg
from psycopg.types.json import Jsonb

from servicios.fuentes_agenda import BOGOTA, recopilar, normalizar, meses
from servicios.sincronizacion_agendas import planificar, aplicar, MIGRACION, existe
from servicios.operacion_agendas import directorio_estado, exclusion, respaldar
from servicios.transporte_agenda import guardar


def resumen(plan,hoy):
    grupos=set(r['grupo'] for r in plan['fuentes']) | {r.get('grupo') for r in plan['incidencias']}
    cobertura=[]
    for code in sorted(x for x in grupos if x):
        code='euroleague' if code=='euroliga' else code
        rows=[r for r in plan['aceptados'] if r['codigo']==code]
        futuros=[r for r in rows if r['inicio_utc'] and datetime.fromisoformat(r['inicio_utc']).astimezone(BOGOTA).date()>=hoy]
        problemas=[r for r in plan['incidencias'] if r.get('grupo') in (code,'euroliga' if code=='euroleague' else code)]
        cobertura.append({'competicion':code,'desde':str(hoy),'hasta_solicitado':str(meses(hoy,3 if code=='wnba' else 2)),
            'eventos_aceptados':len(rows),'futuros_con_hora':len(futuros),
            'ultimo_inicio_publicado':max((r['inicio_utc'] for r in futuros),default=None),
            'incidencias':len(problemas),'oficial_integra':False})
    return {'operaciones':len(plan['operaciones']),'por_tabla':dict(Counter(r['tabla'] for r in plan['operaciones'])),
            'sin_cambios':plan['sin_cambios'],'incidencias':len(plan['incidencias']),
            'cobertura':cobertura,'plan_sha256':plan['sha256'],
            'limite':'Ventanas consultadas no certifican publicación íntegra. Identidades, horas y ET/tanda no acreditados quedan en incidencias; no se inventan partidos.'}


def ejecutar(a):
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    raiz=a.estado or directorio_estado()
    with exclusion(raiz):
        iniciado=datetime.now(timezone.utc)
        hoy=iniciado.astimezone(BOGOTA).date()
        state=raiz/'estado.json'
        if state.exists() and not a.fuentes:
            prev=json.loads(state.read_text())
            if prev.get('estado') in ('COMPLETO','PARCIAL') and prev.get('iniciado_en') and (iniciado-datetime.fromisoformat(prev['iniciado_en'])).total_seconds()<1800:
                print('Fuentes verificadas hace menos de 30 minutos; no se repiten consultas.')
                return 0
        run=raiz/'runs'/iniciado.strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True,mode=0o700)
        estado={'estado':'EN_CURSO','iniciado_en':iniciado.isoformat(),'directorio':str(run)}
        guardar(state,estado)
        try:
            sources=json.loads(a.fuentes.read_text()) if a.fuentes else recopilar(raiz/'cache',run/'fuentes.json',hoy)
            # Replay operativo sólo de la fecha declarada: no afirmar ventana
            # móvil nueva con una captura antigua. Los ensayos tienen otro CLI.
            if sources.get('fecha_cot') and sources['fecha_cot']!=str(hoy):
                raise ValueError('Fuentes de otro día: reanudar con la ventana real')
            rows,issues,proof=normalizar(sources,hoy)
            with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=8) as c:
                c.read_only=True
                c.execute("SET LOCAL statement_timeout='30s'")
                plan=planificar(c,rows,issues,proof,hoy);c.rollback()
            guardar(run/'plan.json',plan)
            info=resumen(plan,hoy)
            ciclo='ERROR' if not proof else 'PARCIAL' if plan['incidencias'] else 'COMPLETO'
            if a.aplicar:
                # También respalda la primera migración y los cambios de metadatos.
                backup=respaldar(os.environ['DATABASE_URL'],run/'respaldo.dump') if plan['operaciones'] or a.migrar else None
                with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=8) as c:
                    c.execute("SET LOCAL lock_timeout='5s'")
                    c.execute("SET LOCAL statement_timeout='60s'")
                    if a.migrar:
                        c.execute(MIGRACION.read_text())
                    if not existe(c,'sincronizaciones_agenda'):
                        raise ValueError('Falta migración aditiva: ensayar y ejecutar --migrar')
                    aplicar(c,plan)
                    info['respaldo']=backup
                    # Recibo PRE-COMMIT y ledger en la misma transacción.
                    guardar(run/'precommit.json',{'plan_sha256':plan['sha256'],'respaldo':backup})
                    c.execute('INSERT INTO sincronizaciones_agenda VALUES(%s,%s,%s,%s,%s)',
                        (uuid4(),iniciado,datetime.now(timezone.utc),ciclo,Jsonb(info)))
                    c.commit()
                guardar(run/'APLICACION_CONFIRMADA.json',{'plan_sha256':plan['sha256'],'confirmado_en':datetime.now(timezone.utc).isoformat()})
                # Idempotencia sólo de filas deportivas/metadatos; el ledger de
                # verificaciones registra cada ciclo, incluso sin modificaciones.
                with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=8) as c:
                    c.read_only=True
                    segundo=planificar(c,rows,issues,proof,hoy);c.rollback()
                guardar(run/'postflight.json',segundo)
                if segundo['operaciones']:
                    raise RuntimeError('Commit confirmado, postflight no idempotente: revisar recibo; no reaplicar')
            terminado=datetime.now(timezone.utc).isoformat()
            guardar(state,{**estado,**info,'estado':ciclo if a.aplicar else 'PLAN_SIN_APLICAR',
                'terminado_en':terminado,'fuentes_verificadas_en':max((p['observado_en'] for p in proof),default=None),
                'cambio_guardado_en':terminado if a.aplicar and plan['operaciones'] else None})
            print(json.dumps(info,ensure_ascii=False))
            return 1 if ciclo=='ERROR' else 0
        except Exception as exc:
            guardar(state,{**estado,'estado':'ERROR','terminado_en':datetime.now(timezone.utc).isoformat(),
                'tipo':type(exc).__name__,'detalle':'No se completó el ciclo. Revisar plan y recibo de commit antes de reanudar; datos previos no se eliminan.'})
            # No imprime excepciones de libpq ni entorno.
            print(type(exc).__name__+': sincronización incompleta; ver evidencia local',file=sys.stderr)
            return 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--aplicar',action='store_true');p.add_argument('--migrar',action='store_true')
    p.add_argument('--fuentes',type=Path);p.add_argument('--estado',type=Path)
    a=p.parse_args()
    if a.migrar and not a.aplicar:
        p.error('--migrar requiere --aplicar')
    return ejecutar(a)


if __name__=='__main__':
    raise SystemExit(main())
