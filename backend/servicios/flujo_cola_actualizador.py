"""Adapta el ejecutor existente a la cola SQL sin cambiar los contratos deportivos."""
from datetime import date, datetime, timedelta
from psycopg.rows import dict_row

from servicios import cola_actualizador as cola
from servicios.actualizador_partidos import OBJETIVOS
from servicios.fuentes_agenda import BOGOTA, FUTBOL
from servicios.resolucion_multifuente_futbol import aplicar_plan_resolucion
from servicios.sincronizacion_agendas import aplicar, plano


def fuente(liga):
    code = liga['codigo']
    if liga['deporte'] == 'futbol':
        return 'ESPN_SOCCER', next((k for k, v in FUTBOL.items() if v == code), 'SIN_ADAPTADOR')
    return ('EUROLEAGUE', 'euroliga') if code == 'euroleague' else ('ESPN_BASKETBALL', code)


def clave_evento(liga, temporada, evento, etapa, periodo, campo):
    provider, _ = fuente(liga)
    return (liga['deporte'], liga['codigo'], str(temporada), provider, str(evento), etapa, periodo, campo)


def ventanas_ciclo(conn, ligas, hoy, ahora):
    by_code = {x['codigo']: x for x in ligas}
    recientes = [(x, hoy - timedelta(days=7), hoy) for x in ligas]
    backlog = []
    for liga in ligas:
        if fuente(liga)[1] == 'SIN_ADAPTADOR':
            continue
        gap = siguiente_tramo(conn, liga['codigo'], hoy)
        if gap:
            backlog.append((liga, *gap))
    for item in cola.vencidos(conn, ahora):
        key = item['clave']
        liga = by_code.get(key[1])
        if not liga:
            continue
        if item['tipo'] == 'VENTANA':
            backlog.append((liga, date.fromisoformat(key[5]), date.fromisoformat(key[6])))
        elif key[5] == 'IDENTIDAD_RESULTADO':
            day = item['fecha_evento'].astimezone(BOGOTA).date()
            if day <= hoy:
                backlog.append((liga, day, day))
    return cola.repartir(recientes, backlog, 64, lambda x: x[0]['codigo'],
                         lambda x: (x[0]['codigo'], x[1], x[2]))


def siguiente_tramo(conn, code, hoy):
    """Busca un hueco de consulta sin saltar fechas al avanzar una ventana reciente."""
    past = conn.execute("""SELECT recibo->'revisiones_legado'->>%s,recibo->>'fecha_base' FROM public.ap_m1_lotes
                           WHERE etapa='INICIAL'""", (code,)).fetchone()
    base = date.fromisoformat(past[1]) if past and past[1] else hoy
    old = date.fromisoformat(past[0]) - timedelta(days=7) if past and past[0] else base - timedelta(days=14)
    end = hoy - timedelta(days=8)
    spans = conn.execute("""SELECT desde,hasta FROM public.ap_m1_tramos WHERE competicion=%s
        UNION SELECT (clave[6])::date,(clave[7])::date FROM public.ap_m1_obligaciones
            WHERE tipo='VENTANA' AND clave[2]=%s AND estado<>'RESUELTO'
        ORDER BY 1,2""", (code, code)).fetchall()
    # Una ventana fallida ya en cola conserva su hueco y su próximo intento.
    # Aquí se buscan segmentos que ni siquiera han sido registrados.
    for start, stop in spans:
        if stop < old:
            continue
        if start > old:
            end = min(end, start - timedelta(days=1))
            break
        old = max(old, stop + timedelta(days=1))
    if old <= end:
        return old, min(end, old + timedelta(days=30))
    return None


def consolidar(registros, problemas):
    """Una repetición de la misma captura por solapamiento no duplica un evento."""
    rows, conflicts = {}, set()
    for row in registros:
        key = (row['codigo'], row['id_fuente'])
        old = rows.get(key)
        if old and ({k: v for k, v in old.items() if k != 'evidencia'}
                    != {k: v for k, v in row.items() if k != 'evidencia'}):
            conflicts.add(key)
        rows[key] = row
    for code, event in sorted(conflicts):
        row = rows.pop((code, event))
        problemas.append({'grupo': code, 'id': event, 'motivo': 'Revisiones contradictorias del mismo evento',
                          'registro': row})
    return list(rows.values())


