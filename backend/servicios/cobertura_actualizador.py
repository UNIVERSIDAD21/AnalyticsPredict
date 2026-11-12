"""Contadores operativos de lectura; no acreditan un inventario oficial completo."""
from collections import Counter
from psycopg.rows import dict_row

ARCHIVADAS = {
    'ARG_MARADONA': 'Edición histórica 2020-2021, sin adaptador vigente.',
    'USA_MLS_BACK': 'Torneo extraordinario de 2020, sin adaptador vigente.',
}


def clasificar(liga):
    """Sólo clasificaciones explícitas: un feed vacío no archiva una competición."""
    motivo = ARCHIVADAS.get(liga['codigo'])
    return {**liga, 'ambito':'HISTORICO_ARCHIVADO' if motivo else 'REVISION_DIARIA',
            'afecta_cobertura_diaria':not bool(motivo), 'motivo_ambito':motivo}


def resumir_obligaciones(rows, ahora):
    result = {}
    for code in {r['clave'][1] for r in rows}:
        group = [r for r in rows if r['clave'][1]==code]
        events = [r for r in group if r['tipo']=='EVENTO']
        stats = [r for r in events if r['clave'][5]=='ESTADISTICAS']
        future = [r['reintentar_en'] for r in group if r.get('reintentar_en') and r['reintentar_en']>ahora]
        result[code] = {
            'resultados':len({r['clave'][4] for r in events if r['clave'][5]=='IDENTIDAD_RESULTADO'}),
            'eventos_agenda':len({r['clave'][4] for r in events if r['clave'][5]=='AGENDA'}),
            'campos_estadisticas':len(stats),
            'partidos_estadisticas':len({r.get('partido_id') or r['clave'][4] for r in stats}),
            'campos_estadisticas_elegibles':sum(not r.get('reintentar_en') or r['reintentar_en']<=ahora for r in stats),
            'consultas_resultados':sum(r['tipo']=='VENTANA' for r in group),
            'proximo_reintento_en':min(future).isoformat() if future else None,
            'motivos':[{'motivo':reason,'obligaciones':count} for reason,count in sorted(Counter(r['motivo'] for r in group).items())],
            'alcance':'COLA_ACUMULADA_NO_PARTIDOS_UNICOS',
        }
    return result


def leer_cobertura_operativa(conn, ligas, agenda, desde, hasta, ahora):
    """Exige transacción READ ONLY del coordinador; obtiene dos censos acotados."""
    if conn.execute('SHOW transaction_read_only').fetchone()[0] != 'on':
        raise ValueError('La cobertura requiere una transacción READ ONLY')
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute("""SELECT clave,tipo,estado,motivo,partido_id,reintentar_en
            FROM ap_m1_obligaciones WHERE estado NOT IN ('RESUELTO','SIN_COBERTURA')""").fetchall()
        recent = {r['codigo']:r for r in cur.execute("""SELECT c.codigo,
            count(*) FILTER (WHERE faltantes>0) partidos_estadisticas_pendientes,
            COALESCE(sum(faltantes),0)::int campos_estadisticas_ausentes
            FROM (SELECT p.competicion_id,
                (p.local_corners_total IS NULL)::int+(p.visitante_corners_total IS NULL)::int+
                (p.local_disparos_total IS NULL)::int+(p.visitante_disparos_total IS NULL)::int+
                (p.local_disparos_arco IS NULL)::int+(p.visitante_disparos_arco IS NULL)::int faltantes
                FROM partidos_futbol p WHERE p.valido IS TRUE AND p.estado='FINALIZADO'
                AND p.local_goles_total IS NOT NULL AND p.visitante_goles_total IS NOT NULL
                AND (p.fecha_partido AT TIME ZONE 'America/Bogota')::date BETWEEN %s AND %s) p
            JOIN competiciones_futbol c ON c.id=p.competicion_id GROUP BY c.codigo""",(desde,hasta))}
    debt = resumir_obligaciones(rows, ahora)
    details = []
    for league in ligas:
        code = league['codigo']
        details.append({**clasificar(league), 'pendientes_cola':debt.get(code, {
            'resultados':0,'eventos_agenda':0,'campos_estadisticas':0,'partidos_estadisticas':0,
            'campos_estadisticas_elegibles':0,'consultas_resultados':0,'proximo_reintento_en':None,
            'motivos':[],'alcance':'COLA_ACUMULADA_NO_PARTIDOS_UNICOS'}),
            'estadisticas_ventana':recent.get(code, {'partidos_estadisticas_pendientes':0,'campos_estadisticas_ausentes':0}) if league['deporte']=='futbol' else None})
    active = [r for r in details if r['afecta_cobertura_diaria']]
    ag = agenda['ligas'] if agenda else []
    pending_active = [r for r in active if r['incidencias']]
    summary = {'desde':str(desde),'hasta':str(hasta),'competiciones_diarias':len(active),
        'competiciones_diarias_con_incidencias':len(pending_active),
        'competiciones_archivadas':len(details)-len(active),
        'consultas_agenda_pendientes':sum(x['consultas_pendientes'] for x in ag),
        'consultas_agenda_error':sum(x['consultas_error'] for x in ag),
        'eventos_agenda_pendientes':sum(x.get('eventos_pendientes_cola',0) for x in ag),
        'campos_estadisticas_ausentes_ventana':sum(x['campos_estadisticas_ausentes'] for x in recent.values()),
        'partidos_estadisticas_pendientes_ventana':sum(x['partidos_estadisticas_pendientes'] for x in recent.values()),
        'cobertura_oficial':'DESCONOCIDA','historico_completo_acreditado':False,
        'limite':'Campos de fútbol: córners, tiros totales y tiros a puerta por lado; sólo finales guardados con FT completo en la ventana. La cola es acumulada.'}
    return details, summary
