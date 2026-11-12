"""Cola y recibos SQL del actualizador local. No abre red ni escribe archivos deportivos."""
from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from servicios.sincronizacion_agendas import huella, plano

RESERVA = 'AnalyticsPredict:multiliga:reserva:v1'
TRABAJADOR = 'AnalyticsPredict:multiliga:worker:v1'


def disponible(conn):
    return conn.execute("SELECT to_regclass('public.ap_m1_ejecuciones') IS NOT NULL").fetchone()[0]


def reservar(conn, ahora, *, tipo='DIARIA'):
    """Devuelve (id, nueva). El trabajador reclama la reserva con un lock de sesión."""
    with conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (RESERVA,))
        active = conn.execute("""SELECT id,estado,solicitada_en FROM public.ap_m1_ejecuciones
                                 WHERE estado IN ('SOLICITADA','EN_CURSO')""").fetchone()
        if active:
            run_id, state, started = active
            if state == 'SOLICITADA' and ahora - started < timedelta(minutes=2):
                return run_id, False
            if not conn.execute('SELECT pg_try_advisory_xact_lock(hashtext(%s))', (TRABAJADOR,)).fetchone()[0]:
                return run_id, False
            finalizar(conn, run_id, 'INTERRUMPIDA', ahora, {'causa': 'TRABAJADOR_AUSENTE'})
        elif not conn.execute('SELECT pg_try_advisory_xact_lock(hashtext(%s))', (TRABAJADOR,)).fetchone()[0]:
            # La ejecución anterior todavía está materializando archivos.
            run_id = conn.execute('SELECT id FROM public.ap_m1_ejecuciones ORDER BY solicitada_en DESC LIMIT 1').fetchone()[0]
            return run_id, False
        run_id = uuid4()
        conn.execute("""INSERT INTO public.ap_m1_ejecuciones(id,estado,solicitada_en,detalle)
                        VALUES(%s,'SOLICITADA',%s,%s)""", (run_id, ahora, Jsonb({'tipo': tipo})))
        return run_id, True


def reclamar(conn, run_id, ahora):
    """La misma conexión debe mantenerse abierta durante la ejecución."""
    with conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (RESERVA,))
        locked = conn.execute('SELECT pg_try_advisory_lock(hashtext(%s))', (TRABAJADOR,)).fetchone()[0]
        if not locked:
            return False
        found = conn.execute("""UPDATE public.ap_m1_ejecuciones SET estado='EN_CURSO', iniciada_en=%s
            WHERE id=%s AND estado='SOLICITADA' RETURNING id""", (ahora, run_id)).fetchone()
        if found:
            return True
        conn.execute('SELECT pg_advisory_unlock(hashtext(%s))', (TRABAJADOR,))
        return False


def finalizar(conn, run_id, estado, ahora, detalle):
    if estado not in ('TERMINADA', 'INTERRUMPIDA', 'ERROR'):
        raise ValueError('Estado terminal inválido')
    return conn.execute("""UPDATE public.ap_m1_ejecuciones SET estado=%s,finalizada_en=%s,detalle=detalle||%s
        WHERE id=%s AND estado IN ('SOLICITADA','EN_CURSO') RETURNING id""",
        (estado, ahora, Jsonb(plano(detalle)), run_id)).fetchone() is not None


def estado_sql(conn, run_id=None):
    """Lectura pura. Los recibos permiten reconstruir el estado si faltó publicar JSON."""
    with conn.cursor(row_factory=dict_row) as cur:
        query = """SELECT * FROM public.ap_m1_ejecuciones"""
        if run_id is None:
            run = cur.execute(query + """ WHERE detalle->>'tipo' IS DISTINCT FROM 'IMPORTACION_INICIAL'
                AND (detalle->>'tipo' IS DISTINCT FROM 'HISTORICA' OR estado IN ('SOLICITADA','EN_CURSO'))
                ORDER BY (estado IN ('SOLICITADA','EN_CURSO')) DESC,solicitada_en DESC,id DESC LIMIT 1""").fetchone()
        else:
            run = cur.execute(query + ' WHERE id=%s', (run_id,)).fetchone()
        if not run:
            return None
        lots = cur.execute("""SELECT etapa,huella,confirmado_en,recibo FROM public.ap_m1_lotes
              WHERE ejecucion_id=%s ORDER BY confirmado_en,huella""", (run['id'],)).fetchall()
    return plano({**run, 'lotes': lots})