def aplicar_resultados(conn, run_id, plan, registros, consultas, ahora, *, acreditar=True):
    by_event = {(r['codigo'], str(r['id_fuente'])): r for r in registros}
    leagues = {x[0]['codigo']: x[0] for x in consultas}
    pending = []
    sin_identidad = set()
    for issue in plan['incidencias']:
        code = issue.get('grupo')
        if code not in leagues or not issue.get('id'):
            continue
        event = str(issue['id'])
        row = by_event.get((code, event)) or issue.get('registro')
        if not row or not row.get('anio') or not row.get('inicio_utc'):
            sin_identidad.add(code)
            continue
        key = clave_evento(leagues[code], row['anio'], event, 'IDENTIDAD_RESULTADO', 'EVENTO', 'identidad_y_resultado')
        observed = datetime.fromisoformat(row['evidencia']['observado_en'])
        pending.append(cola.Pendiente(key, 'REVISION_IDENTIDAD', issue['motivo'], observed,
            row['evidencia'], ahora + timedelta(days=1), datetime.fromisoformat(row['inicio_utc']), intento=True))

    def confirmar(lot_id):
        conn.execute("SET LOCAL lock_timeout='5s'; SET LOCAL statement_timeout='90s'")
        aplicar(conn, plan)
        for item in pending:
            cola.guardar_pendiente(conn, item, lot_id)
        # El checkpoint solo puede avanzar si el trabajo de la próxima etapa
        # ya existe, incluso para las filas que recibirán turno inmediatamente.
        stats_created = sembrar_estadisticas_resultados(conn, lot_id, plan, by_event, leagues, ahora)
        for liga, start, end, issues, proofs in consultas:
            if not acreditar:
                continue
            provider, feed = fuente(liga)
            if feed == 'SIN_ADAPTADOR':
                continue
            key = (liga['deporte'], liga['codigo'], provider, feed)
            window_key = (*key, 'VENTANA', str(start), str(end))
            invalid = [x for x in issues if x.get('ambito') == 'VENTANA' or not x.get('id')]
            if invalid or not proofs or liga['codigo'] in sin_identidad:
                motive = invalid[0]['motivo'] if invalid else 'EVENTO_O_TRAMO_SIN_IDENTIDAD_ACREDITADA'
                cola.guardar_pendiente(conn, cola.Pendiente(window_key, 'ESPERA_FUENTE', motive, ahora,
                    {'pruebas': proofs, 'incidencias': issues}, ahora + timedelta(days=1), intento=True), lot_id)
            else:
                cola.acreditar_tramo(conn, key, start, end, proofs, lot_id)
                cerrar(conn, window_key, None, {'pruebas': proofs}, ahora, lot_id)
        for accepted in plan['aceptados']:
            code, event = accepted['codigo'], str(accepted['id_fuente'])
            row = by_event[(code, event)]
            key = clave_evento(leagues[code], row['anio'], event, 'IDENTIDAD_RESULTADO', 'EVENTO', 'identidad_y_resultado')
            cerrar(conn, key, accepted['partido_id'], row['evidencia'], ahora, lot_id)
            # Una consulta de agenda anterior puede haber dejado la misma
            # identidad pendiente fuera de la ventana diaria actual. Cerrar
            # sólo este evento ya conciliado; no esconder conflictos vigentes.
            if not any(i.get('grupo')==code and str(i.get('id'))==event for i in plan['incidencias']):
                agenda_key = clave_evento(leagues[code], row['anio'], event,
                    'AGENDA', 'EVENTO', 'identidad_fecha_estado')
                cerrar(conn, agenda_key, accepted['partido_id'], row['evidencia'], ahora, lot_id)
        return {'plan_sha256': plan['sha256'], 'operaciones': len(plan['operaciones']),
                'obligaciones_estadisticas_nuevas': stats_created,
                'obligaciones': [list(x.clave) for x in pending],
                'consultas': [[x['codigo'], start, end] for x, start, end, _, _ in consultas]}

    return cola.lote(conn, run_id, 'RESULTADOS', {
        'plan_sha256': plan['sha256'], 'ventanas': [[x['codigo'], lo, hi] for x, lo, hi, _, _ in consultas],
        'acredita_diaria': acreditar,
    }, ahora, confirmar)


