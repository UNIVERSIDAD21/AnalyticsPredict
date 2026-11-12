"""Actualización manual común para el escritorio y la UI; nunca entrena modelos."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.types.json import Jsonb
from dotenv import dotenv_values
from servicios.actualizador_partidos import catalogo, ventana, pendientes, revisar_estadisticas, resumen_ligas, contraste_local
from servicios.fuentes_resultados import Capturas, recolectar
from servicios.fuentes_agenda import BOGOTA
from servicios.operacion_agendas import exclusion, respaldar
from servicios.sincronizacion_agendas import planificar, aplicar
from servicios.transporte_agenda import ClienteAgenda, guardar
from servicios import cola_actualizador as cola
from servicios import flujo_cola_actualizador as flujo
from servicios.etapa_agenda_multiliga import ejecutar_agenda_por_lotes, resumen_publicable
from servicios.cobertura_actualizador import leer_cobertura_operativa
from scripts.refrescar_nba_local import solo_lectura


def configuracion(path, ensayo=None):
    values = dotenv_values(path)
    params = conninfo_to_dict(values.get('DATABASE_URL', ''))
    if (params.get('host') != '127.0.0.1' or params.get('port') != '55433'
            or params.get('dbname') != 'ap_unicode_20261101_044650'
            or params.get('sslmode') != 'disable'
            or any(params.get(k) for k in ('hostaddr', 'service', 'options'))):
        raise ValueError('Destino distinto de la instalación PostgreSQL local verificada')
    if ensayo:
        if not ensayo.startswith('ap_actualizador_prueba_') or not ensayo.replace('_', '').isalnum():
            raise ValueError('La BD de ensayo debe ser un clon propio identificado')
        params['dbname'] = ensayo
    for key in list(os.environ):
        if key.startswith('PG'):
            os.environ.pop(key, None)
    for key in ('AP_AGENDA_ESTADO', 'ANALYTICSPREDICT_MODELO_NBA_ACTIVO',
                'ANALYTICSPREDICT_MODELO_EUROLIGA_ACTIVO', 'ANALYTICSPREDICT_MODELO_WNBA_ACTIVO'):
        if values.get(key):
            os.environ[key] = values[key]
    package = path.resolve().parents[2]
    runtime = package / 'RUNTIME_LOCAL.json'
    if not runtime.is_file():
        raise ValueError('Se exige el archivo de entorno del paquete personal instalado')
    pg_bin = Path(json.loads(runtime.read_text(encoding='utf-8'))['pg_bin'])
    if ensayo:
        # Administración exclusivamente del clon explícito, jamás de la BD personal.
        pg_runtime = Path(json.loads(runtime.read_text(encoding='utf-8'))['postgres_runtime'])
        params.pop('password', None)
        params.update(user='ap_migracion_admin', passfile=str(pg_runtime / 'pgpass.conf'))
        os.environ['PGPASSFILE'] = params['passfile']
    os.environ['AP_PG_DUMP'] = str(pg_bin / 'pg_dump.exe')
    os.environ['AP_PG_RESTORE'] = str(pg_bin / 'pg_restore.exe')
    state = Path(values.get('AP_AGENDA_ESTADO') or package / 'estado/agenda-sinc-local')
    return values, params, package, state


def conectar(params):
    conn = psycopg.connect(**params, connect_timeout=8, application_name='ap_actualizador_partidos_manual')
    with solo_lectura(conn):
        identity = conn.execute('SELECT current_database(),host(inet_server_addr()),inet_server_port()').fetchone()
        if identity != (params['dbname'], '127.0.0.1', 55433):
            raise ValueError('La identidad del servidor no coincide con el destino validado')
        if params['dbname'].startswith('ap_actualizador_prueba_'):
            expected = Path(params['passfile']).parent / 'datos'
            if Path(conn.execute('SHOW data_directory').fetchone()[0]).resolve() != expected.resolve():
                raise ValueError('El clon no pertenece al runtime local esperado')
    return conn


def modelos(conn):
    from motor_autoentrenamiento.artefacto_nba import cargar_artefacto
    from motor_autoentrenamiento.gestor_modelo import ModeloEnMemoria
    from servicios.modelo_nba_exploratorio import cargar_seleccion, estado_refresco
    result = []
    for name, load in [('NBA publicado', lambda: ModeloEnMemoria(cargar_artefacto())), ('NBA candidato', cargar_seleccion)]:
        try:
            with solo_lectura(conn):
                status = estado_refresco(conn, load())
            result.append({'nombre': name, 'version': status['modelo']['modelo_version'],
                'corte': status['modelo']['corte_modelo'],
                'finales_posteriores': status['finales_posteriores_al_modelo'],
                'necesita_actualizacion': status['necesita_actualizacion']})
        except (ValueError, KeyError, TypeError, OSError):
            result.append({'nombre': name, 'corte': None, 'detalle': 'Modelo no verificable; no se entrenó'})
    from motor.euroliga import cargar as cargar_euro
    from servicios.predictor_wnba import cargar as cargar_wnba
    from servicios.consulta_local_ligas import identidad
    for name, code, liga, load in [('Euroliga publicado', 'euroleague', 'euroliga', cargar_euro),
                                    ('WNBA publicado', 'wnba', 'wnba', cargar_wnba)]:
        try:
            meta = identidad(load(), liga)
            with solo_lectura(conn):
                n = conn.execute("""SELECT count(*) FROM partidos_baloncesto p
                    JOIN competiciones_baloncesto c ON c.id=p.competicion_id
                    WHERE c.codigo=%s AND p.valido AND p.fecha_partido>%s
                    AND p.local_total>0 AND p.visitante_total>0
                    AND p.local_q1+p.local_q2+p.local_q3+p.local_q4+COALESCE(p.local_ot,0)=p.local_total
                    AND p.visitante_q1+p.visitante_q2+p.visitante_q3+p.visitante_q4+COALESCE(p.visitante_ot,0)=p.visitante_total
                    AND (p.tipo_partido='REG' OR %s='euroleague' AND p.tipo_partido='POST')""",
                    (code, meta['corte_modelo'], code)).fetchone()[0]
            result.append({'nombre': name, 'version': meta['modelo_version'], 'corte': meta['corte_modelo'],
                           'finales_posteriores': n, 'necesita_actualizacion': n > 0})
        except (ValueError, KeyError, TypeError, OSError, RuntimeError):
            result.append({'nombre': name, 'corte': None, 'detalle': 'Modelo no verificable; no se entrenó'})
    return result


def recibo_nba(conn, package, run, plan, details, ended):
    """Actualiza solo el recibo de datos; jamás NPZ, selección o campaña."""
    nba = next((r for r in details if r['codigo'] == 'nba'), None)
    if not nba:
        return
    target = package / 'estado/nba_exploratorio/ultima_revision.json'
    previous = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    guardar(run / 'RECIBO_NBA_ANTES.json', previous)
    ids = [r['partido_id'] for r in plan['aceptados'] if r['codigo'] == 'nba']
    with solo_lectura(conn):
        latest = conn.execute('SELECT max(fecha_partido) FROM partidos_baloncesto WHERE id=ANY(%s::uuid[])', (ids,)).fetchone()[0]
    # Una revisión parcial o vacía no borra la última validación acreditada.
    known = [str(latest) if latest else None, previous.get('ultimo_final_validado')]
    last_validated = max((x for x in known if x), default=None)
    sources = [p for p in plan['fuentes'] if '/basketball/nba/' in p['url']]
    guardar(target, {**previous, 'revisado_en': ended,
        'ultima_ingesta_en': ended if nba['insertados'] or nba['resultados_actualizados'] else previous.get('ultima_ingesta_en'),
        'desde_feed': nba['desde'], 'hasta_feed': nba['hasta'],
        'fuentes_observadas_en': max((p['observado_en'] for p in sources), default=None),
        'finales_fuente_validados': nba['finales_fuente'], 'eventos_no_finales': nba['no_finales_excluidos'],
        'incidencias': nba['incidencias'], 'estado': 'PARCIAL' if nba['incidencias'] else 'VENTANA_CONTRASTADA',
        'ultimo_final_validado': last_validated, 'pendientes_en_vista_previa': 0,
        'plan_sha256': plan['sha256'], 'historico_integro_acreditado': False,
        'origen': 'actualizador_manual_partidos', 'informe': str(run / 'RESULTADO.json')})


def ejecutar(args, *, reloj=lambda: datetime.now(timezone.utc)):
    values, params, package, state_root = configuracion(args.env_local, args.bd_ensayo)
    historial = getattr(args, 'historico', None)
    agenda_ampliada = getattr(args, 'agenda_ampliada', False)
    normal_archive = package / 'estado/actualizaciones_partidos'
    root = args.estado or state_root
    archive = args.salida or (package / 'estado/recuperacion_historica' if historial else normal_archive)
    if historial and not args.estado:
        root = archive / 'estado'
    if args.bd_ensayo:
        receipt = json.loads((archive.parent / 'CLON.json').read_text(encoding='utf-8'))
        if receipt.get('nombre') != args.bd_ensayo or receipt.get('propio') is not True:
            raise ValueError('Clon sin recibo propio conciliado')
    archive.mkdir(parents=True, exist_ok=True)
    with exclusion(state_root if historial and not args.bd_ensayo else root):
        pause = package / 'estado/actualizaciones_partidos/pausa_calidad.json'
        if not args.bd_ensayo and pause.is_file():
            print('Actualización pausada por revisión de calidad. Consulta el estado local.', file=sys.stderr)
            return 2
        now = reloj()
        today = now.astimezone(BOGOTA).date()
        if historial and historial[3] > today:
            raise ValueError('Un lote histórico no puede incluir días futuros')
        run = archive / now.strftime('%Y%m%dT%H%M%S%fZ')
        run.mkdir(exist_ok=False)
        started = now.isoformat()
        status = {'estado': 'EN_CURSO', 'tipo': 'ACTUALIZACION_PARTIDOS', 'iniciado_en': started,
            'directorio': str(run), 'detalle': 'Revisando resultados y estadísticas; los modelos no se entrenan.'}
        def progress(detail):
            status['detalle'] = detail
            guardar(root / 'estado.json', status)
        def journal(item):
            with (run / 'OPERACIONES.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
        # La caché histórica sigue siendo evidencia de las ejecuciones previas.
        # La caché operativa tiene una ruta estable y hereda los permisos del paquete.
        cache_operativa = (normal_archive if historial and not args.bd_ensayo else archive) / 'cache_v2'
        posible_escritura = False
        execution = None
        try:
            pointer = archive / 'ultima_aplicacion.json'
            with conectar(params) as conn:
                with solo_lectura(conn):
                    leagues = catalogo(conn)
                    sql_activa = args.aplicar and cola.disponible(conn)
                    agenda_activa = not historial and sql_activa and conn.execute(
                        "SELECT to_regclass('public.ap_m2_agenda_consultas') IS NOT NULL").fetchone()[0]
                    if historial:
                        leagues = [x for x in leagues if x['codigo']==historial[0]]
                        if len(leagues)!=1 or flujo.fuente(leagues[0])[1]=='SIN_ADAPTADOR':
                            raise ValueError('Competición histórica desconocida o sin adaptador')
                if historial and args.aplicar and not sql_activa:
                    raise ValueError('Instala la cola SQL antes de aplicar un lote histórico')
                if agenda_ampliada and not agenda_activa:
                    raise ValueError('La agenda ampliada requiere la cola SQL de agenda')
                if sql_activa:
                    supplied = getattr(args, 'ejecucion_id', None)
                    if supplied:
                        execution = supplied
                    else:
                        execution, nueva = cola.reservar(conn, now, tipo='HISTORICA' if historial else 'DIARIA')
                        if not nueva:
                            return 0
                    if not cola.reclamar(conn, execution, now):
                        return 0
                    status['ejecucion_id'] = str(execution)
                elif getattr(args, 'ejecucion_id', None):
                    raise ValueError('Reserva SQL sin migración')
                previous = {}
                if not execution and pointer.exists():
                    previous = json.loads(pointer.read_text(encoding='utf-8'))
                progress(status['detalle'])
                windows = {x['codigo']: ventana(today, previous.get('revisiones', {}).get(x['codigo'])) for x in leagues}
                if historial:
                    windows = {historial[0]: historial[2:]}
                    jobs = [(leagues[0], *historial[2:])]
                elif execution:
                    with solo_lectura(conn):
                        jobs = flujo.ventanas_ciclo(conn, leagues, today, now)
                    windows = {x['codigo']: (today - timedelta(days=7), today) for x in leagues}
                else:
                    jobs = [(league, *windows[league['codigo']]) for league in leagues]
                lower, upper = min(lo for _, lo, _ in jobs), max(hi for _, _, hi in jobs)
                transport = None
                if not args.fuentes or args.completar_capturas:
                    transport = ClienteAgenda(cache_operativa, intervalo=3, max_requests=400 if execution else 800)
                client = Capturas(args.fuentes, completar=transport) if args.fuentes else transport
                records, problems, proofs, consultas = [], [], [], []
                agenda = backup = None
                if agenda_activa:
                    progress('Preparando respaldo para agenda, resultados y estadísticas')
                    backup_url = psycopg.conninfo.make_conninfo(**params)
                    backup = respaldar(backup_url, run / 'PREVIO.dump')
                    cupo_agenda = 200 if agenda_ampliada else 48
                    if transport:
                        transport.presupuesto = 216
                    status['etapa'] = 'AGENDA'
                    posible_escritura = True
                    etapa = ejecutar_agenda_por_lotes(conn, execution, leagues, client, today, now,
                        cupo_lote=cupo_agenda, max_turnos=200, observar=progress)
                    agenda = resumen_publicable(conn, leagues, today, etapa)
                    guardar(run / 'AGENDA.json', agenda)
                    status['agenda_multiliga'] = agenda
                    proofs.extend(p for q in etapa['preparado']['consultas'] for p in q['pruebas'])
                    if transport:
                        transport.presupuesto = 400
                status['etapa'] = 'RESULTADOS'
                coverage = {x['codigo']: {'finales': 0, 'no_finales': 0} for x in leagues}
                seen = set()
                for league, lo, hi in jobs:
                    status['progreso'] = {'ligas_revisadas': len(seen), 'ligas_total': len(leagues)}
                    rows, errors, sources, excluded = recolectar(client, league, lo, hi, observar=progress)
                    if historial:
                        rows = [row for row in rows if str(row.get('anio')) == str(historial[1])]
                    consultas.append((league, lo, hi, errors, sources))
                    records.extend(rows); problems.extend(errors); proofs.extend(sources)
                    seen.add(league['codigo'])
                    if (lo, hi) == windows[league['codigo']]:
                        coverage[league['codigo']]['no_finales'] = excluded
                    guardar(run / 'FUENTES.json', list({s['url']: s for s in proofs}.values()))
                if execution:
                    records = flujo.consolidar(records, problems)
                for row in records:
                    coverage[row['codigo']]['finales'] += 1
                with solo_lectura(conn):
                    plan = planificar(conn, records, problems, proofs, today, desde=lower)
                guardar(run / 'PLAN_RESULTADOS.json', plan)
                status['progreso'] = {'ligas_revisadas': len(leagues), 'ligas_total': len(leagues)}
                if args.aplicar:
                    progress('Verificando respaldo antes de aplicar resultados y estadísticas')
                    # La configuración ya acreditó conexión local; no se imprimen credenciales.
                    if backup is None:
                        backup_url = psycopg.conninfo.make_conninfo(**params)
                        backup = respaldar(backup_url, run / 'PREVIO.dump')
                    guardar(run / 'PRECOMMIT_RESULTADOS.json', {'plan_sha256': plan['sha256'], 'respaldo': backup})
                    posible_escritura = True
                    commit_resultados = {'plan_sha256': plan['sha256']}
                    if execution:
                        batch, _, new = flujo.aplicar_resultados(conn, execution, plan, records, consultas, now,
                                                               acreditar=not historial)
                        commit_resultados.update(lote_sql=batch, reutilizado=not new)
                    else:
                        with conn.transaction():
                            conn.execute("SET LOCAL lock_timeout='5s'; SET LOCAL statement_timeout='90s'")
                            aplicar(conn, plan)
                    guardar(run / 'COMMIT_RESULTADOS.json', {**commit_resultados, 'confirmado_en': reloj().isoformat()})
                    with solo_lectura(conn):
                        second = planificar(conn, records, problems, proofs, today, desde=lower)
                    guardar(run / 'POSTFLIGHT_RESULTADOS.json', second)
                    if second['operaciones']:
                        raise RuntimeError('Commit confirmado; postflight con diferencias. No reaplicar a ciegas')
                else:
                    backup = None
                with solo_lectura(conn):
                    if historial:
                        requested, maps = pendientes(conn, lower, upper)
                        feed = flujo.fuente(leagues[0])[1]
                        season = maps['temporadas'].get((feed, historial[1]))
                        recent = [row for row in requested if row['liga']==feed and str(row['temporada_id'])==str(season)]
                        stat_rows = flujo.candidatos_estadisticas(conn, now, recent, [])
                    elif execution:
                        recent, maps = pendientes(conn, lower, today)
                        due = {str(x['partido_id']) for x in cola.vencidos(conn, now, 'ESTADISTICAS') if x['partido_id']}
                        older, _ = pendientes(conn, today, today, due)
                        stat_rows = flujo.candidatos_estadisticas(conn, now, recent, older)
                    else:
                        stat_rows, maps = pendientes(conn, lower, upper, previous.get('pendientes_estadisticas', []))
                if execution and transport:
                    transport.presupuesto = 800
                confirmar = anotar_error = None
                if execution:
                    flujo.pendientes_estadisticos(conn, execution, recent, maps, now, 'ESTADISTICA_AUN_NO_CONSULTADA')
                    def confirmar(*values):
                        return flujo.confirmar_estadisticas(conn, execution, *values, reloj())
                    def anotar_error(row, motivo):
                        flujo.pendientes_estadisticos(conn, execution, [row], maps, reloj(), motivo,
                                                      intento=True)
                status['etapa'] = 'ESTADISTICAS'
                stats = revisar_estadisticas(conn, stat_rows, maps, client, aplicar=args.aplicar,
                    observar=progress, registrar=journal, confirmar=confirmar, anotar_error=anotar_error)
                proofs.extend(stats['fuentes'])
                guardar(run / 'FUENTES.json', list({s['url']: s for s in proofs}.values()))
                with solo_lectura(conn):
                    remaining, _ = pendientes(conn, lower, upper, [str(r['id']) for r in stat_rows])
                    local_issues = contraste_local(conn, leagues, windows, plan['aceptados'])
                    if execution:
                        outstanding = conn.execute("""SELECT clave[2],count(*) FROM public.ap_m1_obligaciones
                            WHERE estado NOT IN ('RESUELTO','SIN_COBERTURA')
                            AND NOT (tipo='EVENTO' AND clave[6]='AGENDA') GROUP BY clave[2]""").fetchall()
                        for code, count in outstanding:
                            local_issues.append({'grupo': code, 'motivo': 'PENDIENTES_COLA_SQL', 'obligaciones': count})
                stats['incidencias'].extend(local_issues)
                ended = reloj().isoformat()
                details = resumen_ligas(leagues, windows, coverage, plan, stats, ended)
                for row in details:
                    if not historial and windows[row['codigo']][1] < today:
                        row['estado'] = 'PARCIAL'
                        row['incidencias'].append({'grupo': row['codigo'], 'motivo': 'Ventana de recuperación: faltan lotes posteriores'})
                with solo_lectura(conn):
                    details, cobertura_operativa = leer_cobertura_operativa(
                        conn, details, agenda, lower, upper, datetime.fromisoformat(ended))
                complete = all(x['estado'] in ('COMPLETA_EN_VENTANA', 'SIN_FINALES_EN_VENTANA') for x in details)
                if agenda:
                    complete = complete and all(x['estado'] in ('OBSERVADA_EN_FUENTE', 'SIN_EVENTOS_PUBLICADOS')
                                                for x in agenda['ligas'])
                report = {'tipo': 'ACTUALIZACION_INTEGRAL', 'alcance': 'FINALES_Y_ESTADISTICAS_EN_VENTANA',
                    'todas_ligas_verificadas': complete, 'ligas_resultado': details,
                    'cobertura_operativa': cobertura_operativa,
                    'estadisticas': {x['codigo']: {'estado': x['estado'], 'verificado_en': ended,
                        'detalle': f"Finales y campos objetivo revisados de {x['desde']} a {x['hasta']}; {len(x['incidencias'])} incidencias.",
                        'partidos_actualizados': x['estadisticas_actualizadas'], 'campos_recuperados': x['campos_completados']} for x in details},
                    'modelos': modelos(conn), 'ventana_desde': str(lower), 'ventana_hasta': str(upper),
                    'limite': 'Revisión acotada de finales, sin certificar agenda futura ni histórico íntegro. No reentrena modelos.'}
                if agenda:
                    report['alcance'] = 'AGENDA_RESULTADOS_ESTADISTICAS_EN_VENTANAS'
                    report['agenda_multiliga'] = agenda
                if historial:
                    report.update(tipo='RECUPERACION_HISTORICA', alcance='LOTE_DE_TEMPORADA',
                                  temporada_fuente=historial[1], denominador_oficial='DESCONOCIDO',
                                  todas_ligas_verificadas=False)
                status['etapa'] = 'COBERTURA'
                state = 'COMPLETO' if complete else 'PARCIAL'
                publicacion = {**status, 'estado': state, 'terminado_en': ended,
                    'fuentes_verificadas_en': max((s['observado_en'] for s in proofs), default=None),
                    'cambio_guardado_en': ended if args.aplicar and (plan['operaciones'] or stats['actualizados'] or (agenda and agenda['operaciones'])) else None,
                    'detalle': 'Actualización finalizada. Consulta el resumen por liga y sus pendientes.' if args.aplicar else 'Plan preparado sin cambios en la BD.',
                    'ligas_resultado': details, 'cobertura_operativa':cobertura_operativa,
                    'modelos': report['modelos'], 'informe': str(run / 'RESULTADO.json')}
                if args.aplicar:
                    journal({'tipo': 'PRECOMMIT_RESUMEN', 'informe': report})
                    def resumen_sql(_=None):
                        if not historial:
                            conn.execute('INSERT INTO sincronizaciones_agenda(id,iniciado_en,terminado_en,estado,informe) VALUES(%s,%s,%s,%s,%s)',
                                (execution or uuid4(), started, ended, state, Jsonb(report)))
                        if execution:
                            cola.finalizar(conn, execution, 'TERMINADA', datetime.fromisoformat(ended),
                                           {'cobertura': state, 'informe': report, 'publicacion': publicacion})
                        return {'cobertura': state, 'informe': report}
                    if execution:
                        cola.lote(conn, execution, 'RESUMEN', {'ejecucion': str(execution)},
                                  datetime.fromisoformat(ended), resumen_sql)
                    else:
                        with conn.transaction():
                            resumen_sql()
                    journal({'tipo': 'COMMIT_RESUMEN', 'terminado_en': ended})
                    if not args.bd_ensayo and not historial:
                        recibo_nba(conn, package, run, plan, details, ended)
                    checkpoints = dict(previous.get('revisiones', {}))
                    for row in details:
                        # Estadísticas ausentes se reintentan; los errores de identidad/fuente no avanzan la revisión.
                        errors = [x for x in plan['incidencias'] if x.get('grupo') == row['codigo']]
                        if not errors:
                            checkpoints[row['codigo']] = row['hasta']
                    if not execution:
                        guardar(pointer, {'revisiones': checkpoints,
                            'pendientes_estadisticas': list({str(r['id']) for r in remaining}),
                            'informe': str(run / 'RESULTADO.json')})
                else:
                    state = 'PLAN_SIN_APLICAR'
                    report['advertencia_plan'] = 'Las estadísticas nuevas dependen de aplicar primero los resultados; no se acredita escritura ni cobertura final.'
                guardar(run / 'RESULTADO.json', report)
                guardar(root / 'estado.json', {**publicacion, 'estado': state})
                print(json.dumps({'estado': state, 'ligas': len(details), 'informe': str(run / 'RESULTADO.json')}, ensure_ascii=False))
                return 0
        except Exception as exc:
            if execution:
                try:
                    with conectar(params) as recovered, recovered.transaction():
                        cola.finalizar(recovered, execution, 'ERROR', reloj(), {'tipo_error': type(exc).__name__})
                except psycopg.Error:
                    # El lock de sesión se liberó. Otro solicitante podrá reconciliar.
                    pass
            detalle = 'Ciclo interrumpido antes de guardar cambios en la base.'
            if posible_escritura:
                detalle = 'Ciclo interrumpido. Los cambios confirmados se conservan. Consulta los recibos del intento.'
            elif isinstance(exc, PermissionError):
                archivo = Path(exc.filename) if exc.filename else None
                if archivo and archivo.is_relative_to(cache_operativa):
                    detalle = 'El sistema denegó acceso a la caché de fuentes. El intento no guardó cambios en la base.'
                else:
                    detalle = 'El sistema denegó acceso a un archivo local. El intento no guardó cambios en la base.'
            guardar(root / 'estado.json', {**status, 'estado': 'ERROR', 'terminado_en': reloj().isoformat(),
                'detalle': detalle, 'tipo_error': type(exc).__name__})
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aplicar', action='store_true')
    parser.add_argument('--agenda-ampliada', action='store_true',
                        help='Hasta 200 turnos de agenda; conserva los límites de red y de resultados')
    parser.add_argument('--env-local', type=Path, default=Path(__file__).resolve().parents[1] / '.env')
    parser.add_argument('--estado', type=Path)
    parser.add_argument('--salida', type=Path)
    parser.add_argument('--fuentes', type=Path, help='Replay con capturas verificadas, sin red')
    parser.add_argument('--completar-capturas', action='store_true', help='Solo en clon: consultar URLs nuevas sin reemplazar capturas previas')
    parser.add_argument('--bd-ensayo', help='Clon propio ap_actualizador_prueba_*, nunca otro destino')
    parser.add_argument('--ejecucion-id', type=UUID)
    parser.add_argument('--historico', nargs=4, metavar=('LIGA','TEMPORADA_FUENTE','DESDE','HASTA'),
                        help='Lote separado de hasta 31 días; vista previa salvo --aplicar')
    args = parser.parse_args(argv)
    if args.agenda_ampliada and (not args.aplicar or args.historico):
        parser.error('La agenda ampliada requiere --aplicar y el ciclo multiliga')
    if args.bd_ensayo and (not args.estado or not args.salida):
        parser.error('Un ensayo requiere estado y salida separados de la instalación habitual')
    if args.completar_capturas and not (args.bd_ensayo and args.fuentes):
        parser.error('Completar capturas requiere un clon explícito y fuentes previas')
    if args.historico:
        code, year, lo, hi = args.historico
        try:
            start, end = date.fromisoformat(lo), date.fromisoformat(hi)
            season = int(year)
            if not 0 <= (end-start).days <= 30 or not 1900 <= season <= 2100:
                raise ValueError
        except ValueError:
            parser.error('Usa año de fuente y fechas ISO en un rango de hasta 31 días')
        args.historico = (code, season, start, end)
    try:
        return ejecutar(args)
    except Exception as exc:
        print(json.dumps({'estado': 'ERROR', 'tipo': type(exc).__name__, 'detalle': 'Consultar evidencia local; no se imprimen credenciales.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
