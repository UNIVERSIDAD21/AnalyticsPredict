"""Operación manual local: revisar -> aplicar -> entrenar candidato -> seleccionar.

No arranca servicios. No publica el activo. Ningún comando se ejecuta desde GET.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from servicios.refresco_nba import aplicar, guardar_nuevo, huella, planificar


def conectar(env_local, esperada):
    from dotenv import dotenv_values
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    config = dotenv_values(env_local)
    params = conninfo_to_dict(config.get('DATABASE_URL', ''))
    if (params.get('host') != '127.0.0.1' or params.get('port') != '55433'
            or params.get('dbname') != esperada or params.get('hostaddr') or params.get('service')
            or params.get('options') or params.get('sslmode') != 'disable'):
        raise ValueError('Se exige la BD local declarada en 127.0.0.1:55433, sin redirección ni TLS remoto')
    for clave in list(os.environ):
        if clave.startswith('PG'):
            os.environ.pop(clave, None)
    conn = psycopg.connect(**params, connect_timeout=5, application_name='ap_refresco_nba_manual')
    with conn.transaction():
        actual = conn.execute('SELECT current_database(),host(inet_server_addr()),inet_server_port()').fetchone()
        if actual != (esperada, '127.0.0.1', 55433):
            conn.close()
            raise ValueError('La identidad SQL no coincide')
    return conn


@contextmanager
def solo_lectura(conn):
    with conn.transaction():
        conn.execute('SET TRANSACTION READ ONLY')
        yield


def revisar(conn, desde, hasta, anio_fin, salida):
    from scripts.actualizar_partidos_nba import request_json, ESPN_SCOREBOARD
    if desde > hasta or (hasta-desde).days > 60:
        raise ValueError('Usa una ventana incremental de hasta 61 días')
    eventos = {}
    fuentes = []
    salida = Path(salida)
    for n in range((hasta-desde).days + 1):
        dia = desde + timedelta(days=n)
        path = salida / 'fuentes' / (dia.isoformat() + '.json')
        if path.exists():
            raise ValueError('La revisión requiere un destino nuevo; no sobrescribir fuentes')
        feed = request_json(ESPN_SCOREBOARD, {'dates': dia.strftime('%Y%m%d'), 'limit': 500}, retries=1)
        if (len(feed.get('leagues', [])) != 1 or feed['leagues'][0].get('slug') != 'nba'
                or not isinstance(feed.get('events'), list) or len(feed['events']) >= 500):
            raise ValueError('Feed fuera de dominio, ausente o posiblemente truncado')
        guardar_nuevo(path, {'url': ESPN_SCOREBOARD, 'fecha_feed': str(dia),
                            'observado_en': datetime.now(timezone.utc).isoformat(), 'payload': feed})
        fuentes.append({'archivo': str(path.resolve()), 'sha256': sha256(path.read_bytes()).hexdigest()})
        for evento in feed['events']:
            ident = str(evento['id'])
            if ident in eventos and huella(eventos[ident]) != huella(evento):
                raise ValueError('Evento con estados distintos en la misma revisión; repetir en destino nuevo')
            eventos[ident] = evento
    with solo_lectura(conn):
        plan = planificar(conn, list(eventos.values()), anio_fin)
    documento = {'formato': 'nba-refresco-v1', 'desde_feed': str(desde), 'hasta_feed': str(hasta),
                 'revisado_en': datetime.now(timezone.utc).isoformat(), 'fuentes': fuentes, 'plan': plan}
    guardar_nuevo(salida / 'plan.json', documento)
    return documento


def publicar_revision(documento, *, ingesta=None):
    from servicios.modelo_nba_exploratorio import directorio
    raiz = directorio()
    path = raiz / 'ultima_revision.json'
    anterior = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    plan = documento['plan']
    finales = [p for p in plan if p['accion'] != 'EXCLUIDO']
    incidencias = [p['evento_id'] for p in plan if p.get('motivo') not in (None, 'NO_FINAL')]
    dato = {'revisado_en': documento['revisado_en'], 'ultima_ingesta_en': ingesta or anterior.get('ultima_ingesta_en'),
            'desde_feed': documento['desde_feed'], 'hasta_feed': documento['hasta_feed'],
            'finales_fuente_validados': len(finales), 'eventos_no_finales': sum(p.get('motivo') == 'NO_FINAL' for p in plan),
            'incidencias': incidencias, 'estado': 'PARCIAL' if incidencias else 'VENTANA_CONTRASTADA',
            'ultimo_final_validado': max((str(p['registro']['fecha_partido']) for p in finales), default=None),
            'pendientes_en_vista_previa': sum(p['accion'] in ('INSERTAR', 'ACTUALIZAR') for p in plan),
            'plan_sha256': huella(documento), 'historico_integro_acreditado': False}
    if ingesta:
        dato['pendientes_en_vista_previa'] = 0
    temporal = raiz / 'revision.pendiente.json'
    guardar_nuevo(temporal, dato)
    temporal.replace(path)


def ejecutar_plan(conn, path, recibo, respaldo):
    from servicios.operacion_agendas import respaldar
    from psycopg.conninfo import make_conninfo
    path, recibo, respaldo = Path(path), Path(recibo), Path(respaldo)
    if recibo.exists() or respaldo.exists():
        raise ValueError('Recibo y respaldo deben ser nuevos; conciliar si hubo interrupción')
    original = path.read_bytes()
    documento = json.loads(original)
    for fuente in documento['fuentes']:
        if sha256(Path(fuente['archivo']).read_bytes()).hexdigest() != fuente['sha256']:
            raise ValueError('Fuente alterada después de la vista previa')
    # Dump externo, credenciales del objeto protegido; nunca se imprimen.
    backup = respaldar(make_conninfo(**conn.info.get_parameters(), password=conn.info.password), respaldo)
    guardar_nuevo(recibo.with_suffix('.intencion.json'), {'plan_sha256': sha256(original).hexdigest(), 'backup': backup,
                   'estado': 'INTENCION_ANTES_DEL_COMMIT'})
    with conn.transaction():
        resultado = aplicar(conn, documento['plan'])
        for item in documento['plan']:
            if item['accion'] != 'EXCLUIDO':
                after = planificar(conn, [item['evento']], item['anio_fin'])[0]
                if after['accion'] != 'COINCIDENTE':
                    raise ValueError('Postflight dentro de transacción no coincide')
    guardar_nuevo(recibo, {'estado': 'COMMIT_CONFIRMADO', 'plan_sha256': sha256(original).hexdigest(),
                          'completado_en': datetime.now(timezone.utc).isoformat(), **resultado})
    return resultado


def entrenar_candidato(conn, corte, candidato):
    from motor_autoentrenamiento.entrenador_bd import EntrenadorBD
    from motor_autoentrenamiento.artefacto_nba import guardar_artefacto, cargar_artefacto
    from servicios.modelo_nba_exploratorio import directorio
    candidato = Path(candidato).resolve()
    if candidato.exists() or candidato.parent != directorio().resolve():
        raise ValueError('Candidato NUEVO dentro de estado/nba_exploratorio; nunca sobre el activo')
    if corte > datetime.now(timezone.utc).date():
        raise ValueError('El corte no puede estar en el futuro')

    class PoolUnico:
        @contextmanager
        def connection(self):
            yield conn

    # Una sola instantánea y transacción para la muestra y su registro nuevo.
    with conn.transaction():
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('ap_entrenamiento_nba_manual'))")
        if candidato.exists():
            raise ValueError('El candidato ya fue creado; no sobrescribir ni reentrenar')
        datos = EntrenadorBD(PoolUnico()).entrenar(cutoff_fecha=corte)
        datos['metricas'].update(alcance='PERSONAL_EXPLORATORIO', calibrador=None)
        guardar_artefacto(datos, candidato)
        releido = cargar_artefacto(candidato)
        if releido['modelo_version_id'] != datos['modelo_version_id']:
            raise ValueError('El candidato publicado no corresponde a la versión')
    return {'modelo_version_id': datos['modelo_version_id'], 'archivo': candidato.name,
            'sha256': sha256(candidato.read_bytes()).hexdigest(), 'metricas': datos['metricas']}


def seleccionar(candidato):
    from motor_autoentrenamiento.artefacto_nba import cargar_artefacto
    from servicios.modelo_nba_exploratorio import directorio
    candidato = Path(candidato).resolve()
    raiz = directorio().resolve()
    if candidato.parent != raiz:
        raise ValueError('Candidato fuera del directorio permitido')
    datos = cargar_artefacto(candidato)
    if not datos or datos['modelo_version_id'] == 2123 or datos['metricas'].get('alcance') != 'PERSONAL_EXPLORATORIO':
        raise ValueError('No es un candidato personal separado de la campaña 2123')
    seleccion = {'archivo': candidato.name, 'sha256': sha256(candidato.read_bytes()).hexdigest(),
                 'modelo_version_id': datos['modelo_version_id'], 'seleccionado_en': datetime.now(timezone.utc).isoformat(),
                 'alcance': 'PERSONAL_EXPLORATORIO', 'probabilidades': 'RAW/NO_CERTIFICADO'}
    destino = raiz / 'seleccion.json'
    if destino.exists():
        guardar_nuevo(raiz / ('seleccion_anterior_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json'),
                      json.loads(destino.read_text(encoding='utf-8')))
    temporal = raiz / 'seleccion.pendiente.json'
    guardar_nuevo(temporal, seleccion)
    temporal.replace(destino)
    return seleccion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-local', required=True, type=Path)
    parser.add_argument('--bd-esperada', required=True)
    parser.add_argument('--activo', required=True, type=Path, help='Ruta protegida del activo, NO se modifica')
    sub = parser.add_subparsers(dest='accion', required=True)
    rev = sub.add_parser('revisar')
    rev.add_argument('--desde', required=True, type=date.fromisoformat)
    rev.add_argument('--hasta', required=True, type=date.fromisoformat)
    rev.add_argument('--anio-fin', required=True, type=int)
    rev.add_argument('--salida', required=True, type=Path)
    app = sub.add_parser('aplicar')
    app.add_argument('--plan', required=True, type=Path)
    app.add_argument('--recibo', required=True, type=Path)
    app.add_argument('--respaldo', required=True, type=Path)
    fit = sub.add_parser('entrenar')
    fit.add_argument('--corte-exclusivo', required=True, type=date.fromisoformat)
    fit.add_argument('--candidato', required=True, type=Path)
    fit.add_argument('--recibo', required=True, type=Path)
    sel = sub.add_parser('seleccionar')
    sel.add_argument('--candidato', required=True, type=Path)
    consulta = sub.add_parser('consultar')
    consulta.add_argument('--local', required=True)
    consulta.add_argument('--visitante', required=True)
    consulta.add_argument('--periodo', choices=['Q1', 'Q2', 'Q3', 'Q4', 'TOTAL'], required=True)
    consulta.add_argument('--linea', type=float, required=True)
    args = parser.parse_args()
    from dotenv import dotenv_values
    configurado = dotenv_values(args.env_local).get('ANALYTICSPREDICT_MODELO_NBA_ACTIVO')
    if not configurado or Path(configurado).resolve() != args.activo.resolve():
        raise ValueError('La ruta activa no coincide con la configuración protegida de la instalación')
    runtime = args.env_local.resolve().parents[2] / 'RUNTIME_LOCAL.json'
    if runtime.is_file():
        pg_bin = Path(json.loads(runtime.read_text(encoding='utf-8'))['pg_bin'])
        os.environ['AP_PG_DUMP'] = str(pg_bin / 'pg_dump.exe')
        os.environ['AP_PG_RESTORE'] = str(pg_bin / 'pg_restore.exe')
    # Nunca load_dotenv override=True: este proceso no importa db.obtener_pool.
    os.environ['ANALYTICSPREDICT_MODELO_NBA_ACTIVO'] = str(args.activo.resolve())
    with conectar(args.env_local, args.bd_esperada) as conn:
        if args.accion == 'revisar':
            result = revisar(conn, args.desde, args.hasta, args.anio_fin, args.salida)
            publicar_revision(result)
            result = {'eventos': len(result['plan']), 'plan': str(args.salida / 'plan.json')}
        elif args.accion == 'aplicar':
            result = ejecutar_plan(conn, args.plan, args.recibo, args.respaldo)
            publicar_revision(json.loads(args.plan.read_text(encoding='utf-8')), ingesta=datetime.now(timezone.utc).isoformat())
        elif args.accion == 'entrenar':
            if args.recibo.exists():
                raise ValueError('El recibo ya existe; no repetir un entrenamiento')
            result = entrenar_candidato(conn, args.corte_exclusivo, args.candidato)
            guardar_nuevo(args.recibo, result)
        elif args.accion == 'seleccionar':
            from motor_autoentrenamiento.artefacto_nba import cargar_artefacto
            datos = cargar_artefacto(args.candidato)
            with solo_lectura(conn):
                registro = conn.execute('SELECT hash_datos FROM modelo_versiones WHERE id=%s', (datos['modelo_version_id'],)).fetchone()
                if not registro or registro[0] != datos['metricas']['hash_datos']:
                    raise ValueError('Candidato sin versión SQL conciliada; no seleccionar')
            result = seleccionar(args.candidato)
        else:
            from servicios.modelo_nba_exploratorio import cargar_seleccion
            from servicios.consulta_local import consultar
            result = consultar(cargar_seleccion(), args.local, args.visitante, args.periodo, args.linea)
    print(json.dumps(result, default=str, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        # No filtrar la conexión/credenciales en excepciones de libpq.
        print(json.dumps({'estado': 'ERROR', 'tipo': type(exc).__name__}), file=sys.stderr)
        raise SystemExit(1)
