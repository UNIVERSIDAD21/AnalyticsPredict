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


def programar_agenda(conn, ejecucion, ligas, hoy, ahora, *, horizonte=60, cupo=200):
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
    recent = [q for q in recent if q['clave'] in fresh_due]
    return cola.repartir(recent, backlog, cupo, lambda q: q['liga']['codigo'], lambda q: q['clave'])


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
                if issue.get('id') and (query['liga']['codigo'], str(issue['id'])) in events:
                    event = events[(query['liga']['codigo'], str(issue['id']))][0]
                    stage = 'IDENTIDAD_RESULTADO' if event['final'] else 'AGENDA'
                    pendiente(lot, query['liga']['codigo'], issue['id'], issue['motivo'], stage)
                    pending.add((query['liga']['codigo'], str(issue['id'])))
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
                         observar=lambda _: None):
    """El coordinador posee exclusión, respaldo y conexión; esta etapa los reutiliza."""
    tasks = programar_agenda(conn, ejecucion, ligas, hoy, ahora, horizonte=horizonte, cupo=cupo)
    package = preparar_agenda(conn, client, tasks, hoy, observar)
    lot, receipt, new = confirmar_agenda(conn, ejecucion, package, ahora)
    return {'lote': lot, 'recibo': receipt, 'nuevo': new, 'preparado': package}