def estado_compatible(conn, anterior, ahora):
    """Conserva el formato legacy y usa el recibo SQL si faltó publicar el JSON."""
    if not disponible(conn):
        return anterior
    run = estado_sql(conn)
    if not run or run['detalle'].get('tipo') == 'IMPORTACION_INICIAL':
        return anterior
    core = {'ejecucion_id': run['id'], 'iniciado_en': run['iniciada_en'] or run['solicitada_en']}
    current = anterior if anterior.get('ejecucion_id') == run['id'] else {}
    if run['estado'] == 'TERMINADA':
        report = run['detalle']['informe']
        return {**current, **run['detalle'].get('publicacion', {}), **core, 'estado': run['detalle']['cobertura'],
                'terminado_en': run['finalizada_en'], 'ligas_resultado': report['ligas_resultado'],
                'modelos': report['modelos'], 'detalle': 'Actualización terminada. Consulta la cobertura.'}
    state = run['estado']
    if state in ('SOLICITADA', 'EN_CURSO') and not trabajador_presente(conn):
        from datetime import datetime
        if state == 'EN_CURSO' or ahora - datetime.fromisoformat(run['solicitada_en']) >= timedelta(minutes=2):
            state = 'INTERRUMPIDA'
    return {**current, **core, 'estado': state, 'lotes_confirmados': len(run['lotes'])}


def trabajador_presente(conn):
    return conn.execute("""SELECT EXISTS (SELECT 1 FROM pg_locks
        WHERE locktype='advisory' AND granted AND database=(SELECT oid FROM pg_database WHERE datname=current_database())
          AND classid::bigint=((hashtext(%s)::bigint >> 32) & 4294967295)
          AND objid::bigint=(hashtext(%s)::bigint & 4294967295) AND objsubid=1)""",
        (TRABAJADOR, TRABAJADOR)).fetchone()[0]


def lote(conn, run_id, etapa, insumo, ahora, aplicar):
    """Ejecuta callback y sella su recibo en una única transacción; insumo estable."""
    key = huella({'etapa': etapa, 'insumo': plano(insumo)})
    with conn.transaction():
        # La reserva de solicitudes sigue disponible mientras se aplica el lote.
        conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (key,))
        state = conn.execute('SELECT estado FROM public.ap_m1_ejecuciones WHERE id=%s FOR UPDATE',
                             (run_id,)).fetchone()
        if state != ('EN_CURSO',):
            raise ValueError('Ejecución no reclamada')
        # La fila reservada es visible para el callback de esta transacción, nunca
        # como un lote confirmado fuera de ella hasta que se completa el recibo.
        prior = conn.execute('SELECT recibo FROM public.ap_m1_lotes WHERE huella=%s', (key,)).fetchone()
        if prior:
            return key, prior[0], False
        conn.execute("""INSERT INTO public.ap_m1_lotes(huella,ejecucion_id,etapa,confirmado_en,recibo)
            VALUES(%s,%s,%s,%s,'{}')""", (key, run_id, etapa, ahora))
        result = plano(aplicar(key))
        conn.execute('UPDATE public.ap_m1_lotes SET recibo=%s WHERE huella=%s', (Jsonb(result), key))
        return key, result, True


@dataclass(frozen=True)
class Pendiente:
    clave: tuple[str, ...]
    estado: str
    motivo: str
    observado: object
    evidencia: dict
    proximo: object
    fecha_evento: object = None
    partido_id: object = None
    intento: bool = False


def guardar_pendiente(conn, item, lote_id, *, solo_nuevo=False):
    tipo = 'EVENTO' if len(item.clave) == 8 else 'VENTANA'
    row = conn.execute("""
        INSERT INTO public.ap_m1_obligaciones(clave,tipo,estado,motivo,fecha_evento,partido_id,
            primero_en,ultimo_en,intentos,reintentar_en,evidencia_inicial,evidencia_actual,ultimo_lote)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT(clave) DO UPDATE SET
            estado=excluded.estado, motivo=excluded.motivo, fecha_evento=excluded.fecha_evento,
            partido_id=COALESCE(ap_m1_obligaciones.partido_id,excluded.partido_id),
            ultimo_en=GREATEST(ap_m1_obligaciones.ultimo_en,excluded.ultimo_en),
            intentos=ap_m1_obligaciones.intentos+excluded.intentos,
            reintentar_en=excluded.reintentar_en,evidencia_actual=excluded.evidencia_actual,ultimo_lote=excluded.ultimo_lote
        WHERE NOT %s AND (excluded.ultimo_en>=ap_m1_obligaciones.ultimo_en
               OR (ap_m1_obligaciones.estado='PENDIENTE' AND ap_m1_obligaciones.intentos=0 AND excluded.intentos>0))
          AND (ap_m1_obligaciones.partido_id IS NULL OR excluded.partido_id IS NULL
               OR excluded.partido_id=ap_m1_obligaciones.partido_id)
          AND (ap_m1_obligaciones.estado NOT IN ('RESUELTO','SIN_COBERTURA')
               OR excluded.ultimo_en>ap_m1_obligaciones.ultimo_en)
        RETURNING clave
    """, (list(item.clave), tipo, item.estado, item.motivo, item.fecha_evento, item.partido_id,
          item.observado, item.observado, int(item.intento), item.proximo, Jsonb(plano(item.evidencia)),
          Jsonb(plano(item.evidencia)), lote_id, solo_nuevo)).fetchone()
    if row is None and item.partido_id is not None:
        linked = conn.execute('SELECT partido_id FROM public.ap_m1_obligaciones WHERE clave=%s',
                              (list(item.clave),)).fetchone()
        if linked and linked[0] and str(linked[0]) != str(item.partido_id):
            raise ValueError('La clave ya está vinculada a otro partido')
    return row is not None