def sembrar_estadisticas_resultados(conn, lot_id, plan, by_event, ligas, ahora):
    candidates = [a for a in plan['aceptados'] if a['estado']=='FINALIZADO'
                  and ligas[a['codigo']]['deporte']=='futbol']
    if not candidates:
        return 0
    with conn.cursor(row_factory=dict_row) as cur:
        rows = {str(r['id']):r for r in cur.execute(
            'SELECT * FROM public.partidos_futbol WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',
            ([a['partido_id'] for a in candidates],)).fetchall()}
    created = 0
    for a in candidates:
        row = rows[str(a['partido_id'])]
        source = by_event[(a['codigo'], str(a['id_fuente']))]
        proof = {'resultado_observado': source['evidencia'], 'motivo': 'ESTADISTICA_AUN_NO_CONSULTADA'}
        for field in OBJETIVOS:
            if row[field] is not None:
                continue
            key = clave_evento(ligas[a['codigo']], source['anio'], a['id_fuente'], 'ESTADISTICAS', 'All', field)
            item = cola.Pendiente(key, 'PENDIENTE', 'ESTADISTICA_AUN_NO_CONSULTADA', ahora,
                                 proof, ahora, row['fecha_partido'], row['id'])
            created += cola.guardar_pendiente(conn, item, lot_id, solo_nuevo=True)
    return created


def cerrar(conn, key, partido, prueba, ahora, lote):
    from psycopg.types.json import Jsonb

    conn.execute("""UPDATE public.ap_m1_obligaciones SET estado='RESUELTO',motivo='EVIDENCIA_VALIDADA',
        partido_id=COALESCE(partido_id,%s),ultimo_en=GREATEST(ultimo_en,%s),reintentar_en=NULL,
        evidencia_actual=%s,intentos=intentos+1,ultimo_lote=%s
        WHERE clave=%s AND estado<>'RESUELTO' AND (partido_id IS NULL OR partido_id=%s)""",
        (partido, ahora, Jsonb(plano(prueba)), lote, list(key), partido))


def candidatos_estadisticas(conn, ahora, recientes, anteriores, cupo=400):
    due = {str(x['partido_id']) for x in cola.vencidos(conn, ahora, 'ESTADISTICAS') if x['partido_id']}
    prior = {str(x[0]) for x in conn.execute("""SELECT DISTINCT partido_id FROM public.ap_m1_obligaciones
           WHERE estado NOT IN ('RESUELTO','SIN_COBERTURA') AND tipo='EVENTO' AND clave[6]='ESTADISTICAS'""").fetchall()}
    cutoff = ahora.astimezone(BOGOTA).date() - timedelta(days=7)
    ready = [r for r in recientes if str(r['id']) not in prior or str(r['id']) in due]
    fresh = [r for r in ready if r['fecha_partido'].astimezone(BOGOTA).date() >= cutoff]
    backlog = [r for r in ready if r['fecha_partido'].astimezone(BOGOTA).date() < cutoff]
    backlog.extend(r for r in anteriores if str(r['id']) in due)
    return cola.repartir(fresh, backlog, cupo, lambda r: r['liga'], lambda r: (r['liga'], r['id_fuente']))


