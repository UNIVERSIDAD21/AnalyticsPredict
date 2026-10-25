#!/usr/bin/env python3
"""Carga local WNBA: validar (sin BD), ensayar (rollback), aplicar o verificar.

El ensayo guarda pg_dump recuperable y prueba una segunda carga sin duplicados.
Aplicar exige el ensayo y su backup íntegros, y conserva el baseline de WNBA.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from dotenv import load_dotenv
from ingesta_wnba import MIGRACION, _filas, digest, exigir, huella, importar, leer_lote, resumen, instante


def guardar(path, value):
    raw = (json.dumps(value, default=str, ensure_ascii=False, indent=2)+'\n').encode()
    tmp = path.with_suffix('.tmp')
    with tmp.open('xb') as f:
        os.chmod(tmp, 0o600)
        f.write(raw); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)


def respaldo(url, root):
    binary = shutil.which('pg_dump')
    exigir(binary, 'pg_dump no encontrado en PATH; no se escribe sin respaldo')
    path = root/'respaldo_previo.dump'
    exigir(not path.exists(), 'Respaldo ya existente; utilizar otro directorio de operación')
    env = os.environ.copy()
    # Credencial solo en el entorno del proceso hijo; nunca en argv ni reportes.
    for k,v in conninfo_to_dict(url).items():
        exigir(k in {'host','port','dbname','user','password','sslmode','channel_binding','connect_timeout'},
               'Opción de conexión no soportada por el respaldo')
        env['PG'+{'dbname':'DATABASE','channel_binding':'CHANNELBINDING'}.get(k,k.upper())] = v
    env['PGCONNECT_TIMEOUT'] = '20'
    r = subprocess.run([binary,'-Fc','--no-owner','--no-acl','-f',str(path)], env=env, capture_output=True)
    exigir(r.returncode == 0 and path.exists(), 'pg_dump falló; ver log local del operador, sin DML')
    os.chmod(path, 0o600)
    restore = str(Path(binary).with_name('pg_restore'))
    r = subprocess.run([restore,'--list',str(path)],capture_output=True)
    exigir(r.returncode == 0, 'El archivo de respaldo no es legible por pg_restore')
    guardar(root/'respaldo.json', {'archivo':str(path),'sha256':digest(path.read_bytes()),'formato':'pg_dump custom'})
    return json.loads((root/'respaldo.json').read_text())


def huellas(conn, ajenas=False):
    tables = [r['tablename'] for r in _filas(conn, "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")]
    shared = {'competiciones_baloncesto':'codigo', 'equipos':'competicion_principal_id',
              'equipos_baloncesto':'competicion_principal_id', 'temporadas_baloncesto':'competicion_id',
              'partidos_baloncesto':'competicion_id'}
    result = {}
    for table in tables:
        where = sql.SQL('true')
        if table in shared:
            col = shared[table]
            if col == 'codigo':
                where = sql.SQL("codigo {} 'wnba'").format(sql.SQL('<>' if ajenas else '='))
            else:
                where = (sql.SQL("({0} IS NULL OR {0} IS DISTINCT FROM (SELECT id FROM public.competiciones_baloncesto WHERE codigo='wnba'))").format(sql.Identifier(col))
                         if ajenas else sql.SQL("{} = (SELECT id FROM public.competiciones_baloncesto WHERE codigo='wnba')").format(sql.Identifier(col)))
        elif ajenas:
            if not any(k in table for k in ('apuest','predic','modelo','calib','cohorte','forecast','analisis')):
                continue
        elif table not in {'lotes_ingesta_wnba','partidos_fuente_wnba'}:
            continue
        # Es_anual=false en filas ajenas es una ampliación de esquema, no cambio de sus datos.
        row_expr = sql.SQL("to_jsonb(t) - 'es_anual'") if table == 'temporadas_baloncesto' and ajenas else sql.SQL('to_jsonb(t)')
        query = sql.SQL("SELECT count(*) n,md5(coalesce(string_agg(h,'' ORDER BY h),'')) sha FROM (SELECT md5(({})::text) h FROM public.{} t WHERE {}) q").format(row_expr,sql.Identifier(table),where)
        result[table] = _filas(conn, query)[0]
    return result


def auditar(conn, lote):
    rows = _filas(conn, '''SELECT f.*,t.anio_inicio,t.anio_fin,t.es_anual,t.competicion_id temporada_comp,
        e.competicion_principal_id local_comp,v.competicion_principal_id visita_comp,
        c.codigo,p.valido,p.local_total,p.visitante_total,p.tipo_partido,
        p.equipo_local_id p_local,p.equipo_visitante_id p_visita,p.temporada_id p_temporada,
        p.ganador_id,p.competicion_id p_comp,
        p.local_q1,p.local_q2,p.local_q3,p.local_q4,p.local_ot,
        p.visitante_q1,p.visitante_q2,p.visitante_q3,p.visitante_q4,p.visitante_ot
        FROM public.partidos_fuente_wnba f
        JOIN public.competiciones_baloncesto c ON c.id=f.competicion_id
        JOIN public.temporadas_baloncesto t ON t.id=f.temporada_id
        JOIN public.equipos e ON e.id=f.equipo_local_id
        JOIN public.equipos v ON v.id=f.equipo_visitante_id
        LEFT JOIN public.partidos_baloncesto p ON p.id=f.partido_id
        WHERE c.codigo='wnba' AND f.source='ESPN' AND f.source_game_id=ANY(%s)''',
        ([r['source_game_id'] for r in lote['registros']],))
    byid = {r['source_game_id']:r for r in rows}
    exigir(len(rows) == len(byid) == len(lote['registros']), 'Postflight: conteo discordante')
    for r in lote['registros']:
        d = byid[r['source_game_id']]
        exigir(d['registro'] == r and d['registro_sha256'] == huella(r), 'Postflight: payload alterado')
        exigir(d['es_anual'] and d['anio_inicio'] == d['anio_fin'] == r['temporada']
               and d['competicion_id'] == d['temporada_comp'] == d['local_comp'] == d['visita_comp'],
               'Postflight: relación ajena o temporada inválida')
        exigir(d['estado'] == r['estado'] and d['fase'] == r['fase'] and d['inicio_utc'] == instante(r['inicio_utc']),
               'Postflight: estado o corte distinto')
        if r['final_completo']:
            exigir(d['partido_id'] and d['valido'] is True and d['p_comp'] == d['competicion_id']
                   and d['p_local'] == d['equipo_local_id'] and d['p_visita'] == d['equipo_visitante_id']
                   and d['p_temporada'] == d['temporada_id'] and d['tipo_partido'] == r['fase'],
                   'Postflight: vínculo canónico inválido')
            for lado in ('local','visitante'):
                for k in ('q1','q2','q3','q4','ot','total'):
                    exigir(d[lado+'_'+k] == r[lado+'_'+k], 'Postflight: marcador distinto')
            exigir(d['ganador_id'] == d['equipo_local_id' if r['local_total'] > r['visitante_total'] else 'equipo_visitante_id'],
                   'Postflight: ganador distinto')
        else:
            exigir(d['partido_id'] is None and d['local_total'] is None and d['visitante_total'] is None,
                   'Postflight: no final convertido en resultado')
    return {**resumen(lote), 'errores':0, 'verificados':len(rows)}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--entrada', type=Path, required=True)
    p.add_argument('--salida', type=Path, required=True)
    p.add_argument('--modo', choices=('validar','ensayar','aplicar','verificar'), default='validar')
    p.add_argument('--ensayo', type=Path, help='reporte.json de un ensayo terminado y revertido')
    args = p.parse_args(argv)
    root = args.salida.resolve()
    exigir(root != REPO and REPO not in root.parents, 'La evidencia debe estar fuera del repositorio')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    exigir(not (root/'reporte.json').exists(), 'No sobrescribir otra operación; utilice otro directorio')
    lote = leer_lote(args.entrada)
    report = {'modo':args.modo,'lote_sha256':lote['sha256'],'archivos':lote['archivos'],
              'importador_sha256':digest((BACKEND/'ingesta_wnba.py').read_bytes()+Path(__file__).read_bytes()),
              'migracion_sha256':digest(MIGRACION.read_bytes()),
              'inicio_utc':datetime.now(timezone.utc).isoformat(), 'entrada':str(args.entrada), **resumen(lote)}
    if args.modo != 'validar':
        load_dotenv(BACKEND/'.env', override=False)
        url = os.environ.get('DATABASE_URL')
        exigir(url, 'DATABASE_URL no configurada')
        if args.modo == 'ensayar':
            report['respaldo'] = respaldo(url, root)
        elif args.modo == 'aplicar':
            exigir(args.ensayo, 'Aplicar requiere --ensayo')
            prev = json.loads(args.ensayo.read_text())
            exigir(prev.get('estado') == 'ENSAYO_REVERTIDO' and prev.get('lote_sha256') == lote['sha256']
                   and prev.get('archivos') == report['archivos']
                   and prev.get('importador_sha256') == report['importador_sha256']
                   and prev.get('migracion_sha256') == report['migracion_sha256'], 'Ensayo incompatible')
            backup = prev['respaldo']
            exigir(digest(Path(backup['archivo']).read_bytes()) == backup['sha256'], 'Respaldo alterado')
            report['respaldo'] = backup
        # Si se interrumpe tras COMMIT, el archivo indica operación pendiente de
        # verificación, nunca una falsa carga completa; se recupera con verificar.
        report['estado'] = 'EN_CURSO'
        guardar(root/'reporte.json',report)
        with psycopg.connect(url, autocommit=True) as conn:
            with conn.transaction(force_rollback=args.modo == 'ensayar'):
                conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
                conn.execute("SET LOCAL statement_timeout='90s'")
                conn.execute("SET LOCAL lock_timeout='5s'")
                if args.modo == 'verificar':
                    conn.execute('SET TRANSACTION READ ONLY')
                    report['postflight'] = auditar(conn,lote)
                else:
                    conn.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:wnba:import'))")
                    report['baseline_wnba'] = huellas(conn)
                    if args.modo == 'aplicar':
                        exigir(report['baseline_wnba'] == prev['baseline_wnba'], 'WNBA cambió desde el ensayo')
                    protected = huellas(conn,ajenas=True)
                    conn.execute(MIGRACION.read_text())
                    report['carga'] = importar(conn,lote)
                    report['postflight'] = auditar(conn,lote)
                    report['repeticion'] = importar(conn,lote)
                    exigir(report['repeticion']['insertados'] == report['repeticion']['actualizados'] ==
                           report['repeticion']['equipos_creados'] == report['repeticion']['temporadas_creadas'] == 0,
                           'Repetición no idempotente')
                    exigir(huellas(conn,ajenas=True) == protected, 'Datos ajenos cambiaron; revertir')
                    report['huellas_protegidas'] = protected
                    report['huellas_wnba_despues'] = huellas(conn)
            if args.modo == 'ensayar':
                with conn.transaction():
                    conn.execute('SET TRANSACTION READ ONLY')
                    exigir(huellas(conn) == report['baseline_wnba'], 'Rollback no verificado')
    report['estado'] = {'validar':'VALIDADO_SIN_BD','ensayar':'ENSAYO_REVERTIDO',
                        'aplicar':'APLICADO','verificar':'VERIFICADO_READONLY'}[args.modo]
    report['fin_utc'] = datetime.now(timezone.utc).isoformat()
    guardar(root/'reporte.json',report)
    print(json.dumps({'estado':report['estado'],'resumen':resumen(lote), 'carga':report.get('carga'),
                      'reporte':str(root/'reporte.json')},ensure_ascii=False,indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, psycopg.Error) as exc:
        # Los errores de libpq pueden incluir credenciales/hosts: no imprimir su texto.
        print('WNBA:', str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
              getattr(exc,'sqlstate',''), file=sys.stderr)
        raise SystemExit(3)