def resolver_estadistica(conn, clave, partido, evidencia, ahora, lote_id):
    """Solo una observación vigente acreditada del valor canónico permite cerrar."""
    from servicios.actualizador_partidos import OBJETIVOS

    _, _, _, provider, event, stage, period, field = clave
    if stage != 'ESTADISTICAS' or field not in OBJETIVOS:
        raise ValueError('Campo fuera del contrato')
    with conn.cursor() as cur:
        match = cur.execute(sql.SQL("""
            SELECT 1 FROM public.observaciones_estadisticas_futbol_vigentes v
            JOIN public.partidos_futbol p ON p.id=v.partido_id
            WHERE v.fuente=%s AND v.id_evento_fuente=%s AND v.periodo_proveedor=%s
              AND v.campo=%s AND v.partido_id=%s AND v.sha256_payload=%s AND p.{}=v.valor
              AND NOT EXISTS (SELECT 1 FROM public.cuarentena_observaciones_estadisticas_futbol q
                   WHERE q.fuente=v.fuente AND q.id_evento_fuente=v.id_evento_fuente AND q.campo=v.campo
                     AND q.periodo_proveedor=v.periodo_proveedor AND q.sha256_payload=v.sha256_payload)
        """).format(sql.Identifier(field)),
            (provider, event, period, field, partido, evidencia['sha256_payload'])).fetchone()
        if not match:
            raise ValueError('Cierre sin evidencia vigente del valor canónico')
        cur.execute("""UPDATE public.ap_m1_obligaciones SET estado='RESUELTO', motivo='EVIDENCIA_VALIDADA',
            ultimo_en=GREATEST(ultimo_en,%s), reintentar_en=NULL, partido_id=%s, evidencia_actual=%s,
            intentos=intentos+1,ultimo_lote=%s WHERE clave=%s AND estado<>'RESUELTO'
            AND (partido_id=%s OR partido_id IS NULL)""",
            (ahora, partido, Jsonb(plano(evidencia)), lote_id, list(clave), partido))
        return cur.rowcount


def acreditar_tramo(conn, clave, desde, hasta, pruebas, lote_id):
    if not pruebas or not all(p.get('sha256') and p.get('observado_en') and p.get('url') for p in pruebas):
        raise ValueError('Tramo sin capturas verificadas')
    conn.execute("""INSERT INTO public.ap_m1_tramos(deporte,competicion,proveedor,fuente,desde,hasta,evidencia,lote)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
        (*clave, desde, hasta, Jsonb(plano(pruebas)), lote_id))


def checkpoints(conn):
    """Última observación acreditada. Los huecos anteriores siguen en la cola."""
    return {code: str(last) for code, last in conn.execute(
        'SELECT competicion,max(hasta) FROM public.ap_m1_tramos GROUP BY competicion').fetchall()}


def vencidos(conn, ahora, etapa=None):
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute("""SELECT * FROM public.ap_m1_obligaciones WHERE reintentar_en<=%s
            AND (%s::text IS NULL OR (tipo='EVENTO' AND clave[6]=%s))
            ORDER BY reintentar_en,primero_en,clave""", (ahora, etapa, etapa)).fetchall()
    return rows


def repartir(recientes, pendientes, cupo, grupo, identidad):
    """Alterna ventanas/cola y rota ligas. Consume sobrantes de la otra clase."""
    if cupo < 2:
        raise ValueError('El turno necesita capacidad para ambas clases')

    def rueda(items):
        groups = {}
        for item in items:
            groups.setdefault(grupo(item), deque()).append(item)
        while groups:
            for name in list(groups):
                queue = groups[name]
                yield queue.popleft()
                if not queue:
                    del groups[name]

    turns = deque((iter(rueda(recientes)), iter(rueda(pendientes))))
    seen, result = set(), []
    while turns and len(result) < cupo:
        turn = turns.popleft()
        item = next(turn, None)
        if item is None:
            continue
        turns.append(turn)
        key = identidad(item)
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result
