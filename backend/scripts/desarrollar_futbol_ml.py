#!/usr/bin/env python3
"""Declarar, exportar READ ONLY, desarrollar/congelar y evaluar ML fútbol V4.

Archivos externos de creación exclusiva. Nunca activa modelos, ejecuta DML ni
programa procesos futuros. El evaluador se ejecuta explícitamente tras los eventos.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor_futbol.evaluacion.forma_temporal import (
    PoliticaForma, congelar, desarrollar, evaluar_congelada, sellar, verificar,
)
from motor_futbol.evaluacion.estacional import exigir_utc
from motor_futbol.evaluacion.temporal_ridge import LIGAS
from motor_futbol.modelos.artefacto import sha256
from scripts.preparar_futbol_sombra import cargar_partidos, escribir_nuevo


def ruta_externa(valor):
    ruta = Path(valor).resolve()
    repo = Path(__file__).resolve().parents[2]
    if ruta == repo or repo in ruta.parents:
        raise argparse.ArgumentTypeError('Los artefactos se guardan fuera del repositorio')
    return ruta


def cargar_politica(path):
    declaracion = json.loads(path.read_text())
    verificar(declaracion)
    if declaracion['politica'] != PoliticaForma().to_dict():
        raise ValueError('Política distinta de la V4 predeclarada')
    declarado, inicio, fin = (exigir_utc(datetime.fromisoformat(declaracion[k]))
                             for k in ('declarado_en', 'inicio_eval', 'fin_eval'))
    if not declarado < inicio < fin:
        raise ValueError('Orden de declaración inválido')
    return declaracion, declarado, inicio, fin


def exportar(declaracion, snapshot_path, fixtures_path):
    # Importación diferida: declarar, entrenar offline y evaluar snapshots no abre BD.
    import psycopg
    from psycopg.rows import dict_row
    from db import obtener_database_url
    from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
    from motor_futbol.tipos import ConfiguracionEntrenamiento

    class PoolLectura:
        def __init__(self, conn): self.conn = conn
        @contextmanager
        def connection(self): yield self.conn

    if snapshot_path.exists() or fixtures_path.exists() or snapshot_path == fixtures_path:
        raise FileExistsError('Usar dos salidas nuevas y distintas; nunca sobrescribir una observación')
    with psycopg.connect(obtener_database_url(), connect_timeout=15, row_factory=dict_row) as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        conn.execute("SET LOCAL statement_timeout='30s'")
        corte = datetime.now(timezone.utc)
        config = ConfiguracionEntrenamiento(competiciones=list(LIGAS), fecha_corte=corte,
                    fecha_minima=datetime.fromisoformat(PoliticaForma().desde))
        entrenador = EntrenadorFutbol(PoolLectura(conn), config)
        partidos = entrenador._normalizar_partidos(entrenador._obtener_partidos_entrenamiento())
        futuros = conn.execute('''
            SELECT p.id,p.fecha_partido,p.estado,p.valido,el.nombre AS equipo_local,
                   ev.nombre AS equipo_visitante,c.codigo AS competicion_codigo
            FROM partidos_futbol p JOIN equipos_futbol el ON el.id=p.equipo_local_id
            JOIN equipos_futbol ev ON ev.id=p.equipo_visitante_id
            JOIN competiciones_futbol c ON c.id=p.competicion_id
            WHERE c.codigo=ANY(%s) AND p.fecha_partido >= %s AND p.fecha_partido < %s
            ORDER BY p.fecha_partido,p.id''',
            (list(LIGAS), datetime.fromisoformat(declaracion['inicio_eval']),
             datetime.fromisoformat(declaracion['fin_eval']))).fetchall()
        for path, filas in ((snapshot_path, partidos), (fixtures_path, futuros)):
            datos = json.loads(json.dumps(filas, default=str))
            escribir_nuevo(path, {'observado_en': corte.isoformat(), 'partidos': datos,
                'sha256_datos': sha256(datos), 'declaracion_sha256': declaracion['sha256'],
                'transaccion': 'REPEATABLE READ READ ONLY'})
    return {'partidos': len(partidos), 'fixtures': len(futuros), 'observado_en': corte.isoformat()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='accion', required=True)
    declarar = sub.add_parser('declarar')
    declarar.add_argument('--salida', type=ruta_externa, required=True)
    declarar.add_argument('--inicio', type=datetime.fromisoformat, required=True)
    declarar.add_argument('--fin', type=datetime.fromisoformat, required=True)
    extraer = sub.add_parser('exportar')
    extraer.add_argument('--politica', type=Path, required=True)
    extraer.add_argument('--snapshot', type=ruta_externa, required=True)
    extraer.add_argument('--fixtures', type=ruta_externa, required=True)
    desarrollo = sub.add_parser('desarrollar')
    for nombre in ('politica', 'snapshot', 'fixtures'):
        desarrollo.add_argument('--' + nombre, type=Path, required=True)
    desarrollo.add_argument('--salida', type=ruta_externa, required=True)
    desarrollo.add_argument('--cohorte', type=ruta_externa, required=True)
    evaluar = sub.add_parser('evaluar')
    evaluar.add_argument('--cohorte', type=Path, required=True)
    evaluar.add_argument('--snapshot', type=Path, required=True)
    evaluar.add_argument('--salida', type=ruta_externa, required=True)
    args = parser.parse_args(argv)
    ahora = datetime.now(timezone.utc)
    if args.accion == 'declarar':
        inicio, fin = map(exigir_utc, (args.inicio, args.fin))
        if not ahora < inicio < fin:
            raise ValueError('Declarar un periodo estrictamente futuro con zona horaria')
        escribir_nuevo(args.salida, sellar({'politica': PoliticaForma().to_dict(),
            'declarado_en': ahora.isoformat(), 'inicio_eval': inicio.isoformat(), 'fin_eval': fin.isoformat(),
            'criterio': 'Todos los fixtures de cinco ligas; abstenciones y targets ausentes penalizan cobertura',
            'activacion': 'Sin activación automática; punto/MAE no es calibración de probabilidades'}))
        print('V4 declarada; sin consultar BD ni ajustar modelos.')
    elif args.accion == 'exportar':
        declaracion, declarado, _, _ = cargar_politica(args.politica)
        if declarado > ahora:
            raise ValueError('Declaración posterior a la observación')
        print(json.dumps(exportar(declaracion, args.snapshot, args.fixtures)))
    elif args.accion == 'desarrollar':
        declaracion, declarado, inicio, fin = cargar_politica(args.politica)
        if args.salida.exists() or args.cohorte.exists() or args.salida == args.cohorte:
            raise FileExistsError('Desarrollo y cohorte deben ser salidas nuevas y distintas')
        snapshot, partidos = cargar_partidos(args.snapshot)
        fixtures, futuros = cargar_partidos(args.fixtures)
        corte = exigir_utc(datetime.fromisoformat(snapshot['observado_en']))
        observado_fixtures = exigir_utc(datetime.fromisoformat(fixtures['observado_en']))
        if not declarado <= corte <= observado_fixtures < ahora < inicio < fin:
            raise ValueError('Snapshot/calendario deben ser posteriores a declaración y anteriores al periodo')
        if any(p['fecha_partido'] >= corte for p in partidos):
            raise ValueError('El snapshot contiene resultados posteriores al corte')
        for datos in (snapshot, fixtures):
            if datos.get('declaracion_sha256') != declaracion['sha256']:
                raise ValueError('Snapshot sin referencia a la declaración actual')
        informe = desarrollar(partidos, corte)
        congelado = datetime.now(timezone.utc)
        cohorte = congelar(informe, futuros, congelado, inicio, fin, declarado)
        cohorte = sellar({**{k: v for k, v in cohorte.items() if k != 'sha256'},
                          'declaracion_sha256': declaracion['sha256'],
                          'snapshot_sha256': snapshot['sha256_datos'],
                          'fixtures_sha256': fixtures['sha256_datos']})
        if datetime.now(timezone.utc) >= inicio:
            raise ValueError('El periodo comenzó durante el ajuste; no publicar capturas tardías')
        escribir_nuevo(args.salida, informe)
        escribir_nuevo(args.cohorte, cohorte)
        print(json.dumps({k: {'diseno': v['candidato_final'].get('diseno'),
              'estado': v['candidato_final']['estado'],
              'gate_desarrollo': v['resumen']['gate_estadistico_superado'],
              'motivos': v['resumen']['motivos_estadisticos'],
              'predicciones_futuras': len(cohorte['familias'][k]['predicciones']),
              'abstenciones_futuras': len(cohorte['familias'][k]['abstenciones'])}
              for k, v in informe['familias'].items()}, ensure_ascii=False))
    else:
        cohorte = json.loads(args.cohorte.read_text())
        snapshot, partidos = cargar_partidos(args.snapshot)
        observado = exigir_utc(datetime.fromisoformat(snapshot['observado_en']))
        if observado > ahora:
            raise ValueError('Observación fechada en el futuro')
        escribir_nuevo(args.salida, evaluar_congelada(cohorte, partidos, observado))
        print('Evaluación guardada; no promueve ni activa el modelo.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # No filtrar DSN, nombres de hosts protegidos ni errores crudos del driver.
        print('Operación no completada: ' + type(error).__name__, file=sys.stderr)
        raise SystemExit(1)