def pendientes_estadisticos(conn, execution, rows, mapas, ahora, motivo, *, intento=False):
    if not rows:
        return
    seasons = {(feed, canonical): year for (feed, year), canonical in mapas['temporadas'].items()}
    items = []
    for row in rows:
        feed = row['liga']
        league = {'deporte': 'futbol', 'codigo': FUTBOL[feed]}
        season = seasons.get((feed, str(row['temporada_id'])))
        if season is None:
            raise ValueError('Partido estadístico sin temporada fuente conciliada')
        for field in OBJETIVOS:
            if row[field] is None:
                key = clave_evento(league, season, row['id_fuente'], 'ESTADISTICAS', 'All', field)
                items.append(cola.Pendiente(key, 'ESPERA_FUENTE' if intento else 'PENDIENTE', motivo, ahora,
                    {'motivo_operativo': motivo}, ahora + timedelta(days=int(intento)),
                    row['fecha_partido'], row['id'], intento))
    if not items:
        return

    def registrar(lot_id):
        for item in items:
            cola.guardar_pendiente(conn, item, lot_id, solo_nuevo=not intento)
        return {'obligaciones': [list(item.clave) for item in items]}

    return cola.lote(conn, execution, 'ESTADISTICAS',
        {'ejecucion': str(execution), 'motivo': motivo, 'claves': sorted(item.clave for item in items)},
        ahora, registrar)


def campo_con_observacion_vigente(conn, partido_id, campo, valor):
    """Una captura rechazada no invalida una observacion canonica ya acreditada."""
    from psycopg import sql

    if campo not in OBJETIVOS or valor is None:
        return False
    return conn.execute(sql.SQL("""
        SELECT 1 FROM public.observaciones_estadisticas_futbol_vigentes v
        JOIN public.partidos_futbol p ON p.id=v.partido_id
        WHERE p.id=%s AND p.estado='FINALIZADO' AND v.campo=%s
          AND v.periodo_proveedor='All' AND v.valor=%s AND p.{}=v.valor
          AND NOT EXISTS (SELECT 1 FROM public.cuarentena_observaciones_estadisticas_futbol q
            WHERE q.fuente=v.fuente AND q.id_evento_fuente=v.id_evento_fuente
              AND q.campo=v.campo AND q.periodo_proveedor=v.periodo_proveedor
              AND q.sha256_payload=v.sha256_payload)
        LIMIT 1
    """).format(sql.Identifier(campo)), (partido_id, campo, valor)).fetchone() is not None


def confirmar_estadisticas(conn, run_id, row, payload, meta, plan, identities, rejected, ahora):
    feed, event = row['liga'], str(row['id_fuente'])
    league = {'deporte': 'futbol', 'codigo': FUTBOL[feed]}
    season = payload['header']['season']['year']
    rejected_by_field = {x['campo']: x for x in rejected}

    def key(field):
        return clave_evento(league, season, event, 'ESTADISTICAS', 'All', field)

    def guardar(lot_id):
        receipt = {}
        if plan.actualizaciones:
            receipt = aplicar_plan_resolucion(conn, partido_id=str(row['id']),
                goles_local_ft=row['local_goles_total'], goles_visitante_ft=row['visitante_goles_total'],
                plan=plan, identidades=identities, dry_run=False)
        evidence_date = datetime.fromisoformat(meta['observado_en'])
        for field in OBJETIVOS:
            if field in plan.actualizaciones:
                evidence = {'sha256_payload': plan.procedencia[field][0].sha256_payload, 'fuente': meta}
                cola.resolver_estadistica(conn, key(field), row['id'], evidence, ahora, lot_id)
            elif field in rejected_by_field or row[field] is None:
                if campo_con_observacion_vigente(conn, row['id'], field, row[field]):
                    continue
                rejection = rejected_by_field.get(field)
                cola.guardar_pendiente(conn, cola.Pendiente(key(field), 'ESPERA_FUENTE',
                    rejection['motivo'] if rejection else 'ESTADISTICAS_AUSENTES', evidence_date,
                    {'fuente': meta, 'rechazo': rejection}, ahora + timedelta(days=1),
                    row['fecha_partido'], row['id'], True), lot_id)
        return receipt

    _, receipt, new = cola.lote(conn, run_id, 'ESTADISTICAS',
        {'partido': str(row['id']), 'fuente': meta['sha256'], 'observado': meta['observado_en'],
         'campos': sorted(plan.actualizaciones)}, ahora, guardar)
    return receipt if new else None
