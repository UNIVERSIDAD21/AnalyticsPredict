#!/usr/bin/env python3
"""Calendario WNBA: consulta, respaldo, ensayo rollback, aplicación única y postflight.

Sin --aplicar solo consulta la fuente y crea un plan fuera del producto.
--reporte permite reutilizar una consulta íntegra sin repetir las solicitudes.
"""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import psycopg
from dotenv import load_dotenv
from servicios.calendario_wnba import MIGRACION, aplicar, consultar
from scripts.importar_wnba import guardar, respaldo, huellas
from ingesta_wnba import exigir, huella


def ejecutar(reporte, salida, url, *, aplicar_cambios=False):
    salida=Path(salida);salida.mkdir(mode=0o700,parents=True,exist_ok=True)
    exigir(not (salida/'operacion.json').exists(), 'Usar directorio NUEVO; no repetir una operación aplicada')
    report={'consulta_sha256':huella(reporte),'migracion_sha256':huella(MIGRACION.read_text()),
            'aplicador_sha256':huella(Path(__file__).read_text()+Path(__import__('servicios.calendario_wnba',fromlist=['x']).__file__).read_text())}
    if not aplicar_cambios:
        guardar(salida/'consulta.json',reporte);return report
    report['respaldo']=respaldo(url,salida)
    with psycopg.connect(url,autocommit=True) as c:
        def protegidas():
            d=huellas(c,ajenas=True)
            # La nueva columna nullable no altera el contenido previo de apuestas.
            with c.cursor() as cur:
                cur.execute("SELECT count(*), md5(coalesce(string_agg(h,'' ORDER BY h),'')) FROM (SELECT md5((to_jsonb(a)-'fixture_wnba_id')::text) h FROM apuestas a) q")
                n,h=cur.fetchone();d['apuestas']={'n':n,'sha':h}
            return d
        with c.transaction(force_rollback=True):
            c.execute("SET LOCAL lock_timeout='5s'")
            c.execute("SET LOCAL statement_timeout='90s'")
            baseline=protegidas()
            c.execute(MIGRACION.read_text())
            report['ensayo']=aplicar(c,reporte)
            segunda=aplicar(c,reporte)
            exigir(segunda['altas']==segunda['revisados']==0,'Repetición no idempotente')
            exigir(protegidas()==baseline,'Cambio en datos protegidos durante ensayo')
        # Comprobar reversión real, no solo ausencia de excepción.
        report['rollback_verificado']=protegidas()==baseline
        exigir(report['rollback_verificado'],'Rollback no verificado')
        guardar(salida/'ensayo.json',report)
        with c.transaction():
            c.execute("SET LOCAL lock_timeout='5s'")
            c.execute("SET LOCAL statement_timeout='90s'")
            exigir(protegidas()==baseline,'Datos protegidos cambiaron desde ensayo')
            c.execute(MIGRACION.read_text())
            report['aplicacion']=aplicar(c,reporte)
            exigir(protegidas()==baseline,'Cambio en datos protegidos durante aplicación')
        with c.transaction():
            c.execute('SET TRANSACTION READ ONLY')
            report['protegidas_iguales']=protegidas()==baseline
            from psycopg.rows import dict_row
            with c.cursor(row_factory=dict_row) as cur:
                cur.execute('SELECT id,source_game_id,inicio_utc,estado,resultado_id FROM fixtures_wnba ORDER BY id')
                report['postflight']=cur.fetchall()
    report['estado']='APLICADO_Y_VERIFICADO'
    guardar(salida/'consulta.json',reporte);guardar(salida/'operacion.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--desde',type=date.fromisoformat)
    p.add_argument('--salida',type=Path,required=True)
    p.add_argument('--reporte',type=Path)
    p.add_argument('--cache',type=Path)
    p.add_argument('--aplicar',action='store_true')
    a=p.parse_args()
    load_dotenv(BACKEND/'.env',override=False)
    reporte=json.loads(a.reporte.read_text()) if a.reporte else consultar(a.desde,cache=a.cache)
    r=ejecutar(reporte,a.salida,os.environ.get('DATABASE_URL'),aplicar_cambios=a.aplicar)
    print(json.dumps({'estado':r.get('estado','CONSULTADO_SIN_DML'),'encuentros':len(reporte['partidos'])}))

if __name__=='__main__':main()
