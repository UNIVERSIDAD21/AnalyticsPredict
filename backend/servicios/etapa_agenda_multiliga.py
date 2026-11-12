"""Etapa invocable por el coordinador: no abre procesos, backups, locks ni HTTP propios.

Requiere fase 1 y migración de agenda preparadas por el operador. No se activa
por importar/leer. Agenda futura nunca avanza el cursor de resultados de fase 1.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from psycopg.types.json import Jsonb
from psycopg import sql

from servicios.agenda_multiliga import CONTRATO, pedidos, recolectar_agenda, cobertura_agenda
from servicios.sincronizacion_agendas import aplicar, planificar, plano, huella

MIGRACION = Path(__file__).resolve().parents[1] / 'migrations/2026-11-07_agenda_multiliga.sql'


def migrar_agenda(conn, *, rol_aplicacion=None):
    """Operación explícita del operador, transaccional y sin efectos de lectura."""
    with conn.transaction():
        if conn.execute("SELECT to_regclass('public.ap_m1_lotes')").fetchone()[0] is None:
            raise ValueError('Falta la migración de fase 1')
        if conn.execute("SELECT to_regclass('public.ap_m2_agenda_consultas')").fetchone()[0] is not None:
            raise ValueError('Agenda ya preparada: conciliar antes de repetir DDL')
        conn.execute(MIGRACION.read_text(encoding='utf-8'))
        if rol_aplicacion:
            conceder_acceso_agenda(conn, rol_aplicacion)


def conceder_acceso_agenda(conn, rol_aplicacion):
    """Concesión explícita de lectura y escritura de trabajo, no DELETE ni privilegios globales."""
    with conn.transaction():
        if not conn.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (rol_aplicacion,)).fetchone():
            raise ValueError('Rol de aplicación inexistente')
        conn.execute(sql.SQL('GRANT SELECT,INSERT,UPDATE ON public.ap_m2_agenda_consultas TO {}').format(
            sql.Identifier(rol_aplicacion)))


def turnos_agenda(recientes, pendientes, cupo):
    """Un turno por URL; cada ventana conserva su propia evidencia y recibo."""
    from servicios.cola_actualizador import repartir

    def origen(query):
        return query['url'], tuple(sorted(query['params'].items()))

    actuales = {origen(query): query for query in recientes}
    antiguos = {}
    for query in pendientes:
        antiguos.setdefault(origen(query), query)
    antiguos_independientes = (query for key, query in antiguos.items() if key not in actuales)
    elegidos = repartir(actuales.values(), antiguos_independientes, cupo,
                        lambda query: query['liga']['codigo'], origen)
    consultas = []
    for query in elegidos:
        key = origen(query)
        consultas.extend(grupo[key] for grupo in (actuales, antiguos) if key in grupo)
    return consultas


def origen_consulta(query):
    return query['url'], tuple(sorted(query['params'].items()))


def programar_agenda(conn, ejecucion, ligas, hoy, ahora, *, horizonte=60, cupo=200,
                    excluir_origenes=()):
    """Registra también consultas sin turno; un corte HTTP conserva su localización."""
    from servicios import cola_actualizador as cola
    recent = pedidos(ligas, hoy, horizonte)

    def reservar(lot):
        for query in recent:
            conn.execute('''INSERT INTO public.ap_m2_agenda_consultas
                (clave,competicion,solicitud,desde,hasta,estado,primero_en,ultimo_en,reintentar_en,lote)
                VALUES(%s,%s,%s,%s,%s,'PENDIENTE',%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
                (query['clave'], query['liga']['codigo'], Jsonb(query), query['desde'], query['hasta'],
                 ahora, ahora, ahora, lot))
        return {'consultas_reservadas': len(recent), 'contrato': CONTRATO}

    cola.lote(conn, ejecucion, 'AGENDA', {'tipo': 'RESERVA', 'ejecucion': str(ejecucion),
        'claves': [q['clave'] for q in recent]}, ahora, reservar)
    with conn.transaction():
        due = conn.execute('''SELECT solicitud,estado,evidencia FROM public.ap_m2_agenda_consultas
            WHERE reintentar_en<=%s AND (estado IN ('PENDIENTE','ERROR')
                OR COALESCE(jsonb_array_length(evidencia->'pendientes_evento'),0)>0)
            ORDER BY reintentar_en,primero_en,clave''', (ahora,)).fetchall()
        fresh_keys = {q['clave'] for q in recent}
        due_events = {(r['clave'][1],r['clave'][4]) for r in cola.vencidos(conn, ahora)
                      if r['tipo']=='EVENTO' and r['clave'][5] in ('AGENDA','IDENTIDAD_RESULTADO')}
        backlog = [r[0] for r in due if r[0]['clave'] not in fresh_keys and
                   (r[1] in ('PENDIENTE','ERROR') or any(
                       (r[0]['liga']['codigo'],event_id) in due_events for event_id in r[2].get('pendientes_evento',[])))]
        # Las observaciones recientes pueden refrescarse por el TTL compartido.
        fresh_due = {r[0]['clave'] for r in conn.execute('''SELECT solicitud
            FROM public.ap_m2_agenda_consultas WHERE clave=ANY(%s) AND reintentar_en<=%s''',
            (list(fresh_keys), ahora)).fetchall()}
    omitidos = set(excluir_origenes)
    recent = [q for q in recent if q['clave'] in fresh_due and origen_consulta(q) not in omitidos]
    backlog = [q for q in backlog if origen_consulta(q) not in omitidos]
    return turnos_agenda(recent, backlog, cupo)


def preparar_agenda(conn, client, solicitudes, hoy, observar=lambda _: None):
    """Obtiene y verifica fuera de la transacción de escritura; devuelve un plan."""
    paquete = recolectar_agenda(client, solicitudes, observar)
    scheduled = [r for r in paquete['registros'] if r['estado'] != 'FINALIZADO']
    proofs = [p for q in paquete['consultas'] for p in q['pruebas']]
    lower = min((date.fromisoformat(q['desde']) for q in solicitudes), default=hoy)
    with conn.transaction():
        plan = planificar(conn, scheduled, [], proofs, hoy, desde=lower)
    return {**paquete, 'plan': plan,
            'finales_para_resultados': [r for r in paquete['registros'] if r['estado'] == 'FINALIZADO']}


def clave_pendiente(liga, event, etapa='AGENDA'):
    # Import tardío: la extensión solo exige fase 1 al ejecutar, no al importar.
    from servicios.flujo_cola_actualizador import clave_evento
    return clave_evento(liga, event['anio'], event['id'], etapa, 'EVENTO',
                        'identidad_y_resultado' if etapa == 'IDENTIDAD_RESULTADO' else 'identidad_fecha_estado')


def confirmar_agenda(conn, ejecucion, preparado, ahora):
    """Lote atómico: datos de agenda + pendientes + recibo de lectura sin cursor FT."""
    from servicios import cola_actualizador as cola
    from servicios.flujo_cola_actualizador import cerrar
    by_event = {(r['codigo'], str(r['id_fuente'])): r for r in preparado['registros']}
    ligas = {q['liga']['codigo']: q['liga'] for q in preparado['consultas']}
    events = {(q['liga']['codigo'], e['id']): (e, q) for q in preparado['consultas'] for e in q['inventario']}
    pending_events = {(issue['grupo'],str(issue['id'])) for issue in preparado['plan']['incidencias'] if issue.get('id')}
    pending_events.update((r['codigo'],str(r['id_fuente'])) for r in preparado['finales_para_resultados'])
    pending_events.update((q['liga']['codigo'],str(i['id'])) for q in preparado['consultas'] for i in q['incidencias'] if i.get('id'))

    def pendiente(lot, code, event_id, motivo, etapa='AGENDA'):
        event, query = events[(code, str(event_id))]
        when = datetime.fromisoformat(event['inicio_utc']) if event['inicio_utc'] else datetime.combine(
            date.fromisoformat(event['fecha']), datetime.min.time(), timezone.utc)
        evidence = {'consultas': query['pruebas'], 'fecha_solo_para_localizar': not bool(event['inicio_utc']),
                    'inventario': event, 'motivo': motivo}
        cola.guardar_pendiente(conn, cola.Pendiente(clave_pendiente(ligas[code], event, etapa),
            'REVISION_IDENTIDAD', motivo, ahora, evidence, ahora + timedelta(days=1),
            when, intento=True), lot)

    def confirmar(lot):
        conn.execute("SET LOCAL lock_timeout='5s'; SET LOCAL statement_timeout='90s'")
        aplicar(conn, preparado['plan'])
        pending = set()
        for query in preparado['consultas']:
            delay = timedelta(hours=6) if query['estado'] == 'OBSERVADA' else timedelta(days=1)
            # Se guarda el inventario recibido, no un total inferido desde SQL.
            proof = {'pruebas': query['pruebas'], 'inventario': query['inventario'],
                     'incidencias': query['incidencias'], 'motivo': query.get('motivo'),
                     'pendientes_evento': sorted(e['id'] for e in query['inventario']
                                                if (query['liga']['codigo'],e['id']) in pending_events)}
            updated = conn.execute('''UPDATE public.ap_m2_agenda_consultas SET estado=%s,
                ultimo_en=%s,intentos=intentos+1,reintentar_en=%s,evidencia=%s,lote=%s
                WHERE clave=%s AND ultimo_en<=%s''',
                (query['estado'], ahora, ahora+delay, Jsonb(plano(proof)), lot, query['clave'], ahora)).rowcount
            if updated != 1:
                raise ValueError('Consulta sin reserva o revisión más reciente: no confirmar parcialmente')
            for issue in query['incidencias']:
                key = (query['liga']['codigo'], str(issue['id'])) if issue.get('id') else None
                if key in events and key not in pending:
                    event = events[key][0]
                    stage = 'IDENTIDAD_RESULTADO' if event['final'] else 'AGENDA'
                    pendiente(lot, *key, issue['motivo'], stage)
                    pending.add(key)
        for issue in preparado['plan']['incidencias']:
            code, event_id = issue['grupo'], str(issue.get('id'))
            if (code, event_id) not in pending:
                pendiente(lot, code, event_id, issue['motivo'])
                pending.add((code, event_id))
        for row in preparado['finales_para_resultados']:
            code, event_id = row['codigo'], str(row['id_fuente'])
            if (code, event_id) not in pending:
                pendiente(lot, code, event_id, 'FINAL_OBSERVADO_PENDIENTE_ETAPA_RESULTADOS', 'IDENTIDAD_RESULTADO')
                pending.add((code, event_id))
        for accepted in preparado['plan']['aceptados']:
            code, event_id = accepted['codigo'], str(accepted['id_fuente'])
            if (code, event_id) in pending:
                continue
            event = events[(code, event_id)][0]
            row = by_event[(code, event_id)]
            cerrar(conn, clave_pendiente(ligas[code], event), accepted['partido_id'], row['evidencia'], ahora, lot)
        return {'contrato': CONTRATO, 'plan_sha256': preparado['plan']['sha256'],
            'operaciones_agenda': len(preparado['plan']['operaciones']),
            'consultas': [q['clave'] for q in preparado['consultas']],
            'eventos_pendientes': sorted([list(x) for x in pending]),
            'finales_derivados': len(preparado['finales_para_resultados']),
            'cobertura': cobertura_agenda(preparado, list(ligas.values())),
            'limite': 'Agenda observada; resultados/estadísticas y denominador oficial se acreditan aparte'}

    input_data = {'contrato': CONTRATO, 'plan': preparado['plan']['sha256'],
                  'consultas': [{k: q[k] for k in ('clave', 'estado', 'pruebas', 'incidencias')}
                                for q in preparado['consultas']]}
    return cola.lote(conn, ejecucion, 'AGENDA', input_data, ahora, confirmar)


def ejecutar_etapa_agenda(conn, ejecucion, ligas, client, hoy, ahora, *, horizonte=60, cupo=200,
                         observar=lambda _: None, excluir_origenes=()):
    """El coordinador posee exclusión, respaldo y conexión; esta etapa los reutiliza."""
    tasks = programar_agenda(conn, ejecucion, ligas, hoy, ahora, horizonte=horizonte, cupo=cupo,
                            excluir_origenes=excluir_origenes)
    package = preparar_agenda(conn, client, tasks, hoy, observar)
    lot, receipt, new = confirmar_agenda(conn, ejecucion, package, ahora)
    return {'lote': lot, 'recibo': receipt, 'nuevo': new, 'preparado': package}


def ejecutar_agenda_por_lotes(conn, ejecucion, ligas, client, hoy, ahora, *,
                             horizonte=60, cupo_lote=48, max_turnos=200,
                             observar=lambda _: None):
    """Drena trabajo elegible con el cliente, lock, respaldo y presupuesto del caller.

    Un turno puede acreditar consultas de varias ventanas a la misma URL. No
    reintenta esa URL dentro del ciclo, ni declara cobertura por vaciar elegibles.
    Los lotes conservan sus recibos SQL independientes para reanudar tras un corte.
    """
    if (type(cupo_lote) is not int or type(max_turnos) is not int
            or not 2 <= cupo_lote <= 200 or not 2 <= max_turnos <= 200):
        raise ValueError('Lotes permitidos: 2 a 200 turnos, máximo total 200')
    usados, consultas, lotes = set(), [], []
    operaciones, ultimo_lote = 0, None
    motivo = 'LIMITE_TURNOS'
    while max_turnos - len(usados) >= 2:
        observar(f'Agenda: lote {len(lotes)+1}; {len(usados)}/{max_turnos} turnos utilizados')
        etapa = ejecutar_etapa_agenda(conn, ejecucion, ligas, client, hoy, ahora,
            horizonte=horizonte, cupo=min(cupo_lote, max_turnos-len(usados)),
            excluir_origenes=frozenset(usados), observar=observar)
        actuales = etapa['preparado']['consultas']
        if not actuales:
            motivo = 'SIN_CONSULTAS_ELEGIBLES'
            break
        nuevos = {origen_consulta(q) for q in actuales} - usados
        if not nuevos:
            raise ValueError('La agenda repitió turnos del mismo ciclo; revisar continuidad')
        if len(nuevos) > max_turnos-len(usados):
            raise ValueError('Plan de agenda excede el presupuesto autorizado')
        usados.update(nuevos)
        consultas.extend(actuales)
        operaciones += etapa['recibo']['operaciones_agenda']
        ultimo_lote = etapa['lote']
        lotes.append({'lote':ultimo_lote, 'turnos':len(nuevos), 'consultas':len(actuales)})
        red = getattr(client, 'completar', None) or client
        if getattr(red, 'http', 0) >= getattr(red, 'presupuesto', float('inf')):
            motivo = 'PRESUPUESTO_HTTP'
            break
    return {'lote':ultimo_lote, 'recibo':{'operaciones_agenda':operaciones},
            'preparado':{'consultas':consultas}, 'lotes':lotes,
            'turnos_consumidos':len(usados), 'limite_turnos':max_turnos,
            'motivo_parada':motivo}


def resumen_publicable(conn, ligas, hoy, etapa, *, horizonte=60):
    """Incluye solicitudes diferidas y distingue inventario observado de cobertura oficial."""
    by_code = {x['codigo']: [] for x in ligas}
    for item in pedidos(ligas, hoy, horizonte):
        by_code[item['liga']['codigo']].append(item['clave'])
    attempted = {q['clave'] for q in etapa['preparado']['consultas']}
    summaries = []
    with conn.transaction():
        rows = conn.execute("""SELECT clave,estado,evidencia FROM public.ap_m2_agenda_consultas
            WHERE clave=ANY(%s)""", ([k for ks in by_code.values() for k in ks],)).fetchall()
        pendientes = dict(conn.execute("""SELECT clave[2],count(*) FROM public.ap_m1_obligaciones
            WHERE tipo='EVENTO' AND clave[6]='AGENDA' AND estado NOT IN ('RESUELTO','SIN_COBERTURA')
            GROUP BY clave[2]""").fetchall())
    by_key = {r[0]: r[1:] for r in rows}
    for liga in ligas:
        keys = by_code[liga['codigo']]
        observed = [by_key[k][1] for k in keys if k in by_key and by_key[k][0]=='OBSERVADA']
        errors = sum(k in by_key and by_key[k][0]=='ERROR' for k in keys)
        missing = len(keys) - len(observed) - errors
        inventory = {e['id']:e for evidence in observed for e in evidence.get('inventario', [])}
        summary = {**liga, 'solicitadas':len(keys), 'consultas_observadas':len(observed), 'consultas_error':errors,
                   'consultas_pendientes':missing, 'consultas_en_ciclo':len(set(keys)&attempted),
                   'eventos_enumerados':len(inventory),
                   'horas_confirmadas':sum(bool(e.get('inicio_utc')) for e in inventory.values()),
                   'ultima_fecha_publicada':max((e['fecha'] for e in inventory.values()), default=None),
                   'incidencias_observadas':sum(len(q.get('incidencias',[])) for q in observed),
                   'eventos_pendientes_cola':pendientes.get(liga['codigo'], 0),
                   'cobertura_oficial':'DESCONOCIDA'}
        if not keys:
            summary['estado'] = 'SIN_ADAPTADOR'
        elif errors or missing or summary['incidencias_observadas'] or summary['eventos_pendientes_cola']:
            summary['estado'] = 'PARCIAL'
        else:
            summary['estado'] = 'OBSERVADA_EN_FUENTE' if inventory else 'SIN_EVENTOS_PUBLICADOS'
        summaries.append(summary)
    return {'lote':etapa['lote'], 'desde':str(hoy-timedelta(days=1)),
             'hasta':str(hoy+timedelta(days=horizonte)), 'ligas':summaries,
             'operaciones':etapa['recibo']['operaciones_agenda'],
             'ejecucion_lotes':{k:etapa[k] for k in ('lotes','turnos_consumidos','limite_turnos','motivo_parada')
                                if k in etapa}}
